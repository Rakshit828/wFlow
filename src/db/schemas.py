from beanie import Indexed, Link, Document, PydanticObjectId
from pydantic import EmailStr, Field, BaseModel
from datetime import datetime
from enum import Enum

class Users(Document):
    email: Indexed(EmailStr, unique=True) # type: ignore
    password: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime


class NodeTypeEnum(str, Enum):
    GENERAL = "general"
    LLM = "llm"
    INTEGRATION = "integration"
    DATA = "data"

class Nodes(Document):
    name: str
    description: str
    node_type: NodeTypeEnum
    


class EdgeTypeEnum(str, Enum):
    LINEAR = "linear"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"

class Edge(BaseModel):
    node1: PydanticObjectId
    node2: PydanticObjectId
    edge_type: EdgeTypeEnum

class Pipelines(Document):
    nodes: Link[Nodes]
    edges: list[Edge]

    created_by: Link[Users]
    starred_by: Link[Users]



