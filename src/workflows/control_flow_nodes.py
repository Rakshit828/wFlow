from .types import ApplicationNode
from pydantic import BaseModel
from temporalio import activity
import operator
import re


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
    ">":  operator.gt,
    "<":  operator.lt,
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
 
 
def _resolve_operand(raw: str, values: dict):
    """
    Resolve a token to a Python value.
 
    Priority:
      1. Named variable present in `values`
      2. Quoted string literal   → str (strips quotes)
      3. Boolean literal         → bool
      4. None literal            → None
      5. Integer literal         → int
      6. Float literal           → float
      7. Bare word               → str (as-is)
    """
    raw = raw.strip()
 
    if raw in values:
        return values[raw]
 
    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
 
    lower = raw.lower()
    if lower == "true":  return True
    if lower == "false": return False
    if lower == "none":  return None
 
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
 
    return raw
 
 
class _Parser:
    """Recursive descent parser. One instance per evaluate call."""
 
    def __init__(self, tokens: list[str], values: dict):
        self.tokens = tokens
        self.pos    = 0
        self.values = values
 
    # ── Internal helpers ──────────────────────────────────────────────────────
 
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
 
    # ── Grammar rules (top → bottom = low → high precedence) ─────────────────
 
    def parse_expr(self) -> bool:
        return self.parse_or()
 
    def parse_or(self) -> bool:
        left = self.parse_and()
        while self._match("or"):
            self._consume()
            right = self.parse_and()
            left  = left or right
        return left
 
    def parse_and(self) -> bool:
        left = self.parse_not()
        while self._match("and"):
            self._consume()
            right = self.parse_not()
            left  = left and right
        return left
 
    def parse_not(self) -> bool:
        if self._match("not"):
            self._consume()
            return not self.parse_not()   # right-associative; handles `not not x`
        return self.parse_comparison()
 
    def parse_comparison(self) -> bool:
        left = self.parse_atom()
        tok  = self._peek()
 
        if tok is None:
            return bool(left)
 
        # "not in" arrives as a single token from the tokenizer
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
            try:
                return bool(_CMP_OPS[tok](left, right))
            except TypeError as exc:
                raise ValueError(
                    f"Cannot compare {type(left).__name__} '{tok}' "
                    f"{type(right).__name__}: {exc}"
                ) from exc
 
        # Bare variable used as a truthy check (e.g. "is_active")
        return bool(left)
 
    def parse_atom(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression: expected a value")
 
        if tok == "(":
            self._consume("(")
            val = self.parse_expr()       # recurse — full precedence inside parens
            self._consume(")")
            return val
 
        self._consume()
        return _resolve_operand(tok, self.values)
 
    # ── Helper ────────────────────────────────────────────────────────────────
 
    @staticmethod
    def _eval_contains(left, right, *, negate: bool) -> bool:
        if not hasattr(right, "__contains__"):
            raise ValueError(
                f"'in' requires an iterable on the right side, "
                f"got {type(right).__name__}"
            )
        result = left in right
        return (not result) if negate else result
 
 
def _evaluate_condition(condition: str, values: dict) -> bool:
    """
    Evaluate a boolean condition string against a dict of named values.
 
    Examples
    --------
    >>> _evaluate_condition("score >= 0.8 and status == 'approved'",
    ...                     {"score": 0.91, "status": "approved"})
    True
 
    >>> _evaluate_condition("(role in roles) or override == true",
    ...                     {"role": "guest", "roles": ["admin"], "override": False})
    False
    """
    tokens = _tokenize(condition)
    parser = _Parser(tokens, values)
    result = parser.parse_expr()
 
    if parser.pos != len(parser.tokens):
        remaining = " ".join(parser.tokens[parser.pos:])
        raise ValueError(
            f"Unexpected token(s) at end of expression: '{remaining}'"
        )
 
    return result
 
 
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


IF_NODE = ApplicationNode(
    key="if_node",
    name="if_node",
    fn=if_node,
    service=None,
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
    service=None,
    valid_permissions=None,
    description="Multi-branch routing. Matches a resolved value against a list of cases.",
    type="CONTROL_FLOW",
    node_input_model=SwitchNodeInput,
    node_output_model=SwitchNodeOutput,
)
