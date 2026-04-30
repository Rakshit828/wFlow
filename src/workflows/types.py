from pydantic import BaseModel, ConfigDict, model_validator
from typing import Union, Callable, Dict, Any, Type
from bson import ObjectId
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


class ApplicationNode(BaseModel):
    key: str  # The key of the function useful to locate them directly from NODE_MAPS
    name: str  # The unique name of the node/function. App level Id.
    fn: Callable | None = None  # The actual node function refrence
    description: str  # The description of what the node does.
    service: str  # Which service the node is related to. Eg: google.gmail, discord.bot
    valid_permissions: list[str]  # Valid permission to execute the node
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

    @model_validator(mode="before")
    def validate_if_edge(self):
        if self.type == "if":
            if self.decision is None:
                raise ValueError("Decision must be provided for if edge.")
        elif self.type == "switch":
            if self.case is None:
                raise ValueError("Case must be provided for switch edge.")
        return self

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Pipeline(BaseModel):
    nodes: list[Node]
    edges: list[Edge]

    model_config = ConfigDict(arbitrary_types_allowed=True)
