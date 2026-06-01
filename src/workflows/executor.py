"""
executor.py — Full async workflow executor.

Walks an ExecutionPlan step by step, handling every edge type:
  LINEAR   → run node, store output, continue
  PARALLEL → asyncio.gather all branch starts concurrently
  MERGE    → already handled by plan ordering; just confirm all sources done
  IF       → run if_node, evaluate decision, execute true or false sub-plan
  SWITCH   → run switch_node, evaluate case, execute matching sub-plan

The executor is intentionally decoupled from Temporal. It works as a
standalone async engine. You can wrap each `_run_node` call in
`workflow.execute_activity(...)` to make it Temporal-native.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from .types import (
    ExecutionPlan,
    ExecutionStep,
    ExecutionStepKind,
    Node,
    Workflow,
)

logger = logging.getLogger(__name__)


# ─── Node runner protocol ─────────────────────────────────────────────────────
# The executor calls NODE_REGISTRY[node.key](resolved_inputs, node.config)
# and expects a dict back. You plug in your actual activity functions here.

NodeFn = Callable[[Dict[str, Any], Dict[str, Any]], Any]


# ─── Resolve inputs (imported from your resolve_inputs module) ─────────────────
# Keeping a local minimal version here for self-containment;
# swap with your full resolve_inputs.resolve_inputs_simple if preferred.


def _resolve(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Dict[str, Any]:
    """Thin shim — replace with resolve_inputs.resolve_inputs_simple in production."""
    try:
        from .utils import resolve_inputs

        return resolve_inputs(inputs, outputs).resolved
    except ImportError:
        return inputs  # fallback: pass through unresolved


# ─── Executor ─────────────────────────────────────────────────────────────────
class WorkflowExecutor:
    """
    Executes an ExecutionPlan produced by build_execution_plan().

    Usage:
        executor = WorkflowExecutor(workflow, node_registry)
        outputs  = await executor.run(plan)
    """

    def __init__(
        self,
        workflow: Workflow,
        node_registry: Dict[str, NodeFn],
    ):
        self.workflow = workflow
        self.node_registry = node_registry
        self._node_map: Dict[str, Node] = {n.name: n for n in workflow.nodes}

    # ─── Public entry point ───────────────────────────────────────────────────

    async def run(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute the full plan.

        Returns:
            Dict mapping node_name → output dict for every executed node.
        """
        outputs: Dict[str, Any] = {}
        await self._execute_plan(plan, outputs)
        return outputs

    # ─── Plan execution ───────────────────────────────────────────────────────

    async def _execute_plan(
        self,
        plan: ExecutionPlan,
        outputs: Dict[str, Any],
    ) -> None:
        for step in plan.steps:
            await self._execute_step(step, outputs)

    async def _execute_step(
        self,
        step: ExecutionStep,
        outputs: Dict[str, Any],
    ) -> None:

        # ── RUN ───────────────────────────────────────────────────────────────
        if step.kind == ExecutionStepKind.RUN:
            if len(step.nodes) == 1:
                await self._run_node(step.nodes[0], outputs)
            else:
                # Multiple nodes in a RUN step → run concurrently (parallel fan-out)
                await asyncio.gather(
                    *[self._run_node(name, outputs) for name in step.nodes]
                )

        # ── MERGE ─────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.MERGE:
            # All listed nodes should already be in outputs (ran in parallel).
            # This step is a semantic checkpoint — nothing to execute.
            missing = [n for n in step.nodes if n not in outputs]
            if missing:
                raise RuntimeError(
                    f"MERGE step reached but these nodes have not completed: {missing}"
                )
            logger.debug("MERGE checkpoint passed for: %s", step.nodes)

        # ── IF ────────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.IF:
            # The if_node itself was already run in a preceding RUN step.
            # Read its decision output.
            if_node_name = step.nodes[0]
            decision = self._get_output(if_node_name, outputs, "decision")

            if not isinstance(decision, bool):
                raise ValueError(
                    f"if_node '{if_node_name}' must output a bool 'decision', "
                    f"got {type(decision).__name__}: {decision!r}"
                )

            logger.info("IF '%s' → decision=%s", if_node_name, decision)

            chosen_plan = step.true_plan if decision else step.false_plan
            if chosen_plan:
                await self._execute_plan(chosen_plan, outputs)

        # ── SWITCH ────────────────────────────────────────────────────────────
        elif step.kind == ExecutionStepKind.SWITCH:
            switch_node_name = step.nodes[0]
            case_value = self._get_output(switch_node_name, outputs, "case")

            logger.info("SWITCH '%s' → case='%s'", switch_node_name, case_value)

            case_plans = step.case_plans or {}
            chosen_plan = case_plans.get(
                case_value, case_plans.get(step.default_case)  # fallback to default
            )
            if chosen_plan:
                await self._execute_plan(chosen_plan, outputs)
            else:
                logger.warning(
                    "SWITCH '%s': no plan for case '%s' and no default.",
                    switch_node_name,
                    case_value,
                )

    # ─── Single node execution ────────────────────────────────────────────────
    async def _run_node(
        self,
        node_name: str,
        outputs: Dict[str, Any],
    ) -> None:
        """
        Resolve inputs, call the node function, store the output.

        The node function is looked up from node_registry by node.key.
        It receives (resolved_inputs, node.config) and must return a dict.
        """
        node = self._node_map.get(node_name)
        if node is None:
            raise KeyError(f"Node '{node_name}' not found in workflow.")

        # Resolve references in inputs against accumulated outputs
        resolved_inputs = _resolve(node.inputs, outputs)

        logger.info(
            "RUN  %-30s | inputs_keys=%s", node_name, list(resolved_inputs.keys())
        )

        fn = self.node_registry.get(node.key)
        if fn is None:
            raise KeyError(
                f"No function registered for node key '{node.key}' "
                f"(node '{node_name}'). "
                f"Registered keys: {list(self.node_registry.keys())}"
            )

        # Call the node function
        # In Temporal: replace with await workflow.execute_activity(fn, ...)
        if asyncio.iscoroutinefunction(fn):
            result = await fn(resolved_inputs, node.config)
        else:
            result = await asyncio.to_thread(fn, resolved_inputs, node.config)

        # Normalise output to dict
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        elif not isinstance(result, dict):
            result = {"output": result}

        outputs[node_name] = result
        logger.info("DONE %-30s | output_keys=%s", node_name, list(result.keys()))

    # ─── Output helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _get_output(node_name: str, outputs: Dict[str, Any], key: str) -> Any:
        """
        Retrieve a specific key from a node's output dict.

        Handles two common output shapes:
          {"decision": True}                     → direct
          {"output": {"decision": True}}         → nested under "output"
        """
        node_out = outputs.get(node_name)
        if node_out is None:
            raise KeyError(f"Node '{node_name}' has no output yet.")

        if key in node_out:
            return node_out[key]

        # Check one level of nesting
        nested = node_out.get("output", {})
        if isinstance(nested, dict) and key in nested:
            return nested[key]

        raise KeyError(
            f"Key '{key}' not found in output of '{node_name}'. "
            f"Available: {list(node_out.keys())}"
        )
