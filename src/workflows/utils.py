from collections import defaultdict, deque
from pydantic import BaseModel
from .types import Pipeline, NodeDependency, Node
from .nodes import NODES_MAP
from src.integrations.googlecloud.resolvers import GoogleNodeConfigResolver
import re


def resolve_inputs(inputs: dict, outputs: dict) -> dict:
    """
    Resolve all input references based on previous node outputs.

    Handles multiple reference formats:
    1. Direct references: "node_name.outputs.path" -> resolves to actual value
    2. Multiple space-separated: "node1.outputs.x node2.outputs.y" -> list of values
    3. Template strings: "text {ref} more text" -> interpolates resolved values
    4. Mixed references in space-separated format

    Args:
        inputs: Dict of input keys to values (some may contain references)
        outputs: Dict of node_name -> output_value from previous executions

    Returns:
        Dict with all references resolved to actual values
    """

    resolved = {}

    for key, value in inputs.items():
        if not isinstance(value, str):
            # Non-string values pass through unchanged
            resolved[key] = value
            continue

        # Extract all references from the value using regex pattern
        # Pattern matches: node_name.outputs.path.to.value
        pattern = r"\b[a-zA-Z_][a-zA-Z0-9_]*\.outputs(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\b"
        references = re.findall(pattern, value)

        if not references:
            # No references found, keep the value as-is
            resolved[key] = value
            continue

        # Check if value is purely references (space-separated) or template with references
        if "{" in value and "}" in value:
            # Template string: resolve and interpolate
            resolved_value = value
            for ref in references:
                resolved_val = _resolve_single_reference(ref, outputs)
                # Replace reference in template (handle both {ref} and direct ref)
                resolved_value = resolved_value.replace(ref, str(resolved_val))
            resolved[key] = resolved_value
        else:
            # Pure reference(s): space-separated or single
            resolved_values = []
            for ref in references:
                resolved_val = _resolve_single_reference(ref, outputs)
                resolved_values.append(resolved_val)

            # Handle single vs multiple references
            if len(resolved_values) == 1:
                resolved[key] = resolved_values[0]
            elif len(resolved_values) > 1:
                # Multiple references: return as list
                resolved[key] = resolved_values
            else:
                resolved[key] = value

    return resolved


def _resolve_single_reference(reference: str, outputs: dict):
    """
    Resolve a single reference to its actual value.
    Reference format: node_name.outputs.path.to.value
    Returns the original reference string if not found.
    """
    if not ("." in reference and "outputs" in reference):
        return reference

    try:
        parts = reference.split(".")
        node_name = parts[0]

        # Validate structure: node.outputs.path
        if len(parts) < 2 or parts[1] != "outputs":
            return reference

        if node_name not in outputs:
            # Node output not yet available
            return reference

        node_output = outputs[node_name]
        # Get the nested path (everything after .outputs)
        path_parts = parts[2:]  # skip node_name and outputs

        # Navigate through nested structure
        current = node_output
        for part in path_parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return reference
            elif hasattr(current, part):
                # Handle pydantic models and objects with attributes
                current = getattr(current, part, None)
                if current is None:
                    return reference
            else:
                return reference

        return current
    except (IndexError, KeyError, AttributeError):
        return reference


def topological_sort(dependency: NodeDependency, nodes: list[Node]) -> list[str]:
    """Returns the valid order for the nodes to execute without dependency error."""

    # Build graph: node -> list of nodes that depend on it (reverse of dependency)
    graph = defaultdict(list)
    in_degree = {node.name: 0 for node in nodes}

    for node in nodes:
        deps = dependency.data.get(node.name, [])
        for dep in deps:
            graph[dep].append(node.name)
        in_degree[node.name] = len(deps)

    # Queue for nodes with no dependencies

    queue = deque([node for node in in_degree if in_degree[node] == 0])
    order = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for dependent in graph[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(nodes):
        raise ValueError("Cycle detected in dependencies")

    return order


async def resolve_configs(pipeline: Pipeline, user_id: str) -> dict:

    resolved_configs = {}
    nodes_map = NODES_MAP

    for node in pipeline.nodes:
        node_def = nodes_map.get(node.key)
        if not node_def:
            raise ValueError(f"Node {node.key} not found in NODES_MAP")

        if node_def.service and "google" in node_def.service:
            resolver = GoogleNodeConfigResolver()
            config = await resolver.resolve(node.key, user_id)
            resolved_configs[node.key] = config

    return resolved_configs
