from __future__ import annotations
import re
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Optional, Union, get_args, get_origin

from .nodes import NODES_MAP
from .types import Pipeline, NodeDependency, Node
from src.integrations.googlecloud.resolvers import GoogleNodeConfigResolver

logger = logging.getLogger(__name__)


class ResolutionErrorCode(Enum):
    NODE_NOT_FOUND = auto()
    PATH_NOT_FOUND = auto()
    INDEX_OUT_OF_RANGE = auto()
    TYPE_NOT_SUBSCRIPTABLE = auto()
    COERCION_FAILED = auto()
    MALFORMED_REFERENCE = auto()


@dataclass
class ResolutionError:
    """Structured diagnostic produced when a reference cannot be resolved."""

    reference: str
    input_key: str
    error_code: ResolutionErrorCode
    detail: str
    suggestion: str = ""

    def __str__(self) -> str:
        parts = [
            f"[{self.error_code.name}] Could not resolve '{self.reference}' "
            f"(key='{self.input_key}'): {self.detail}"
        ]
        if self.suggestion:
            parts.append(f"  → Suggestion: {self.suggestion}")
        return "\n".join(parts)


@dataclass
class ResolutionResult:
    """Return value of resolve_inputs — resolved dict + any diagnostics."""

    resolved: dict[str, Any]
    errors: list[ResolutionError] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def raise_if_errors(self) -> None:
        """Raise a RuntimeError aggregating all resolution failures."""
        if self.errors:
            msg = "\n".join(str(e) for e in self.errors)
            raise RuntimeError(f"resolve_inputs encountered errors:\n{msg}")

    def log_errors(self, level: int = logging.WARNING) -> None:
        for err in self.errors:
            logger.log(level, str(err))


# ─── Reference Grammar ────────────────────────────────────────────────────────
#
# Full reference syntax (EBNF-ish):
#
#   reference    ::= node_ref default_clause?
#   node_ref     ::= IDENT ".outputs" path_segment+
#   path_segment ::= "." IDENT ( "[" INT "]" )* ( ".*" )?
#   default_clause ::= "|" default_value
#   default_value  ::= quoted_str | number | "true" | "false" | "null"
#   quoted_str     ::= '"' [^"]* '"' | "'" [^']* "'"
#
# Examples:
#   node1.outputs.items[0].title
#   node2.outputs.result | "fallback"
#   node3.outputs.tags.*
#   node4.outputs.matrix[1][2]

_IDENT = r"[a-zA-Z_][a-zA-Z0-9_]*"
_INDEX = r"\[\d+\]"
_WILDCARD = r"\.\*"

# Matches a full node reference optionally followed by "| default"
_REF_CORE = (
    rf"(?:{_IDENT})"  # node_name
    rf"\.outputs"  # literal keyword
    rf"(?:\.{_IDENT}"  # .field
    rf"(?:{_INDEX})*"  # optional [idx] repetitions
    rf"(?:{_WILDCARD})?)+"  # optional .* at end of a segment
)
_DEFAULT_CLAUSE = (
    r"(?:\s*\|\s*" r'(?:"[^"]*"|\'[^\']*\'|true|false|null|-?\d+(?:\.\d+)?))?'
)
REF_PATTERN = re.compile(
    rf"(?P<ref>{_REF_CORE})" rf"(?P<default>{_DEFAULT_CLAUSE})",
    re.ASCII,
)

# Lighter pattern used to detect any reference in a string quickly
_HAS_REF = re.compile(rf"\b{_IDENT}\.outputs\b", re.ASCII)


# ─── Path Parsing ─────────────────────────────────────────────────────────────


@dataclass
class _PathSegment:
    attr: str
    indices: list[int] = field(default_factory=list)
    wildcard: bool = False


def _parse_path(raw_path: str) -> list[_PathSegment]:
    """
    Parse "field[0][1].other.*" into a list of _PathSegment objects.
    raw_path is everything after "node.outputs."
    """
    segments: list[_PathSegment] = []
    # Split on dots not followed by * (to keep .* attached to previous segment)
    # We handle the .* wildcard as a flag on the segment.
    parts = raw_path.split(".")
    i = 0
    while i < len(parts):
        part = parts[i]
        if part == "*":
            # Attach wildcard to last segment
            if segments:
                segments[-1].wildcard = True
            i += 1
            continue

        # Extract array indices from "field[0][2]"
        idx_matches = re.findall(r"\[(\d+)\]", part)
        attr_name = re.sub(r"\[\d+\]", "", part)
        if not attr_name:
            i += 1
            continue
        seg = _PathSegment(
            attr=attr_name,
            indices=[int(x) for x in idx_matches],
        )
        # Peek ahead: if next part is *, mark wildcard and consume it
        if i + 1 < len(parts) and parts[i + 1] == "*":
            seg.wildcard = True
            i += 1
        segments.append(seg)
        i += 1
    return segments


# ─── Path Navigation ──────────────────────────────────────────────────────────

_SENTINEL = object()


def _get_attr_or_key(obj: Any, key: str) -> Any:
    """Access obj[key] (dict) or obj.key (object/Pydantic model)."""
    if isinstance(obj, dict):
        return obj.get(key, _SENTINEL)
    val = getattr(obj, key, _SENTINEL)
    return val


def _navigate(
    root: Any,
    segments: list[_PathSegment],
    reference: str,
    input_key: str,
    errors: list[ResolutionError],
) -> Any:
    """
    Walk the resolved output tree along `segments`.
    Returns _SENTINEL on failure (error appended to `errors`).
    Supports:
      - Dict / object attribute access
      - Array indexing  (seg.indices)
      - Wildcard mapping (seg.wildcard → list of mapped values)
    """
    current: Any = root

    for seg_idx, seg in enumerate(segments):
        # ── Attribute / key access ────────────────────────────────────────────
        val = _get_attr_or_key(current, seg.attr)
        if val is _SENTINEL:
            errors.append(
                ResolutionError(
                    reference=reference,
                    input_key=input_key,
                    error_code=ResolutionErrorCode.PATH_NOT_FOUND,
                    detail=f"Key/attribute '{seg.attr}' not found in {type(current).__name__}",
                    suggestion=(
                        f"Available keys: {list(current.keys())}"
                        if isinstance(current, dict)
                        else f"Available attrs: {[a for a in dir(current) if not a.startswith('_')]}"
                    ),
                )
            )
            return _SENTINEL
        current = val

        # ── Array indexing ────────────────────────────────────────────────────
        for idx in seg.indices:
            if not hasattr(current, "__getitem__"):
                errors.append(
                    ResolutionError(
                        reference=reference,
                        input_key=input_key,
                        error_code=ResolutionErrorCode.TYPE_NOT_SUBSCRIPTABLE,
                        detail=(
                            f"Cannot index into {type(current).__name__} "
                            f"at segment '{seg.attr}[{idx}]'"
                        ),
                    )
                )
                return _SENTINEL
            try:
                current = current[idx]
            except (IndexError, KeyError):
                errors.append(
                    ResolutionError(
                        reference=reference,
                        input_key=input_key,
                        error_code=ResolutionErrorCode.INDEX_OUT_OF_RANGE,
                        detail=(
                            f"Index [{idx}] out of range for collection of "
                            f"length {len(current)} at segment '{seg.attr}'"
                        ),
                        suggestion=(
                            f"Valid indices: 0..{len(current) - 1}"
                            if current
                            else "Collection is empty"
                        ),
                    )
                )
                return _SENTINEL

        # ── Wildcard mapping ──────────────────────────────────────────────────
        if seg.wildcard:
            remaining = segments[seg_idx + 1 :]
            if not hasattr(current, "__iter__") or isinstance(current, (str, bytes)):
                errors.append(
                    ResolutionError(
                        reference=reference,
                        input_key=input_key,
                        error_code=ResolutionErrorCode.TYPE_NOT_SUBSCRIPTABLE,
                        detail=f"Wildcard '.*' applied to non-iterable {type(current).__name__}",
                    )
                )
                return _SENTINEL

            results: list[Any] = []
            for item in current:
                if remaining:
                    mapped = _navigate(item, remaining, reference, input_key, errors)
                    if mapped is not _SENTINEL:
                        results.append(mapped)
                else:
                    results.append(item)
            return results  # early return — remaining segments already consumed

    return current


# ─── Default Value Parsing ────────────────────────────────────────────────────


def _parse_default(default_clause: str) -> Any:
    """Parse '| default_value' string into a Python value."""
    raw = default_clause.strip().lstrip("|").strip()
    if raw in ("null", ""):
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw.startswith(('"', "'")):
        return raw[1:-1]
    try:
        return int(raw) if "." not in raw else float(raw)
    except ValueError:
        return raw


# ─── Type Coercion ────────────────────────────────────────────────────────────

_COERCE_MAP: dict[type, type] = {
    int: int,
    float: float,
    bool: bool,
    str: str,
}


def _coerce(
    value: Any,
    target_type: type,
    reference: str,
    input_key: str,
    errors: list[ResolutionError],
) -> Any:
    """Attempt to cast `value` to `target_type`. Returns value unchanged on failure."""
    if target_type is None or isinstance(value, target_type):
        return value

    origin = get_origin(target_type)

    # Handle Optional[X]
    if origin is Union:
        inner_types = [t for t in get_args(target_type) if t is not type(None)]
        for t in inner_types:
            result = _coerce(value, t, reference, input_key, [])
            if result is not _SENTINEL:
                return result
        return value

    # Handle List[X]
    if origin in (list, tuple) and isinstance(value, (list, tuple)):
        args = get_args(target_type)
        item_type = args[0] if args else None
        if item_type:
            return [_coerce(v, item_type, reference, input_key, errors) for v in value]
        return list(value)

    coerce_fn = _COERCE_MAP.get(target_type)
    if coerce_fn is None:
        return value  # Unknown target type — pass through

    try:
        return coerce_fn(value)
    except (ValueError, TypeError) as exc:
        errors.append(
            ResolutionError(
                reference=reference,
                input_key=input_key,
                error_code=ResolutionErrorCode.COERCION_FAILED,
                detail=f"Cannot coerce {type(value).__name__} → {target_type.__name__}: {exc}",
                suggestion=f"Ensure '{reference}' produces a value compatible with {target_type.__name__}",
            )
        )
        return value  # Graceful: return original rather than crashing


# ─── Core Reference Resolver ──────────────────────────────────────────────────


def _resolve_single_reference(
    reference: str,
    outputs: dict[str, Any],
    input_key: str,
    errors: list[ResolutionError],
    default: Any = _SENTINEL,
) -> Any:
    """
    Resolve a single reference string to its actual value.

    Reference format:
        node_name.outputs[.field[idx][*]]+ [| default]

    Returns:
        Resolved value, the provided default, or the original reference string
        (with an error recorded) if resolution fails and no default was given.
    """
    m = REF_PATTERN.match(reference.strip())
    if not m:
        errors.append(
            ResolutionError(
                reference=reference,
                input_key=input_key,
                error_code=ResolutionErrorCode.MALFORMED_REFERENCE,
                detail="Reference does not match expected pattern 'node.outputs.path'",
                suggestion="Format: node_name.outputs.field[idx].nested.*",
            )
        )
        return default if default is not _SENTINEL else reference

    ref_core = m.group("ref")
    default_clause = m.group("default") or ""

    # ── Parse default from inline clause or caller-supplied value ────────────
    resolved_default: Any = _SENTINEL
    if default_clause.strip():
        resolved_default = _parse_default(default_clause)
    elif default is not _SENTINEL:
        resolved_default = default

    # ── Split node name + path ────────────────────────────────────────────────
    parts = ref_core.split(".", 2)  # ["node_name", "outputs", "path..."]
    node_name = parts[0]

    if len(parts) < 3:
        # "node.outputs" with no path — return entire node output
        if node_name not in outputs:
            errors.append(
                ResolutionError(
                    reference=reference,
                    input_key=input_key,
                    error_code=ResolutionErrorCode.NODE_NOT_FOUND,
                    detail=f"Node '{node_name}' not found in outputs",
                    suggestion=f"Available nodes: {list(outputs.keys())}",
                )
            )
            return resolved_default if resolved_default is not _SENTINEL else reference
        return outputs[node_name]

    raw_path = parts[2]

    # ── Node existence check ──────────────────────────────────────────────────
    if node_name not in outputs:
        if resolved_default is not _SENTINEL:
            return resolved_default
        errors.append(
            ResolutionError(
                reference=reference,
                input_key=input_key,
                error_code=ResolutionErrorCode.NODE_NOT_FOUND,
                detail=f"Node '{node_name}' has no recorded output yet",
                suggestion=f"Available nodes: {list(outputs.keys())}",
            )
        )
        return reference  # Graceful: keep original

    # ── Navigate path ─────────────────────────────────────────────────────────
    segments = _parse_path(raw_path)
    value = _navigate(outputs[node_name], segments, reference, input_key, errors)

    if value is _SENTINEL:
        return resolved_default if resolved_default is not _SENTINEL else reference

    return value


# ─── Public API ───────────────────────────────────────────────────────────────


def resolve_inputs(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    type_hints: Optional[dict[str, type]] = None,
    *,
    strict: bool = False,
    log_level: int = logging.WARNING,
) -> ResolutionResult:
    """
    Resolve all input references based on previous node outputs.

    Supports the following reference formats in any string value:

    ┌──────────────────────────────────────────────────────────────────────┐
    │  Format                      │  Example                              │
    ├──────────────────────────────┼───────────────────────────────────────┤
    │  Direct                      │  node.outputs.field                   │
    │  Nested                      │  node.outputs.a.b.c                   │
    │  Array index                 │  node.outputs.items[0].title          │
    │  Multi-dimensional index     │  node.outputs.matrix[1][2]            │
    │  Wildcard / map              │  node.outputs.items.*.title           │
    │  Default value               │  node.outputs.val | "fallback"        │
    │  Template interpolation      │  "Hello {node.outputs.name}!"         │
    │  Space-separated multi-ref   │  node1.outputs.x node2.outputs.y      │
    └──────────────────────────────┴───────────────────────────────────────┘

    Args:
        inputs:     Dict of input key → value (may contain references).
        outputs:    Dict of node_name → output produced by that node.
        type_hints: Optional dict of input key → Python type for coercion.
                    e.g. {"temperature": float, "tags": list[str]}
        strict:     If True, raises RuntimeError when any reference fails.
        log_level:  Python logging level for emitting resolution errors.

    Returns:
        ResolutionResult with `.resolved` dict and `.errors` list.
    """
    type_hints = type_hints or {}
    result_dict: dict[str, Any] = {}
    all_errors: list[ResolutionError] = []

    for key, value in inputs.items():
        target_type = type_hints.get(key)

        # ── Non-string: pass through (with optional coercion) ─────────────────
        if not isinstance(value, str):
            result_dict[key] = (
                _coerce(value, target_type, "<static>", key, all_errors)
                if target_type
                else value
            )
            continue

        # ── Fast path: no reference pattern present ───────────────────────────
        if not _HAS_REF.search(value):
            result_dict[key] = (
                _coerce(value, target_type, "<static>", key, all_errors)
                if target_type
                else value
            )
            continue

        # ── Find all references (with optional default clauses) ───────────────
        ref_matches = list(REF_PATTERN.finditer(value))

        if not ref_matches:
            result_dict[key] = value
            continue

        # ── Determine resolution mode ─────────────────────────────────────────
        # Template mode: the raw string has content outside of references
        stripped = REF_PATTERN.sub("", value).strip()
        is_template = bool(stripped) or ("{" in value and "}" in value)

        if is_template:
            # ── Template interpolation ────────────────────────────────────────
            resolved_str = value
            for m in ref_matches:
                full_match = m.group(0)
                ref_core = m.group("ref")

                resolved_val = _resolve_single_reference(
                    full_match, outputs, key, all_errors
                )
                # In templates: replace {ref} blocks or bare refs
                resolved_str = resolved_str.replace(
                    "{" + full_match + "}", str(resolved_val)
                ).replace(full_match, str(resolved_val))

            result_dict[key] = (
                _coerce(resolved_str, target_type, value, key, all_errors)
                if target_type
                else resolved_str
            )

        else:
            # ── Pure reference(s): single or space-separated ──────────────────
            resolved_values: list[Any] = []
            for m in ref_matches:
                resolved_val = _resolve_single_reference(
                    m.group(0), outputs, key, all_errors
                )
                resolved_values.append(resolved_val)

            if len(resolved_values) == 1:
                final = resolved_values[0]
            else:
                final = resolved_values

            result_dict[key] = (
                _coerce(final, target_type, value, key, all_errors)
                if target_type
                else final
            )

    result = ResolutionResult(resolved=result_dict, errors=all_errors)
    result.log_errors(log_level)

    if strict:
        result.raise_if_errors()

    return result


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