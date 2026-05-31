from __future__ import annotations
import re
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Optional, Union, get_args, get_origin

from .nodes import NODES_MAP
from .types import Pipeline, Node
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
    parts = raw_path.split(".")
    i = 0
    while i < len(parts):
        part = parts[i]
        if part == "*":
            if segments:
                segments[-1].wildcard = True
            i += 1
            continue

        idx_matches = re.findall(r"\[(\d+)\]", part)
        attr_name = re.sub(r"\[\d+\]", "", part)
        if not attr_name:
            i += 1
            continue
        seg = _PathSegment(
            attr=attr_name,
            indices=[int(x) for x in idx_matches],
        )
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
    """
    current: Any = root

    for seg_idx, seg in enumerate(segments):
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
            return results

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

    if origin is Union:
        inner_types = [t for t in get_args(target_type) if t is not type(None)]
        for t in inner_types:
            result = _coerce(value, t, reference, input_key, [])
            if result is not _SENTINEL:
                return result
        return value

    if origin in (list, tuple) and isinstance(value, (list, tuple)):
        args = get_args(target_type)
        item_type = args[0] if args else None
        if item_type:
            return [_coerce(v, item_type, reference, input_key, errors) for v in value]
        return list(value)

    coerce_fn = _COERCE_MAP.get(target_type)
    if coerce_fn is None:
        return value

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
        return value


# ─── Core Reference Resolver ──────────────────────────────────────────────────


def _resolve_single_reference(
    reference: str,
    outputs: dict[str, Any],
    input_key: str,
    errors: list[ResolutionError],
    default: Any = _SENTINEL,
) -> Any:
    """
    Resolve a single reference string like "node.outputs.field[0].sub" to its value.
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

    resolved_default: Any = _SENTINEL
    if default_clause.strip():
        resolved_default = _parse_default(default_clause)
    elif default is not _SENTINEL:
        resolved_default = default

    parts = ref_core.split(".", 2)  # ["node_name", "outputs", "path..."]
    node_name = parts[0]

    if len(parts) < 3:
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
        return reference

    segments = _parse_path(raw_path)
    value = _navigate(outputs[node_name], segments, reference, input_key, errors)

    if value is _SENTINEL:
        return resolved_default if resolved_default is not _SENTINEL else reference

    return value


# ─── Single-value resolver (used recursively) ─────────────────────────────────


def _resolve_value(
    value: Any,
    outputs: dict[str, Any],
    input_key: str,
    all_errors: list[ResolutionError],
    type_hints: dict[str, type],
    *,
    _top_level_key: str | None = None,  # the root inputs key, for type hint lookup
) -> Any:
    """
    Resolve a single value which may be:
      • a string  — scanned for node references and/or sibling placeholders
      • a dict    — recursively resolved (enables nested inputs like `values: {...}`)
      • a list    — each element recursively resolved
      • anything else — passed through as-is

    This is the core recursive workhorse called from both PASS 1 (for top-level
    inputs entries) and from itself when descending into nested dicts/lists.

    `_top_level_key` is the key under `inputs` we're currently resolving;
    it is used to look up type hints for the outermost value only.
    """
    lookup_key = _top_level_key or input_key

    # ── dict: recurse into every value ───────────────────────────────────────
    if isinstance(value, dict):
        return {
            k: _resolve_value(v, outputs, f"{input_key}.{k}", all_errors, type_hints)
            for k, v in value.items()
        }

    # ── list: recurse into every element ─────────────────────────────────────
    if isinstance(value, list):
        return [
            _resolve_value(item, outputs, f"{input_key}[{i}]", all_errors, type_hints)
            for i, item in enumerate(value)
        ]

    # ── non-string scalar: pass through (with optional top-level coercion) ───
    if not isinstance(value, str):
        target_type = type_hints.get(lookup_key)
        if target_type:
            return _coerce(value, target_type, "<static>", input_key, all_errors)
        return value

    # ── string: fast-path if no reference pattern present ────────────────────
    if not _HAS_REF.search(value):
        return value  # sibling placeholder substitution happens in PASS 2

    # ── find all node references ──────────────────────────────────────────────
    ref_matches = list(REF_PATTERN.finditer(value))
    if not ref_matches:
        return value

    target_type = type_hints.get(lookup_key)

    # Determine whether this is a template or a pure reference
    stripped = REF_PATTERN.sub("", value).strip()
    is_template = bool(stripped) or ("{" in value and "}" in value)

    if is_template:
        resolved_str = value
        for m in ref_matches:
            full_match = m.group(0)
            resolved_val = _resolve_single_reference(
                full_match, outputs, input_key, all_errors
            )
            resolved_str = resolved_str.replace(
                "{" + full_match + "}", str(resolved_val)
            ).replace(full_match, str(resolved_val))

        return (
            _coerce(resolved_str, target_type, value, input_key, all_errors)
            if target_type
            else resolved_str
        )

    else:
        resolved_values: list[Any] = [
            _resolve_single_reference(m.group(0), outputs, input_key, all_errors)
            for m in ref_matches
        ]
        final: Any = (
            resolved_values[0] if len(resolved_values) == 1 else resolved_values
        )
        return (
            _coerce(final, target_type, value, input_key, all_errors)
            if target_type
            else final
        )


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

    Handles arbitrarily nested dicts and lists, so inputs like:

        {
            "condition": "word_count >= min_words",
            "values": {
                "word_count": "groq_llm_node2.outputs.output.word_count",
                "min_words": 500,
            }
        }

    correctly resolve the references inside the nested ``values`` dict.

    Supported reference formats (anywhere in the tree):

    ┌──────────────────────────────────────────────────────────────────────┐
    │  Format                      │  Example                              │
    ├──────────────────────────────┼───────────────────────────────────────┤
    │  Direct                      │  node.outputs.field                   │
    │  Nested path                 │  node.outputs.a.b.c                   │
    │  Array index                 │  node.outputs.items[0].title          │
    │  Multi-dimensional index     │  node.outputs.matrix[1][2]            │
    │  Wildcard / map              │  node.outputs.items.*.title           │
    │  Default value               │  node.outputs.val | "fallback"        │
    │  Template interpolation      │  "Hello {node.outputs.name}!"         │
    │  Space-separated multi-ref   │  node1.outputs.x node2.outputs.y      │
    │  Sibling-key placeholder     │  "Topics: {topics}"  (key in inputs)  │
    │  Nested dict values          │  {"key": "node.outputs.field"}        │
    │  Nested list elements        │  ["node.outputs.x", "node.outputs.y"] │
    └──────────────────────────────┴───────────────────────────────────────┘

    Args:
        inputs:     Dict of input key → value (may contain references at any depth).
        outputs:    Dict of node_name → output produced by that node.
        type_hints: Optional dict of input key → Python type for coercion.
        strict:     If True, raises RuntimeError when any reference fails.
        log_level:  Python logging level for emitting resolution errors.

    Returns:
        ResolutionResult with `.resolved` dict and `.errors` list.
    """
    type_hints = type_hints or {}
    all_errors: list[ResolutionError] = []

    # ══════════════════════════════════════════════════════════════════════════
    # PASS 1 — Recursively resolve all node-output references
    #
    # _resolve_value handles strings, dicts, lists, and scalars uniformly.
    # Nested dicts (e.g. the `values` field of an if_node) are walked in full
    # so every leaf string is checked for references.
    # ══════════════════════════════════════════════════════════════════════════
    pass1: dict[str, Any] = {}

    for key, value in inputs.items():
        pass1[key] = _resolve_value(
            value, outputs, key, all_errors, type_hints, _top_level_key=key
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PASS 2 — Substitute {sibling_key} placeholders in top-level strings only
    #
    # After node references are resolved, some string values may still contain
    # {key} placeholders referring to other input keys resolved in pass 1.
    # We only do this at the top level (not recursing into nested dicts) because
    # nested dicts are self-contained argument bags for their node's input model.
    #
    # Rules:
    #   • Only string values containing {…} tokens are processed.
    #   • Only tokens matching a key in `inputs` are substituted.
    #   • list → comma-separated; other → str().
    #   • Unknown tokens are left intact.
    # ══════════════════════════════════════════════════════════════════════════
    _PLACEHOLDER = re.compile(r"\{([^}]+)\}")

    result_dict: dict[str, Any] = {}

    for key, value in pass1.items():
        if not isinstance(value, str) or "{" not in value:
            result_dict[key] = value
            continue

        def _replace_placeholder(m: re.Match, _pass1: dict = pass1) -> str:
            token = m.group(1).strip()
            if token not in _pass1:
                return m.group(0)
            sibling = _pass1[token]
            if isinstance(sibling, list):
                return ", ".join(str(v) for v in sibling)
            return str(sibling)

        substituted = _PLACEHOLDER.sub(_replace_placeholder, value)

        target_type = type_hints.get(key)
        result_dict[key] = (
            _coerce(substituted, target_type, value, key, all_errors)
            if target_type and substituted != value
            else substituted
        )

    result = ResolutionResult(resolved=result_dict, errors=all_errors)
    result.log_errors(log_level)

    if strict:
        result.raise_if_errors()

    return result


async def resolve_configs(pipeline: Pipeline, user_id: str) -> dict:

    resolved_configs = {}
    nodes_map = NODES_MAP

    for node in pipeline.nodes:
        node_def = nodes_map.get(node.key)
        if not node_def:
            raise ValueError(f"Node {node.key} not found in NODES_MAP")

        if node_def.service and "google" in node_def.service and node_def.type != "LLM":
            resolver = GoogleNodeConfigResolver()
            config = await resolver.resolve(node.key, user_id)
            resolved_configs[node.key] = config

    return resolved_configs
