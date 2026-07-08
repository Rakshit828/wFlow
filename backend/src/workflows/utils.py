from __future__ import annotations
import re
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Optional, Union, get_args, get_origin

from .nodes import NODES_MAP
from .types import Workflow, Node

logger = logging.getLogger(__name__)


class ResolutionErrorCode(Enum):
    NODE_NOT_FOUND = auto()
    PATH_NOT_FOUND = auto()
    INDEX_OUT_OF_RANGE = auto()
    TYPE_NOT_SUBSCRIPTABLE = auto()
    COERCION_FAILED = auto()
    MALFORMED_REFERENCE = auto()
    CONTEXT_PATH_NOT_FOUND = auto()  # ← new


@dataclass
class ResolutionError:
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
    resolved: dict[str, Any]
    errors: list[ResolutionError] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def raise_if_errors(self) -> None:
        if self.errors:
            msg = "\n".join(str(e) for e in self.errors)
            raise RuntimeError(f"resolve_inputs encountered errors:\n{msg}")

    def log_errors(self, level: int = logging.WARNING) -> None:
        for err in self.errors:
            logger.log(level, str(err))


# ─── Reference grammar ────────────────────────────────────────────────────────
#
# Two reference families, both share the default-value clause syntax:
#
#   Node reference:
#       node_name.outputs.path[idx].*  [| default]
#
#   Context reference (NEW):
#       context.path[idx].*            [| default]
#
# The regex below matches BOTH families in a single pass.
# The distinguishing logic is in _resolve_single_reference.

_IDENT = r"[a-zA-Z_][a-zA-Z0-9_]*"
_INDEX = r"\[\d+\]"
_WILDCARD = r"\.\*"

# Matches either:
#   context.<path>
#   <node>.outputs.<path>
_REF_CORE = (
    rf"(?:"
    rf"context"  # context prefix
    rf"|"
    rf"(?:{_IDENT})\.outputs"  # node.outputs
    rf")"
    rf"(?:\.{_IDENT}(?:{_INDEX})*(?:{_WILDCARD})?)+"  # .field[idx].*
)

_DEFAULT_CLAUSE = (
    r"(?:\s*\|\s*" r'(?:"[^"]*"|\'[^\']*\'|true|false|null|-?\d+(?:\.\d+)?))?'
)

REF_PATTERN = re.compile(
    rf"(?P<ref>{_REF_CORE})(?P<default>{_DEFAULT_CLAUSE})",
    re.ASCII,
)

# Fast pre-check: does the string contain ANY reference at all?
_HAS_REF = re.compile(
    rf"(?:\bcontext\.|\b{_IDENT}\.outputs\.)",
    re.ASCII,
)


# ─── Path parsing ─────────────────────────────────────────────────────────────


@dataclass
class _PathSegment:
    attr: str
    indices: list[int] = field(default_factory=list)
    wildcard: bool = False


def _parse_path(raw_path: str) -> list[_PathSegment]:
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


# ─── Path navigation ──────────────────────────────────────────────────────────

_SENTINEL = object()


def _get_attr_or_key(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, _SENTINEL)
    return getattr(obj, key, _SENTINEL)


def _navigate(
    root: Any,
    segments: list[_PathSegment],
    reference: str,
    input_key: str,
    errors: list[ResolutionError],
    *,
    error_code_not_found: ResolutionErrorCode = ResolutionErrorCode.PATH_NOT_FOUND,
) -> Any:
    current: Any = root
    for seg_idx, seg in enumerate(segments):
        val = _get_attr_or_key(current, seg.attr)
        if val is _SENTINEL:
            errors.append(
                ResolutionError(
                    reference=reference,
                    input_key=input_key,
                    error_code=error_code_not_found,
                    detail=(
                        f"Key/attribute '{seg.attr}' not found in "
                        f"{type(current).__name__}"
                    ),
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
                            f"Valid indices: 0..{len(current)-1}"
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
                        detail=(
                            f"Wildcard '.*' applied to non-iterable "
                            f"{type(current).__name__}"
                        ),
                    )
                )
                return _SENTINEL
            results: list[Any] = []
            for item in current:
                if remaining:
                    mapped = _navigate(
                        item,
                        remaining,
                        reference,
                        input_key,
                        errors,
                        error_code_not_found=error_code_not_found,
                    )
                    if mapped is not _SENTINEL:
                        results.append(mapped)
                else:
                    results.append(item)
            return results

    return current


# ─── Default value parsing ────────────────────────────────────────────────────


def _parse_default(clause: str) -> Any:
    raw = clause.strip().lstrip("|").strip()
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


# ─── Type coercion ────────────────────────────────────────────────────────────

_COERCE_MAP: dict[type, type] = {int: int, float: float, bool: bool, str: str}


def _coerce(
    value: Any,
    target_type: type,
    reference: str,
    input_key: str,
    errors: list[ResolutionError],
) -> Any:
    if target_type is None or isinstance(value, target_type):
        return value
    origin = get_origin(target_type)
    if origin is Union:
        for t in [t for t in get_args(target_type) if t is not type(None)]:
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
                detail=(
                    f"Cannot coerce {type(value).__name__} → "
                    f"{target_type.__name__}: {exc}"
                ),
                suggestion=(
                    f"Ensure '{reference}' produces a value compatible "
                    f"with {target_type.__name__}"
                ),
            )
        )
        return value


# ─── Context reference resolver (NEW) ─────────────────────────────────────────


def _resolve_context_reference(
    reference: str,  # full match string e.g. "context.user.name | 'anon'"
    ref_core: str,  # just the path part e.g. "context.user.name"
    context: dict[str, Any],
    input_key: str,
    errors: list[ResolutionError],
    default: Any,
    default_clause: str,
) -> Any:
    """
    Resolve a `context.path.to.value` reference against the workflow context dict.

    The `context` prefix is stripped, and the remainder is navigated as a
    dotted path (with optional array indices and wildcards) through the
    context dict.
    """
    # Determine effective default
    resolved_default: Any = _SENTINEL
    if default_clause.strip():
        resolved_default = _parse_default(default_clause)
    elif default is not _SENTINEL:
        resolved_default = default

    # Strip the leading "context." prefix to get the path
    # ref_core looks like "context.some.path[0]"
    path_after_context = ref_core[len("context.") :]  # "some.path[0]"
    if not path_after_context:
        # bare "context" reference — return the whole context dict
        return context

    segments = _parse_path(path_after_context)
    value = _navigate(
        context,
        segments,
        reference,
        input_key,
        errors,
        error_code_not_found=ResolutionErrorCode.CONTEXT_PATH_NOT_FOUND,
    )

    if value is _SENTINEL:
        return resolved_default if resolved_default is not _SENTINEL else reference

    return value


# ─── Node output reference resolver ──────────────────────────────────────────


def _resolve_node_reference(
    reference: str,
    ref_core: str,
    outputs: dict[str, Any],
    input_key: str,
    errors: list[ResolutionError],
    default: Any,
    default_clause: str,
) -> Any:
    """
    Resolve a `node_name.outputs.path` reference against accumulated node outputs.
    Unchanged from previous version.
    """
    resolved_default: Any = _SENTINEL
    if default_clause.strip():
        resolved_default = _parse_default(default_clause)
    elif default is not _SENTINEL:
        resolved_default = default

    parts = ref_core.split(".", 2)  # ["node", "outputs", "path..."]
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

    segments = _parse_path(parts[2])
    value = _navigate(
        outputs[node_name],
        segments,
        reference,
        input_key,
        errors,
    )

    if value is _SENTINEL:
        return resolved_default if resolved_default is not _SENTINEL else reference

    return value


# ─── Unified single-reference resolver ───────────────────────────────────────


def _resolve_single_reference(
    reference: str,
    outputs: dict[str, Any],
    context: dict[str, Any],
    input_key: str,
    errors: list[ResolutionError],
    default: Any = _SENTINEL,
) -> Any:
    """
    Dispatch to either _resolve_context_reference or _resolve_node_reference
    based on whether the reference starts with `context.`.
    """
    m = REF_PATTERN.match(reference.strip())
    if not m:
        errors.append(
            ResolutionError(
                reference=reference,
                input_key=input_key,
                error_code=ResolutionErrorCode.MALFORMED_REFERENCE,
                detail="Reference does not match expected pattern",
                suggestion=(
                    "Node ref:    node_name.outputs.field[idx]\n"
                    "Context ref: context.key.nested_key"
                ),
            )
        )
        return default if default is not _SENTINEL else reference

    ref_core = m.group("ref")
    default_clause = m.group("default") or ""

    # ── Dispatch on prefix ────────────────────────────────────────────────────
    if ref_core.startswith("context.") or ref_core == "context":
        return _resolve_context_reference(
            reference, ref_core, context, input_key, errors, default, default_clause
        )
    else:
        return _resolve_node_reference(
            reference, ref_core, outputs, input_key, errors, default, default_clause
        )


# ─── Recursive value resolver ─────────────────────────────────────────────────


def _resolve_value(
    value: Any,
    outputs: dict[str, Any],
    context: dict[str, Any],
    input_key: str,
    all_errors: list[ResolutionError],
    type_hints: dict[str, type],
    *,
    _top_level_key: str | None = None,
) -> Any:
    """
    Recursively resolve a single value — string, dict, list, or scalar.

    Dicts and lists are walked in full so nested references (e.g. inside an
    if_node's `values` dict) are resolved correctly.
    """
    lookup_key = _top_level_key or input_key

    # ── dict: recurse into every value ───────────────────────────────────────
    if isinstance(value, dict):
        return {
            k: _resolve_value(
                v, outputs, context, f"{input_key}.{k}", all_errors, type_hints
            )
            for k, v in value.items()
        }

    # ── list: recurse into every element ─────────────────────────────────────
    if isinstance(value, list):
        return [
            _resolve_value(
                item, outputs, context, f"{input_key}[{i}]", all_errors, type_hints
            )
            for i, item in enumerate(value)
        ]

    # ── non-string scalar ─────────────────────────────────────────────────────
    if not isinstance(value, str):
        target_type = type_hints.get(lookup_key)
        return (
            _coerce(value, target_type, "<static>", input_key, all_errors)
            if target_type
            else value
        )

    # ── fast path: no reference present ──────────────────────────────────────
    if not _HAS_REF.search(value):
        return value  # sibling placeholder substitution handled in pass 2

    # ── find all references ───────────────────────────────────────────────────
    ref_matches = list(REF_PATTERN.finditer(value))
    if not ref_matches:
        return value

    target_type = type_hints.get(lookup_key)

    # Template vs pure-reference detection
    stripped = REF_PATTERN.sub("", value).strip()
    is_template = bool(stripped) or ("{" in value and "}" in value)

    if is_template:
        resolved_str = value
        for m in ref_matches:
            full_match = m.group(0)
            resolved_val = _resolve_single_reference(
                full_match, outputs, context, input_key, all_errors
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
        resolved_values = [
            _resolve_single_reference(
                m.group(0), outputs, context, input_key, all_errors
            )
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
    context: dict[str, Any] | None = None,  # ← NEW parameter
    type_hints: dict[str, type] | None = None,
    *,
    strict: bool = False,
    log_level: int = logging.WARNING,
) -> ResolutionResult:
    """
    Resolve all input references based on previous node outputs and/or the
    workflow context dict.

    Reference formats
    ─────────────────
    Node output reference (unchanged):
        node_name.outputs.field
        node_name.outputs.items[0].title
        node_name.outputs.items.*.title
        node_name.outputs.val | "fallback"

    Context reference (NEW):
        context.key
        context.nested.key
        context.items[0]
        context.flags | false

    Template interpolation works for both:
        "Hello {context.user_name}, here is {node.outputs.summary}!"

    Sibling-key placeholders (pass 2):
        topics = "node.outputs.outlines"
        prompt = "Write about {topics}"   ← resolved after pass 1

    Args:
        inputs:     Dict of input key → value (references at any depth).
        outputs:    Dict of node_name → output from previous executions.
        context:    Workflow.context dict (runtime / user-defined variables).
                    Defaults to {} if not provided.
        type_hints: Optional {key: type} for automatic coercion.
        strict:     Raise RuntimeError on any unresolved reference.
        log_level:  Log level for resolution warnings.

    Returns:
        ResolutionResult with .resolved dict and .errors list.
    """
    context = context or {}
    type_hints = type_hints or {}
    all_errors: list[ResolutionError] = []

    # ── Pass 1: resolve all node-output and context references ────────────────
    pass1: dict[str, Any] = {}
    for key, value in inputs.items():
        pass1[key] = _resolve_value(
            value,
            outputs,
            context,
            key,
            all_errors,
            type_hints,
            _top_level_key=key,
        )

    # ── Pass 2: substitute {sibling_key} placeholders in top-level strings ───
    _PLACEHOLDER = re.compile(r"\{([^}]+)\}")

    result_dict: dict[str, Any] = {}
    for key, value in pass1.items():
        if not isinstance(value, str) or "{" not in value:
            result_dict[key] = value
            continue

        def _replace(m: re.Match, _p1: dict = pass1) -> str:
            token = m.group(1).strip()
            if token not in _p1:
                return m.group(0)
            sibling = _p1[token]
            return (
                ", ".join(str(v) for v in sibling)
                if isinstance(sibling, list)
                else str(sibling)
            )

        substituted = _PLACEHOLDER.sub(_replace, value)
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


async def resolve_configs(workflow: Workflow, user_id: str) -> dict:

    resolved_configs = {}
    nodes_map = NODES_MAP

    for node in workflow.nodes:
        node_def = nodes_map.get(node.key)
        if not node_def:
            raise ValueError(f"Node {node.key} not found in NODES_MAP")

        if node_def.service and "google" in node_def.service and node_def.type != "LLM":
            resolver = GoogleNodeConfigResolver()
            config = await resolver.resolve(node.key, user_id)
            resolved_configs[node.key] = config

    return resolved_configs
