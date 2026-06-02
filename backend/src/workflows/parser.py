"""
parser.py — Converts a Workflow into a list of ParsedNodeData.

Fixes over original:
  1. Dependencies derived from EDGES (not input string scanning) — correct and fast.
     Input scanning was unreliable (substring collisions, missed nested dicts).
  2. All flags computed correctly from edge types.
"""

from __future__ import annotations

from typing import Dict, List, Set

from .types import (
    Edge,
    EdgesTypeEnum,
    ParsedNodeData,
    Workflow,
)


def parse_workflow(workflow: Workflow) -> List[ParsedNodeData]:
    """
    Analyse the workflow graph and return one ParsedNodeData per node.

    Key design choice: dependencies are derived purely from edges, not from
    scanning input strings. This is correct because:
      - The edges ARE the authoritative execution graph.
      - Input references (node.outputs.x) are resolved at runtime by
        resolve_inputs(); the parser doesn't need to replicate that.
    """

    node_names: Set[str] = {n.name for n in workflow.nodes}
    edges = workflow.edges

    # Index edges for O(1) lookups
    # edges_by_target[node] = list of edges whose target is node
    edges_by_target: Dict[str, List[Edge]] = {n: [] for n in node_names}
    # edges_by_source[node] = list of edges whose source is node
    edges_by_source: Dict[str, List[Edge]] = {n: [] for n in node_names}

    for edge in edges:
        if edge.target in edges_by_target:
            edges_by_target[edge.target].append(edge)
        if edge.source in edges_by_source:
            edges_by_source[edge.source].append(edge)

    parsed: List[ParsedNodeData] = []

    for node in workflow.nodes:
        name          = node.name
        in_edges      = edges_by_target[name]   # edges arriving at this node
        out_edges     = edges_by_source[name]   # edges leaving this node

        # ── Dependencies ──────────────────────────────────────────────────────
        # A node depends on its source nodes via all edge types other than the
        # virtual start node.
        dependencies: List[str] = [
            e.source
            for e in in_edges
            if e.source != "start"
        ]

        # ── Control node ──────────────────────────────────────────────────────
        # A node is a control node if it has outgoing IF or SWITCH edges.
        outgoing_types = {e.type for e in out_edges}
        is_control_node = (
            EdgesTypeEnum.IF     in outgoing_types or
            EdgesTypeEnum.SWITCH in outgoing_types
        )

        # ── If-branch node ────────────────────────────────────────────────────
        # A node is an if-branch if it is the TARGET of an IF edge.
        if_in_edges = [e for e in in_edges if e.type == EdgesTypeEnum.IF]
        is_if_branch = len(if_in_edges) > 0
        # There should only ever be one IF edge arriving (True or False branch).
        if_decision  = if_in_edges[0].decision if if_in_edges else None

        # ── Switch-branch node ────────────────────────────────────────────────
        switch_in_edges = [e for e in in_edges if e.type == EdgesTypeEnum.SWITCH]
        is_switch_branch = len(switch_in_edges) > 0
        switch_case      = switch_in_edges[0].case if switch_in_edges else None

        # ── Parallel source ───────────────────────────────────────────────────
        is_parallel_source = EdgesTypeEnum.PARALLEL in outgoing_types

        # ── Merge target ──────────────────────────────────────────────────────
        merge_in = [e for e in in_edges if e.type == EdgesTypeEnum.MERGE]
        is_merge_target = len(merge_in) > 0

        parsed.append(ParsedNodeData(
            name               = name,
            dependencies       = dependencies,
            is_control_node    = is_control_node,
            is_if_branch       = is_if_branch,
            is_switch_branch   = is_switch_branch,
            is_parallel_source = is_parallel_source,
            is_merge_target    = is_merge_target,
            if_decision        = if_decision,
            switch_case        = switch_case,
        ))

    return parsed