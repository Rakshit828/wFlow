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
    valid_permissions: list[str] | None = None  # Valid permission to execute the node
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
    nodes: list[Node]
    edges: list[Edge]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NodeDependency(BaseModel):
    data: Dict[str, list[str]]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowInput(BaseModel):
    pipeline_str: str
    configs: Dict[str, Any] | None = None


PIPENINE_EXAMPLE = Pipeline(
    **{
        "nodes": [
            {
                "key": "llm.groq",
                "name": "groq_llm_node1",
                "type": "LLM",
                "inputs": {"prompt": "Generate me 9 outlines for essay on Nepal"},
                "config": {"response_model": {"output": {"outlines": "list.str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node2",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a description on topics {topics}",
                    "topics": "groq_llm_node1.outputs.output.outlines[0] groq_llm_node1.outputs.output.outlines[1] groq_llm_node1.outputs.output.outlines[2]",
                },
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node3",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a description on topics {topics}",
                    "topics": "groq_llm_node1.outputs.output.outlines[3] groq_llm_node1.outputs.output.outlines[4] groq_llm_node1.outputs.output.outlines[5]",
                },
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node4",
                "type": "LLM",
                "inputs": {
                    "prompt": "Generate me a description on topics {topics}",
                    "topics": "groq_llm_node1.outputs.output.outlines[6] groq_llm_node1.outputs.output.outlines[7] groq_llm_node1.outputs.output.outlines[8]",
                },
                "config": {"response_model": {"output": {"article": "str"}}},
                "outputs": {},
            },
            {
                "key": "llm.groq",
                "name": "groq_llm_node5",
                "type": "LLM",
                "inputs": {
                    "prompt": "Merge these different articles to produce a single best article. Articles are : {articles}",
                    "articles": "groq_llm_node2.outputs.output.article groq_llm_node3.outputs.output.article groq_llm_node4.outputs.output.article",
                },
                "config": {"response_model": {"output": {"final_article": "str"}}},
                "outputs": {},
            },
        ],
        "edges": [
            {"source": "start", "target": "groq_llm_node1", "type": "linear"},
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node2",
                "type": "parallel",
            },
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node3",
                "type": "parallel",
            },
            {
                "source": "groq_llm_node1",
                "target": "groq_llm_node4",
                "type": "parallel",
            },
            {"source": "groq_llm_node2", "target": "groq_llm_node5", "type": "linear"},
            {"source": "groq_llm_node3", "target": "groq_llm_node5", "type": "linear"},
            {"source": "groq_llm_node4", "target": "groq_llm_node5", "type": "linear"},
            {"source": "groq_llm_node5", "target": "end", "type": "linear"},

        ],
    }
)
