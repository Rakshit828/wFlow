from pydantic import BaseModel, ConfigDict, model_validator
from typing import Union, Callable, Dict, Any, Type, Optional, List
import enum


class NodesTypeEnum(str, enum.Enum):
    ACTION = "ACTION"  # Denotes the action we do on behalf of users.
    LLM = "LLM"  # Denotes external LLM to be called.
    TRANSFORM = "TRANSFORM"  # For data transformations
    API = "API"  # For calling external APIs
    DATA_SOURCE = "DATA_SOURCE"  # This like databases, VDB,
    CONTROL_FLOW = "CONTROL_FLOW"  # This is for nodes like if and switch
    TRIGGER = "TRIGGER"  # External Triggers that will invoke the workflow


class EdgesTypeEnum(str, enum.Enum):
    LINEAR = "linear"
    IF = "if"
    SWITCH = "switch"
    PARALLEL = "parallel"
    MERGE = "merge"


class ApplicationNode(BaseModel):
    key: str  # The key of the function useful to locate them directly from NODE_MAPS
    name: str  # The unique name of the node/function. App level Id.
    fn: Callable[[Type[BaseModel]], Type[BaseModel]] | None = (
        None  # The actual node function refrence
    )
    description: str  # The description of what the node does.
    service: str | None = (
        None  # Which service the node is related to. Eg: google.gmail, discord.bot
    )
    valid_permissions: List[str] | None = None  # Valid permission to execute the node
    type: NodesTypeEnum  # The type of the node.
    node_input_model: Type[BaseModel] | None = (
        None  # The pydantic input model of the node
    )
    node_output_model: Type[BaseModel] | None = (
        None  # The pydantic output model of the node.
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Node(BaseModel):
    key: str
    name: str
    type: NodesTypeEnum
    inputs: Dict[str, Any] = {}
    config: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Edge(BaseModel):
    source: str
    target: str
    type: EdgesTypeEnum
    decision: Optional[bool] = None
    case: Optional[str] = None

    @model_validator(mode="after")
    def validate_edge(self):
        if self.type == EdgesTypeEnum.IF and self.decision is None:
            raise ValueError("IF edge requires 'decision'.")
        if self.type == EdgesTypeEnum.SWITCH and self.case is None:
            raise ValueError("SWITCH edge requires 'case'.")
        return self


class Workflow(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    context: Dict[str, Any] = {}  # Holds the runtime or user created variables

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ParsedNodeData(BaseModel):
    """
    Metadata about a single node derived from the workflow graph.

    Flag semantics (all mutually exclusive pairs are validated):

      is_control_node      — This node IS an if/switch decision node.
      is_if_branch         — This node is one of the two targets of an IF edge.
      is_switch_branch     — This node is one of the N targets of a SWITCH edge.
      is_parallel_source   — This node fans out to parallel targets.
      is_merge_target      — This node waits for all its MERGE-edge sources.
    """

    name: str
    dependencies: List[str]  # Node names this node must wait for

    # Control flow role flags
    is_control_node: bool = False  # Owns the if/switch decision
    is_if_branch: bool = False  # Is a branch TARGET of an if edge
    is_switch_branch: bool = False  # Is a branch TARGET of a switch edge
    is_parallel_source: bool = False  # Fans out to parallel targets
    is_merge_target: bool = False  # Waits for multiple merge-edge sources

    # Which decision/case value activates this node (for branch nodes)
    if_decision: Optional[bool] = None  # True / False for if-branch nodes
    switch_case: Optional[str] = None  # case string for switch-branch nodes

    @model_validator(mode="after")
    def validate_node_data(self) -> "ParsedNodeData":
        if self.is_if_branch and self.is_switch_branch:
            raise TypeError("A node cannot be both an if-branch and a switch-branch.")
        if self.is_control_node and (self.is_if_branch or self.is_switch_branch):
            raise TypeError("A control node cannot also be a branch target.")
        return self

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutionStepKind(str, enum.Enum):
    RUN = "run"  # Execute these nodes (possibly in parallel)
    IF = "if"  # Evaluate if_node, then choose a sub-plan
    SWITCH = "switch"  # Evaluate switch_node, then choose a sub-plan
    MERGE = "merge"  # Wait for all parallel branches to complete


class ExecutionStep(BaseModel):
    """One step in an ExecutionPlan."""

    kind: ExecutionStepKind
    nodes: List[str] = []  # Node name(s) to run (for RUN / MERGE steps)

    # For IF steps
    true_plan: Optional["ExecutionPlan"] = None
    false_plan: Optional["ExecutionPlan"] = None

    # For SWITCH steps
    case_plans: Optional[Dict[str, "ExecutionPlan"]] = None
    default_case: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutionPlan(BaseModel):
    """Ordered List of steps to execute a (sub-)workflow."""

    steps: List[ExecutionStep] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ─── Workflow input ────────────────────────────────────────────────────────────
class WorkflowInput(BaseModel):
    workflow: Workflow
    configs: Optional[Dict[str, Any]] = None  # For workflows which are not simple
