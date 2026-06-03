from .types import ApplicationNode
from pydantic import BaseModel
from temporalio import activity
import operator
import re
from typing import Any


class IfNodeInput(BaseModel):
    condition: str
    values: dict


class IfNodeOutput(BaseModel):
    decision: bool


class SwitchNodeInput(BaseModel):
    value: str
    cases: list[str]
    default: str = "default"


class SwitchNodeOutput(BaseModel):
    case: str


_CMP_OPS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

_TOKEN_RE = re.compile(
    r"""
    \s*
    (
        \(                              |  # open paren
        \)                              |  # close paren
        >=|<=|==|!=|>|<                |  # comparison — longest match first
        \bnot\s+in\b                   |  # 'not in' — must precede bare 'not'
        \band\b | \bor\b | \bnot\b     |  # logical operators
        \bin\b                          |  # membership
        "(?:[^"\\]|\\.)*"              |  # double-quoted string literal
        '(?:[^'\\]|\\.)*'              |  # single-quoted string literal
        -?\d+(?:\.\d+)?                |  # numeric literal (int or float)
        \b\w+\b                           # identifier, keyword, or bool
    )
    \s*
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _tokenize(expr: str) -> list[str]:
    tokens = [m.group(1) for m in _TOKEN_RE.finditer(expr)]
    if not tokens:
        raise ValueError(f"Empty or unparseable expression: '{expr}'")
    return tokens


# ─── Type coercion ────────────────────────────────────────────────────────────


def _coerce_scalar(value: Any) -> Any:
    """
    Coerce a scalar value to its most natural Python type.

    Handles the common case where upstream nodes (LLMs, sheets, JSON
    deserialisation) produce numeric/boolean values as strings, e.g.
    "42", "3.14", "true", "None".

    Rules (applied in order):
      • Non-string → returned as-is (already typed)
      • "true" / "false" (case-insensitive) → bool
      • "none" / "null" (case-insensitive)  → None
      • Parseable as int                     → int
      • Parseable as float                   → float
      • Otherwise                            → str (unchanged)
    """
    if not isinstance(value, str):
        return value

    lower = value.strip().lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("none", "null"):
        return None

    stripped = value.strip()
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass

    return value


def _coerce_values(values: dict) -> dict:
    """Apply _coerce_scalar to every top-level value in the dict."""
    return {k: _coerce_scalar(v) for k, v in values.items()}


def _align_types(left: Any, right: Any) -> tuple[Any, Any]:
    """
    Attempt to make both operands share a compatible type for comparison.

    This handles the most common mismatch: one side is a str that should
    be numeric (arrived from an LLM output or cell value) while the other
    side is already int/float.

    Rules:
      • If both are already the same type → no change.
      • If one is str and the other is int/float → try to parse the str
        as the numeric type.  If it fails, leave both unchanged (the
        comparison will fail with a clear error).
      • bool is a subclass of int in Python; we deliberately do NOT widen
        bools to int here because "True >= 1" is almost certainly a bug
        in the condition, not intent.
    """
    # Already compatible
    if type(left) is type(right):
        return left, right

    # bool guard — never silently coerce bools to numbers
    if isinstance(left, bool) or isinstance(right, bool):
        return left, right

    # str ↔ numeric
    if isinstance(left, str) and isinstance(right, (int, float)):
        coerced = _coerce_scalar(left)
        if isinstance(coerced, (int, float)):
            return coerced, right

    if isinstance(right, str) and isinstance(left, (int, float)):
        coerced = _coerce_scalar(right)
        if isinstance(coerced, (int, float)):
            return left, coerced

    # str ↔ str (already the same, caught above) — nothing to do
    return left, right


# ─── Operand resolution ───────────────────────────────────────────────────────


def _resolve_operand(raw: str, values: dict) -> Any:
    """
    Resolve a token to a Python value.

    Priority:
      1. Named variable present in `values`  (already coerced by _coerce_values)
      2. Quoted string literal   → str (strips quotes, no further coercion)
      3. Boolean literal         → bool
      4. None literal            → None
      5. Integer literal         → int
      6. Float literal           → float
      7. Bare word               → str (as-is)
    """
    raw = raw.strip()

    if raw in values:
        return values[raw]  # already typed via _coerce_values

    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]  # quoted strings stay as str — intentional

    lower = raw.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("none", "null"):
        return None

    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass

    return raw


# ─── Parser ───────────────────────────────────────────────────────────────────


class _Parser:
    """Recursive-descent boolean expression parser."""

    def __init__(self, tokens: list[str], values: dict):
        self.tokens = tokens
        self.pos = 0
        self.values = values  # pre-coerced by _coerce_values

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, expected: str | None = None) -> str:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if expected is not None and tok.lower() != expected.lower():
            raise ValueError(f"Expected '{expected}', got '{tok}'")
        self.pos += 1
        return tok

    def _match(self, *keywords: str) -> bool:
        tok = self._peek()
        return tok is not None and tok.lower() in {k.lower() for k in keywords}

    # ── Grammar (low → high precedence) ──────────────────────────────────────

    def parse_expr(self) -> bool:
        return self.parse_or()

    def parse_or(self) -> bool:
        left = self.parse_and()
        while self._match("or"):
            self._consume()
            right = self.parse_and()
            left = left or right
        return left

    def parse_and(self) -> bool:
        left = self.parse_not()
        while self._match("and"):
            self._consume()
            right = self.parse_not()
            left = left and right
        return left

    def parse_not(self) -> bool:
        if self._match("not"):
            self._consume()
            return not self.parse_not()
        return self.parse_comparison()

    def parse_comparison(self) -> bool:
        left = self.parse_atom()
        tok = self._peek()

        if tok is None:
            return bool(left)

        # "not in" arrives as a single token
        if tok.lower() == "not in":
            self._consume()
            right = self.parse_atom()
            return self._eval_contains(left, right, negate=True)

        if tok.lower() == "in":
            self._consume()
            right = self.parse_atom()
            return self._eval_contains(left, right, negate=False)

        if tok in _CMP_OPS:
            self._consume()
            right = self.parse_atom()

            # ── Type alignment before comparison ──────────────────────────────
            # Resolve any str/numeric mismatch introduced by upstream nodes
            # returning numbers as strings (e.g. LLM output "5", sheet "3.14").
            aligned_left, aligned_right = _align_types(left, right)

            try:
                return bool(_CMP_OPS[tok](aligned_left, aligned_right))
            except TypeError as exc:
                raise ValueError(
                    f"Cannot compare {type(aligned_left).__name__!r} value "
                    f"{aligned_left!r} '{tok}' {type(aligned_right).__name__!r} "
                    f"value {aligned_right!r}: {exc}\n"
                    f"  Original operands: left={left!r} ({type(left).__name__}), "
                    f"right={right!r} ({type(right).__name__})"
                ) from exc

        # Bare variable used as a truthy check (e.g. "is_active")
        return bool(left)

    def parse_atom(self) -> Any:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression: expected a value")

        if tok == "(":
            self._consume("(")
            val = self.parse_expr()
            self._consume(")")
            return val

        self._consume()
        return _resolve_operand(tok, self.values)

    @staticmethod
    def _eval_contains(left: Any, right: Any, *, negate: bool) -> bool:
        if not hasattr(right, "__contains__"):
            raise ValueError(
                f"'in' requires an iterable on the right side, "
                f"got {type(right).__name__}"
            )
        result = left in right
        return (not result) if negate else result


# ─── Public evaluation entry point ───────────────────────────────────────────


def _evaluate_condition(condition: str, values: dict) -> bool:
    """
    Evaluate a boolean condition string against a dict of named values.

    Values are coerced to their natural Python types before evaluation so
    that comparisons like ``email_count >= 1`` work even when `email_count`
    arrived as the string ``"3"`` from a previous node's output.

    Examples
    --------
    >>> _evaluate_condition("score >= 0.8 and status == 'approved'",
    ...                     {"score": "0.91", "status": "approved"})
    True

    >>> _evaluate_condition("count >= 1",
    ...                     {"count": "5"})
    True

    >>> _evaluate_condition("(role in roles) or override == true",
    ...                     {"role": "guest", "roles": ["admin"], "override": False})
    False
    """
    # Coerce all incoming values so "5" → 5, "true" → True, etc.
    coerced_values = _coerce_values(values)

    tokens = _tokenize(condition)
    parser = _Parser(tokens, coerced_values)
    result = parser.parse_expr()

    if parser.pos != len(parser.tokens):
        remaining = " ".join(parser.tokens[parser.pos :])
        raise ValueError(f"Unexpected token(s) at end of expression: '{remaining}'")

    return result


# ─── Temporal activities ──────────────────────────────────────────────────────


@activity.defn
async def if_node(node_input: IfNodeInput) -> IfNodeOutput:
    decision = _evaluate_condition(node_input.condition, node_input.values)
    return IfNodeOutput(decision=decision)


@activity.defn
async def switch_node(node_input: SwitchNodeInput) -> SwitchNodeOutput:
    target = node_input.value.strip()

    # 1. Exact match
    if target in node_input.cases:
        return SwitchNodeOutput(case=target)

    # 2. Case-insensitive match
    target_lower = target.lower()
    for case in node_input.cases:
        if case.lower() == target_lower:
            return SwitchNodeOutput(case=case)

    # 3. Fallback to default
    return SwitchNodeOutput(case=node_input.default)


# ─── ApplicationNode registrations ───────────────────────────────────────────

IF_NODE = ApplicationNode(
    key="if_node",
    name="if_node",
    fn=if_node,
    service="internal",
    valid_permissions=None,
    description="Conditional branching. Evaluates a condition and returns true or false.",
    type="CONTROL_FLOW",
    node_input_model=IfNodeInput,
    node_output_model=IfNodeOutput,
)

SWITCH_NODE = ApplicationNode(
    key="switch_node",
    name="switch_node",
    fn=switch_node,
    service="internal",
    valid_permissions=None,
    description="Multi-branch routing. Matches a resolved value against a list of cases.",
    type="CONTROL_FLOW",
    node_input_model=SwitchNodeInput,
    node_output_model=SwitchNodeOutput,
)
