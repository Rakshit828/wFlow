"""
workflow.py — Temporal DynamicWorkflow backed by the ExecutionPlan engine.

Key design points
─────────────────
• node_def.fn is already a @activity.defn — passed directly to
  workflow.execute_activity(node_def.fn, input_model_instance).

• Parallel fan-out: multiple nodes in one RUN step → asyncio.gather().
  (workflow.gather does not exist in the Temporal Python SDK; asyncio.gather
  is correct here because execute_activity returns an awaitable future and
  Temporal schedules all of them concurrently before any is awaited.)

"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from src.workflows.parser import parse_pipeline
    from src.workflows.planner import build_execution_plan
    from src.workflows.types import (
        ExecutionPlan,
        ExecutionStep,
        ExecutionStepKind,
        Node,
        Pipeline,
        WorkflowInput,
    )
    from src.workflows.nodes import NODES_MAP
    from src.workflows.utils import resolve_configs, resolve_inputs, ResolutionResult

logger = logging.getLogger(__name__)

_NODE_TIMEOUT = timedelta(seconds=300)
_CONFIG_TIMEOUT = timedelta(seconds=60)


# ═══════════════════════════════════════════════════════════════════════════════
# Activities
# ═══════════════════════════════════════════════════════════════════════════════


@activity.defn
async def resolve_configs_activity(inputs: WorkflowInput) -> Dict[str, Any]:
    """Resolve per-node service credentials / configs before execution starts."""
    pipeline = Pipeline(**json.loads(inputs.pipeline_str))
    user_id = (inputs.configs or {}).get("user_id")
    resolved = await resolve_configs(pipeline, user_id)
    activity.logger.info("Configs resolved for %d nodes", len(resolved))
    return resolved


# ═══════════════════════════════════════════════════════════════════════════════
# Workflow
# ═══════════════════════════════════════════════════════════════════════════════

@workflow.defn
class DynamicWorkflow:
    """
    Executes an arbitrary pipeline defined by WorkflowInput.

    Execution order is determined by the ExecutionPlan produced by the planner.
    Each node's .fn (already decorated @activity.defn) is dispatched via
    workflow.execute_activity() with a fully-constructed Pydantic input model.
    """

    @workflow.run
    async def run(self, inputs: WorkflowInput) -> Dict[str, Any]:
        workflow.logger.info("DynamicWorkflow started")

        pipeline: Pipeline = Pipeline(**json.loads(inputs.pipeline_str))

        # ── 1. Resolve service configs ─────────────────────────────────────────
        resolved_configs: Dict[str, Any] = await workflow.execute_activity(
            resolve_configs_activity,
            inputs,
            start_to_close_timeout=_CONFIG_TIMEOUT,
        )
        workflow.logger.info("Configs resolved for %d nodes", len(resolved_configs))

        # ── 2. Parse & plan ───────────────────────────────────────────────────
        parsed = parse_pipeline(pipeline)
        plan = build_execution_plan(pipeline, parsed)

        workflow.logger.info(
            "Execution plan built: %d top-level steps", len(plan.steps)
        )

        # ── 3. Walk the plan ──────────────────────────────────────────────────
        outputs: Dict[str, Any] = {}
        await self._execute_plan(plan, pipeline, resolved_configs, outputs)

        workflow.logger.info(
            "DynamicWorkflow completed. Nodes run: %s", list(outputs.keys())
        )
        return {
            "outputs": outputs,
            "resolved_configs": resolved_configs,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Plan walker
    # ═══════════════════════════════════════════════════════════════════════════

    async def _execute_plan(
        self,
        plan: ExecutionPlan,
        pipeline: Pipeline,
        resolved_configs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:
        for step in plan.steps:
            await self._execute_step(step, pipeline, resolved_configs, outputs)

    async def _execute_step(
        self,
        step: ExecutionStep,
        pipeline: Pipeline,
        resolved_configs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:

        # ── RUN ───────────────────────────────────────────────────────────────
        if step.kind == ExecutionStepKind.RUN:
            if len(step.nodes) == 1:
                await self._run_node(step.nodes[0], pipeline, resolved_configs, outputs)
            else:
                # Parallel fan-out: schedule all activities then await together.
                # asyncio.gather is correct here — each _run_node internally
                # calls workflow.execute_activity which returns a coroutine;
                # Temporal schedules them all before the first one is awaited.
                await asyncio.gather(
                    *[
                        self._run_node(name, pipeline, resolved_configs, outputs)
                        for name in step.nodes
                    ]
                )

        # ── MERGE ─────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.MERGE:
            # Semantic checkpoint — all listed nodes must already be in outputs.
            missing = [n for n in step.nodes if n not in outputs]
            if missing:
                raise RuntimeError(
                    f"MERGE checkpoint failed: nodes not yet completed: {missing}"
                )
            workflow.logger.info("MERGE checkpoint passed: %s", step.nodes)

        # ── IF ────────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.IF:
            await self._execute_if(step, pipeline, resolved_configs, outputs)

        # ── SWITCH ────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.SWITCH:
            await self._execute_switch(step, pipeline, resolved_configs, outputs)


    # ─── IF ───────────────────────────────────────────────────────────────────

    async def _execute_if(
        self,
        step: ExecutionStep,
        pipeline: Pipeline,
        resolved_configs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:
        """
        The if_node was already executed in the preceding RUN step.
        Read its `decision` output and execute the matching sub-plan.
        """
        if_node_name = step.nodes[0]
        decision = self._read_output(if_node_name, outputs, "decision")

        if not isinstance(decision, bool):
            raise ValueError(
                f"if_node '{if_node_name}' must output a bool 'decision', "
                f"got {type(decision).__name__}: {decision!r}"
            )

        workflow.logger.info("IF '%s' → decision=%s", if_node_name, decision)

        chosen_plan = step.true_plan if decision else step.false_plan
        if chosen_plan:
            await self._execute_plan(chosen_plan, pipeline, resolved_configs, outputs)

    # ─── SWITCH ───────────────────────────────────────────────────────────────

    async def _execute_switch(
        self,
        step: ExecutionStep,
        pipeline: Pipeline,
        resolved_configs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:
        """
        The switch_node was already executed in the preceding RUN step.
        Read its `case` output and execute the matching sub-plan.
        Falls back to default_case if no exact match is found.
        """
        switch_node_name = step.nodes[0]
        case_value = self._read_output(switch_node_name, outputs, "case")

        workflow.logger.info("SWITCH '%s' → case='%s'", switch_node_name, case_value)

        case_plans = step.case_plans or {}
        chosen_plan = case_plans.get(case_value)

        if chosen_plan is None and step.default_case:
            workflow.logger.warning(
                "SWITCH '%s': no plan for case '%s', falling back to default '%s'",
                switch_node_name,
                case_value,
                step.default_case,
            )
            chosen_plan = case_plans.get(step.default_case)

        if chosen_plan is None:
            workflow.logger.warning(
                "SWITCH '%s': no plan for case '%s' and no default — skipping.",
                switch_node_name,
                case_value,
            )
            return

        await self._execute_plan(chosen_plan, pipeline, resolved_configs, outputs)

    # ─── Single node execution ────────────────────────────────────────────────────────

    async def _run_node(
        self,
        node_name: str,
        pipeline: Pipeline,
        resolved_configs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:
        """
        Resolve inputs, build the Pydantic input model, and dispatch the node
        activity via workflow.execute_activity().

        node_def.fn is already decorated with @activity.defn — we pass it
        directly; no wrapper activity is needed.

        Input merge order (later wins):
            1. Resolved references from previous node outputs (resolve_inputs)
            2. Service config from resolved_configs (keyed by node.key)
            3. Static config from node.config in the pipeline definition
        """
        node: Optional[Node] = next(
            (n for n in pipeline.nodes if n.name == node_name), None
        )
        if node is None:
            raise KeyError(f"Node '{node_name}' not found in pipeline definition.")

        node_def = NODES_MAP.get(node.key)
        if node_def is None:
            raise ValueError(
                f"Node key '{node.key}' (node '{node_name}') not found in NODES_MAP. "
                f"Registered keys: {list(NODES_MAP.keys())}"
            )

        # ── 1. Resolve node input references against accumulated outputs ───────
        resolution: ResolutionResult = resolve_inputs(node.inputs, outputs)
        resolution.raise_if_errors()
        resolved_node_inputs: Dict[str, Any] = resolution.resolved

        # ── 2. Merge service + static configs ─────────────────────────────────
        merged_config: Dict[str, Any] = {}

        service_config = resolved_configs.get(node.key)
        if service_config:
            merged_config.update(service_config)
        if node.config:
            merged_config.update(node.config)
        if merged_config:
            resolved_node_inputs["config"] = merged_config

        workflow.logger.info(
            "Dispatching '%s' (key=%s) | inputs=%s",
            node_name,
            node.key,
            list(resolved_node_inputs.keys()),
        )

        # ── 3. Build the typed Pydantic input model ───────────────────────────
        if node_def.node_input_model is None:
            raise ValueError(f"Node '{node.key}' has no node_input_model defined.")

        input_model = node_def.node_input_model(**resolved_node_inputs)

        # ── 4. Dispatch via Temporal ──────────────────────────────────────────
        node_output = await workflow.execute_activity(
            node_def.fn,
            input_model,
            start_to_close_timeout=_NODE_TIMEOUT,
        )

        # Normalise to plain dict (Pydantic model → dict)
        if hasattr(node_output, "model_dump"):
            node_output = node_output.model_dump()
        elif not isinstance(node_output, dict):
            node_output = {"output": node_output}

        outputs[node_name] = node_output
        workflow.logger.info(
            "Completed '%s' | output_keys=%s",
            node_name,
            list(node_output.keys()),
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _read_output(node_name: str, outputs: Dict[str, Any], key: str) -> Any:
        """
        Read a specific key from a node's output.

        Handles two common output shapes:
            {"decision": True}              → direct
            {"output": {"decision": True}}  → nested under "output"
        """
        node_out = outputs.get(node_name)
        if node_out is None:
            raise KeyError(
                f"Cannot read '{key}' from '{node_name}': node has no output yet. "
                f"Nodes with output: {list(outputs.keys())}"
            )

        if key in node_out:
            return node_out[key]

        nested = node_out.get("output", {})
        if isinstance(nested, dict) and key in nested:
            return nested[key]

        raise KeyError(
            f"Key '{key}' not found in output of '{node_name}'. "
            f"Available keys: {list(node_out.keys())}"
        )
