"""
workflow.py — Temporal DynamicWorkflow backed by the ExecutionPlan engine.

Key design points
─────────────────
* node_def.fn is already a @activity.defn — we call it directly via
  workflow.execute_activity(node_def.fn, input_model_instance).
* Control-flow nodes (if_node / switch_node) are ordinary activities whose
  output is read back to route execution. The planner always emits:
      RUN [if_node]  →  IF step      (reads decision from outputs)
      RUN [switch_node]  →  SWITCH step  (reads case from outputs)
  so the control node is executed as a normal node in _run_node; the
  IF/SWITCH step only reads the already-stored output.
* Parallel fan-out: multiple nodes in one RUN step → workflow.gather().
* Loop: loop_body runs repeatedly; loop-back node's continue_loop flag
  drives the iteration decision.
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

_NODE_TIMEOUT   = timedelta(seconds=300)
_CONFIG_TIMEOUT = timedelta(seconds=60)
_MAX_LOOP_ITERS = 10


# ─── Config resolution activity ───────────────────────────────────────────────

@activity.defn
async def resolve_configs_activity(inputs: WorkflowInput) -> Dict[str, Any]:
    """Resolve per-node service credentials / configs before execution starts."""
    pipeline  = Pipeline(**json.loads(inputs.pipeline_str))
    user_id   = (inputs.configs or {}).get("user_id")
    resolved  = await resolve_configs(pipeline, user_id)
    activity.logger.info("Configs resolved for %d nodes", len(resolved))
    return resolved


# ─── Workflow ─────────────────────────────────────────────────────────────────

@workflow.defn
class DynamicWorkflow:
    """
    Executes an arbitrary pipeline defined by WorkflowInput.

    The execution order is determined by the ExecutionPlan produced by the
    planner. Each node's .fn (already decorated with @activity.defn) is
    dispatched via workflow.execute_activity() with a fully-constructed
    Pydantic input model instance.
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
        plan   = build_execution_plan(pipeline, parsed)

        workflow.logger.info(
            "Execution plan built: %d top-level steps", len(plan.steps)
        )

        # ── 3. Walk the plan ──────────────────────────────────────────────────
        # `outputs` accumulates every node result keyed by node name.
        outputs: Dict[str, Any] = {}
        await self._execute_plan(plan, pipeline, resolved_configs, outputs)

        workflow.logger.info(
            "DynamicWorkflow completed. Nodes run: %s", list(outputs.keys())
        )
        return {
            "outputs":          outputs,
            "resolved_configs": resolved_configs,
        }

    # ─── Plan / step walking ──────────────────────────────────────────────────

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
                await self._run_node(
                    step.nodes[0], pipeline, resolved_configs, outputs
                )
            else:
                # Multiple nodes in one RUN step → concurrent parallel fan-out.
                # Build the execute_activity coroutines first, then gather them.
                # We cannot use workflow.gather (doesn't exist); asyncio.gather
                # works here because _run_node schedules Temporal activities
                # (which are non-blocking futures) and awaits them concurrently.
                await asyncio.gather(
                    *[
                        self._run_node(name, pipeline, resolved_configs, outputs)
                        for name in step.nodes
                    ]
                )

        # ── MERGE ─────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.MERGE:
            # Semantic checkpoint — all listed nodes must already be in outputs
            # (they were launched as parallel RUN nodes earlier).
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

        # ── LOOP ──────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.LOOP:
            await self._execute_loop(step, pipeline, resolved_configs, outputs)

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
        """
        switch_node_name = step.nodes[0]
        case_value = self._read_output(switch_node_name, outputs, "case")

        workflow.logger.info(
            "SWITCH '%s' → case='%s'", switch_node_name, case_value
        )

        case_plans  = step.case_plans or {}
        chosen_plan = case_plans.get(case_value)

        if chosen_plan is None and step.default_case:
            workflow.logger.warning(
                "SWITCH '%s': no plan for case '%s', falling back to default '%s'",
                switch_node_name, case_value, step.default_case,
            )
            chosen_plan = case_plans.get(step.default_case)

        if chosen_plan is None:
            workflow.logger.warning(
                "SWITCH '%s': no plan for case '%s' and no default — skipping.",
                switch_node_name, case_value,
            )
            return

        await self._execute_plan(chosen_plan, pipeline, resolved_configs, outputs)

    # ─── LOOP ─────────────────────────────────────────────────────────────────

    async def _execute_loop(
        self,
        step: ExecutionStep,
        pipeline: Pipeline,
        resolved_configs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:
        """
        Execute the loop body repeatedly until the loop-back node signals stop
        or _MAX_LOOP_ITERS is reached.

        Convention: the loop-back node (is_loop_back_node=True) must include
            {"continue_loop": bool}
        in its output. True → run body again; False (or key absent) → exit.
        """
        if not step.loop_body:
            workflow.logger.warning("LOOP step has no body — skipping.")
            return

        loop_back_node = self._find_loop_back_node(step.loop_entry, pipeline)

        for iteration in range(1, _MAX_LOOP_ITERS + 1):
            workflow.logger.info(
                "LOOP entry='%s' — iteration %d/%d",
                step.loop_entry, iteration, _MAX_LOOP_ITERS,
            )

            await self._execute_plan(
                step.loop_body, pipeline, resolved_configs, outputs
            )

            if loop_back_node is None:
                workflow.logger.debug("LOOP: no loop-back node — single iteration.")
                break

            loop_output  = outputs.get(loop_back_node, {})
            continue_loop = loop_output.get("continue_loop", False)

            if not continue_loop:
                workflow.logger.info(
                    "LOOP: '%s' signalled stop after iteration %d.",
                    loop_back_node, iteration,
                )
                break

            workflow.logger.info(
                "LOOP: '%s' signalled continue — starting iteration %d.",
                loop_back_node, iteration + 1,
            )
        else:
            workflow.logger.warning(
                "LOOP hit max iterations (%d) for entry='%s'. Forcing exit.",
                _MAX_LOOP_ITERS, step.loop_entry,
            )

    # ─── Single node execution ────────────────────────────────────────────────

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
        directly. No wrapper activity is needed.

        Input merge order (later wins):
            1. References resolved from previous node outputs
            2. Service config from resolved_configs (keyed by node.key)
            3. Static config from node.config in the pipeline definition
        """
        node: Optional[Node] = next(
            (n for n in pipeline.nodes if n.name == node_name), None
        )
        if node is None:
            raise KeyError(
                f"Node '{node_name}' not found in pipeline definition."
            )

        node_def = NODES_MAP.get(node.key)
        if node_def is None:
            raise ValueError(
                f"Node key '{node.key}' (node '{node_name}') not found in NODES_MAP. "
                f"Registered keys: {list(NODES_MAP.keys())}"
            )

        # ── 1. Resolve references in node inputs ──────────────────────────────
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
            "Dispatching node '%s' (key=%s) | input_keys=%s",
            node_name, node.key, list(resolved_node_inputs.keys()),
        )

        # ── 3. Build Pydantic input model ─────────────────────────────────────
        if node_def.node_input_model is None:
            raise ValueError(
                f"Node '{node.key}' has no node_input_model defined. "
                "Every node must declare its Pydantic input model."
            )

        input_model = node_def.node_input_model(**resolved_node_inputs)

        # ── 4. Dispatch via Temporal — node_def.fn IS the @activity.defn ──────
        node_output: Dict[str, Any] = await workflow.execute_activity(
            node_def.fn,
            input_model,
            start_to_close_timeout=_NODE_TIMEOUT,
        )

        # Normalise output: Pydantic model → dict
        if hasattr(node_output, "model_dump"):
            node_output = node_output.model_dump()
        elif not isinstance(node_output, dict):
            node_output = {"output": node_output}

        outputs[node_name] = node_output
        workflow.logger.info(
            "Node '%s' completed | output_keys=%s",
            node_name, list(node_output.keys()),
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

    @staticmethod
    def _find_loop_back_node(
        entry_node: Optional[str], pipeline: Pipeline
    ) -> Optional[str]:
        """Find the node whose LOOP edge points back to entry_node."""
        if entry_node is None:
            return None
        from src.workflows.types import EdgesTypeEnum
        for edge in pipeline.edges:
            if edge.type == EdgesTypeEnum.LOOP and edge.target == entry_node:
                return edge.source
        return None