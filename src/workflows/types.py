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
    LOOP = "loop"
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
    outputs: Dict[str, Any] = {}  # This will be filled by out application in runtime.

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Edge(BaseModel):
    source: str
    target: str
    type: EdgesTypeEnum
    decision: Union[bool, None] = None
    case: Union[str, None] = None

    @model_validator(mode="after")
    def validate_edge(self):
        node_type = self.type
        if node_type == "if":
            if self.decision is None:
                raise ValueError("Decision must be provided for if edge.")
        elif node_type == "switch":
            if self.case is None:
                raise ValueError("Case must be provided for switch edge.")
        return self

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Pipeline(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ─── Parsed node metadata (produced by parse_pipeline) ────────────────────────

class ParsedNodeData(BaseModel):
    """
    Metadata about a single node derived from the pipeline graph.

    Flag semantics (all mutually exclusive pairs are validated):

      is_control_node      — This node IS an if/switch decision node.
      is_if_branch         — This node is one of the two targets of an IF edge.
      is_switch_branch     — This node is one of the N targets of a SWITCH edge.
      is_loop_back_node    — This node is the SOURCE of a LOOP edge (jumps back).
      is_loop_entry_node   — This node is the TARGET of a LOOP edge (re-entered).
      is_parallel_source   — This node fans out to parallel targets.
      is_merge_target      — This node waits for all its MERGE-edge sources.
    """

    name: str
    dependencies: List[str]  # Node names this node must wait for

    # Control flow role flags
    is_control_node: bool = False  # Owns the if/switch decision
    is_if_branch: bool = False  # Is a branch TARGET of an if edge
    is_switch_branch: bool = False  # Is a branch TARGET of a switch edge
    is_loop_back_node: bool = False  # SOURCE of a loop back-edge
    is_loop_entry_node: bool = False  # TARGET of a loop back-edge (re-entry point)
    is_parallel_source: bool = False  # Fans out to parallel targets
    is_merge_target: bool = False  # Waits for multiple merge-edge sources

    # Which decision/case value activates this node (for branch nodes)
    if_decision: Optional[bool] = None  # True / False for if-branch nodes
    switch_case: Optional[str] = None  # case string for switch-branch nodes

    @model_validator(mode="after")
    def validate_node_data(self) -> "ParsedNodeData":
        if self.is_loop_back_node and self.is_loop_entry_node:
            raise TypeError("A node cannot be both loop_back and loop_entry.")
        if self.is_if_branch and self.is_switch_branch:
            raise TypeError("A node cannot be both an if-branch and a switch-branch.")
        if self.is_control_node and (self.is_if_branch or self.is_switch_branch):
            raise TypeError("A control node cannot also be a branch target.")
        return self

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ─── Execution plan produced by the planner ───────────────────────────────────

class ExecutionStepKind(str, enum.Enum):
    RUN = "run"  # Execute these nodes (possibly in parallel)
    IF = "if"  # Evaluate if_node, then choose a sub-plan
    SWITCH = "switch"  # Evaluate switch_node, then choose a sub-plan
    LOOP = "loop"  # Execute body repeatedly until loop-back stops
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

    # For LOOP steps
    loop_body: Optional["ExecutionPlan"] = None
    loop_entry: Optional[str] = None  # node name that is the loop re-entry point

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExecutionPlan(BaseModel):
    """Ordered List of steps to execute a (sub-)pipeline."""

    steps: List[ExecutionStep] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ─── Workflow input ────────────────────────────────────────────────────────────


class WorkflowInput(BaseModel):
    pipeline_str: str
    configs: Optional[Dict[str, Any]] = None


class WorkflowInput(BaseModel):
    pipeline_str: str
    configs: Dict[str, Any] | None = None
