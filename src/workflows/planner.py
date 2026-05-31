"""
planner.py — Converts ParsedNodeData list into a hierarchical ExecutionPlan.

Core insight: LOOP is a property of the PATH taken to reach a node, not a
property of the node itself. channel_classifier is a loop entry only when
reached via the False branch (through rewrite_node's back-edge). When reached
via the True branch (direct IF edge), it's a normal sequential node.

We track this by passing `via_loop_edge: bool` into each recursive sub-plan,
and only emitting a LOOP step when the entry into that sub-plan came via a
loop back-edge.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set

from .types import (
    EdgesTypeEnum,
    ExecutionPlan,
    ExecutionStep,
    ExecutionStepKind,
    ParsedNodeData,
    Pipeline,
)

# ─── Graph helpers ────────────────────────────────────────────────────────────


def _if_branches(node_name: str, pipeline: Pipeline):
    """Returns (true_target, false_target) for an IF control node."""
    true_t = false_t = None
    for e in pipeline.edges:
        if e.source == node_name and e.type == EdgesTypeEnum.IF:
            if e.decision is True:
                true_t = e.target
            else:
                false_t = e.target
    return true_t, false_t


def _switch_branches(node_name: str, pipeline: Pipeline) -> Dict[str, str]:
    """Returns {case_value: target_node} for a SWITCH control node."""
    return {
        e.case: e.target
        for e in pipeline.edges
        if e.source == node_name
        and e.type == EdgesTypeEnum.SWITCH
        and e.target not in ("end", "start")
    }


def _loop_back_source(entry_node: str, pipeline: Pipeline) -> Optional[str]:
    """Returns the node that has a LOOP edge pointing back to entry_node."""
    for e in pipeline.edges:
        if e.type == EdgesTypeEnum.LOOP and e.target == entry_node:
            return e.source
    return None


def _linear_successor(node_name: str, pipeline: Pipeline) -> Optional[str]:
    """Returns the single LINEAR successor of a node, or None."""
    for e in pipeline.edges:
        if (
            e.source == node_name
            and e.type == EdgesTypeEnum.LINEAR
            and e.target not in ("end", "start")
        ):
            return e.target
    return None


def _collect_subgraph(
    start: str,
    pipeline: Pipeline,
    all_node_names: Set[str],
    stop_before: Optional[Set[str]] = None,
) -> List[str]:
    """
    BFS from start, following all edges except LOOP back-edges.
    Stops before (excludes) any node in stop_before.
    Returns nodes in BFS order.
    """
    stop_before = stop_before or set()
    visited: Set[str] = set()
    order: List[str] = []
    queue = deque([start])

    while queue:
        n = queue.popleft()
        if n in visited or n in stop_before or n not in all_node_names:
            continue
        visited.add(n)
        order.append(n)

        for e in pipeline.edges:
            if (
                e.source == n
                and e.type != EdgesTypeEnum.LOOP
                and e.target not in visited
            ):
                queue.append(e.target)

    return order


def _kahn_sort(
    node_names: List[str],
    parsed_map: Dict[str, ParsedNodeData],
    scope: Set[str],
) -> List[str]:
    """
    Topological sort (Kahn's algorithm) over `node_names`,
    considering only dependencies that fall within `scope`.
    """
    node_set = set(node_names)
    in_degree: Dict[str, int] = {n: 0 for n in node_set}

    for n in node_set:
        p = parsed_map.get(n)
        if not p:
            continue
        for dep in p.dependencies:
            if dep in node_set and dep in scope:
                in_degree[n] += 1

    ready: deque[str] = deque(n for n in node_set if in_degree[n] == 0)
    order: List[str] = []

    while ready:
        # Prefer non-barrier nodes so control nodes sort last within their batch
        non_barriers = [
            n
            for n in ready
            if not (parsed_map[n].is_control_node if parsed_map.get(n) else False)
        ]
        node = (non_barriers or list(ready))[0]
        ready.remove(node)
        order.append(node)

        for n2 in node_set:
            p2 = parsed_map.get(n2)
            if p2 and node in p2.dependencies and node in scope:
                in_degree[n2] -= 1
                if in_degree[n2] == 0:
                    ready.append(n2)

    return order


# ─── Core plan builder ────────────────────────────────────────────────────────


def build_execution_plan(
    pipeline: Pipeline,
    parsed: List[ParsedNodeData],
    start_nodes: Optional[List[str]] = None,
    visited: Optional[Set[str]] = None,
    *,
    via_loop_edge: bool = False,  # True when this sub-plan is entered via a loop back-edge
) -> ExecutionPlan:
    """
    Recursively build an ExecutionPlan from the pipeline.

    The `via_loop_edge` parameter is the key fix: it tells the planner
    whether the start_nodes were reached via a LOOP back-edge. Only in
    that case should the first loop-entry node be wrapped in a LOOP step.
    """
    if visited is None:
        visited = set()

    all_node_names: Set[str] = {n.name for n in pipeline.nodes}
    parsed_map: Dict[str, ParsedNodeData] = {p.name: p for p in parsed}

    if start_nodes is None:
        # Entry nodes: nodes with no dependencies
        start_nodes = [p.name for p in parsed if not p.dependencies]

    plan = ExecutionPlan()

    # Collect all nodes in scope for this sub-plan (excluding already-visited)
    scope_nodes: List[str] = []
    for sn in start_nodes:
        for n in _collect_subgraph(sn, pipeline, all_node_names):
            if n not in visited and n not in scope_nodes:
                scope_nodes.append(n)

    if not scope_nodes:
        return plan

    scope_set = set(scope_nodes)

    # Topological sort within scope
    sorted_nodes = _kahn_sort(scope_nodes, parsed_map, scope=scope_set | visited)

    local_visited: Set[str] = set(visited)
    i = 0

    while i < len(sorted_nodes):
        node_name = sorted_nodes[i]

        if node_name in local_visited:
            i += 1
            continue

        p = parsed_map.get(node_name)
        if p is None:
            i += 1
            continue

        # ── LOOP ENTRY — only when we arrived here via a loop back-edge ───────
        #
        # If via_loop_edge=True and this is the first node in the sub-plan,
        # it's the re-entry point. Wrap the rest of this sub-plan in a LOOP.
        if via_loop_edge and i == 0 and p.is_loop_entry_node:
            loop_back = _loop_back_source(node_name, pipeline)

            # Build the loop body normally (via_loop_edge=False so we don't
            # wrap it again — the body is just sequential from here)
            loop_body = build_execution_plan(
                pipeline,
                parsed,
                start_nodes=[node_name],
                visited=set(local_visited),
                via_loop_edge=False,  # ← normal plan inside the loop body
            )

            plan.steps.append(
                ExecutionStep(
                    kind=ExecutionStepKind.LOOP,
                    nodes=[node_name],
                    loop_body=loop_body,
                    loop_entry=node_name,
                )
            )

            # Mark everything in the loop body as visited
            body_nodes = _collect_subgraph(node_name, pipeline, all_node_names)
            local_visited.update(body_nodes)
            if loop_back:
                local_visited.add(loop_back)
            break  # LOOP step covers the rest of this sub-plan

        # ── PARALLEL SOURCE ───────────────────────────────────────────────────
        if p.is_parallel_source:
            parallel_targets = [
                e.target
                for e in pipeline.edges
                if e.source == node_name
                and e.type == EdgesTypeEnum.PARALLEL
                and e.target not in ("end", "start")
            ]
            plan.steps.append(
                ExecutionStep(
                    kind=ExecutionStepKind.RUN,
                    nodes=[node_name],
                )
            )
            local_visited.add(node_name)

            plan.steps.append(
                ExecutionStep(
                    kind=ExecutionStepKind.RUN,
                    nodes=parallel_targets,
                )
            )
            local_visited.update(parallel_targets)
            i += 1
            continue

        # ── MERGE TARGET ──────────────────────────────────────────────────────
        if p.is_merge_target:
            merge_sources = [
                e.source
                for e in pipeline.edges
                if e.target == node_name and e.type == EdgesTypeEnum.MERGE
            ]
            plan.steps.append(
                ExecutionStep(
                    kind=ExecutionStepKind.MERGE,
                    nodes=merge_sources,
                )
            )

        # ── CONTROL NODE (if / switch) ────────────────────────────────────────
        if p.is_control_node:
            # Run the control node
            plan.steps.append(
                ExecutionStep(
                    kind=ExecutionStepKind.RUN,
                    nodes=[node_name],
                )
            )
            local_visited.add(node_name)

            out_types = {e.type for e in pipeline.edges if e.source == node_name}

            if EdgesTypeEnum.IF in out_types:
                true_t, false_t = _if_branches(node_name, pipeline)

                # True branch: reached directly (no loop edge) → via_loop_edge=False
                true_plan = (
                    build_execution_plan(
                        pipeline,
                        parsed,
                        start_nodes=[true_t] if true_t else [],
                        visited=set(local_visited),
                        via_loop_edge=False,
                    )
                    if true_t
                    else ExecutionPlan()
                )

                # False branch: check if it eventually loops back somewhere
                # The False branch itself starts normally; the LOOP is detected
                # inside the False branch when the loop-back node's successor
                # is re-entered via a loop edge.
                false_plan = (
                    build_execution_plan(
                        pipeline,
                        parsed,
                        start_nodes=[false_t] if false_t else [],
                        visited=set(local_visited),
                        via_loop_edge=False,
                    )
                    if false_t
                    else ExecutionPlan()
                )

                plan.steps.append(
                    ExecutionStep(
                        kind=ExecutionStepKind.IF,
                        nodes=[node_name],
                        true_plan=true_plan,
                        false_plan=false_plan,
                    )
                )

                # Mark branch subgraphs visited
                for t in [true_t, false_t]:
                    if t:
                        local_visited.update(
                            _collect_subgraph(t, pipeline, all_node_names)
                        )

            elif EdgesTypeEnum.SWITCH in out_types:
                case_map = _switch_branches(node_name, pipeline)
                case_plans: Dict[str, ExecutionPlan] = {}

                for case_val, target in case_map.items():
                    case_plans[case_val] = build_execution_plan(
                        pipeline,
                        parsed,
                        start_nodes=[target],
                        visited=set(local_visited),
                        via_loop_edge=False,
                    )
                    local_visited.update(
                        _collect_subgraph(target, pipeline, all_node_names)
                    )

                plan.steps.append(
                    ExecutionStep(
                        kind=ExecutionStepKind.SWITCH,
                        nodes=[node_name],
                        case_plans=case_plans,
                    )
                )

            i += 1
            continue

        # ── LOOP-BACK NODE (e.g. rewrite_node) ───────────────────────────────
        #
        # This node's output determines whether the loop continues.
        # After running it, the loop back-edge points to the loop entry.
        # We run it normally here; the LOOP wrapper (which handles retrying)
        # is created in the parent False-branch sub-plan.
        if p.is_loop_back_node:
            plan.steps.append(
                ExecutionStep(
                    kind=ExecutionStepKind.RUN,
                    nodes=[node_name],
                )
            )
            local_visited.add(node_name)

            # After the loop-back node, follow the LOOP edge to the entry node
            loop_target = next(
                (
                    e.target
                    for e in pipeline.edges
                    if e.source == node_name and e.type == EdgesTypeEnum.LOOP
                ),
                None,
            )

            if loop_target and loop_target not in local_visited:
                # Recurse into the loop entry — this time WITH via_loop_edge=True
                # so it gets wrapped in a LOOP step
                loop_continuation = build_execution_plan(
                    pipeline,
                    parsed,
                    start_nodes=[loop_target],
                    visited=set(local_visited),
                    via_loop_edge=True,
                )
                plan.steps.extend(loop_continuation.steps)
                local_visited.update(
                    _collect_subgraph(loop_target, pipeline, all_node_names)
                )

            i += 1
            continue

        # ── NORMAL RUN ────────────────────────────────────────────────────────
        plan.steps.append(
            ExecutionStep(
                kind=ExecutionStepKind.RUN,
                nodes=[node_name],
            )
        )
        local_visited.add(node_name)
        i += 1

    return plan
