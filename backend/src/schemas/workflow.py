from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from typing import List, Optional, Literal, Dict, Any
from src.workflows.types import Node, Edge, NodesTypeEnum


class CreateNewWorkflowModel(BaseModel):
    name: str
    description: str
    nodes: List[Node]
    edges: List[Edge]
    visibility: Literal["public", "private"]


class WorkflowResponseModel(BaseModel):
    workflow_id: str
    name: str
    description: str
    nodes: List[Node]
    edges: List[Edge]
    visibility: Literal["public", "private"]
    stars: Optional[int] = None
    created_by: str


class NodeFullResponse(Node):
    input_model: Dict[str, Any] = {}  # Json schema
    output_model: Dict[str, Any] = {}  # json schema

class SingleWorkflowResponseModel(BaseModel):
    workflow_id: str
    name: str
    description: str
    nodes: List[NodeFullResponse]
    edges: List[Edge]
    visibility: Literal["public", "private"]
    stars: Optional[int] = None
    created_by: str


class StarWorkflowResponseModel(BaseModel):
    workflow_id: str
    stars: int


class WorkflowListItemModel(BaseModel):
    workflow_id: str
    name: str
    description: str
    visibility: Literal["public", "private"]
    stars: int
    created_by: str

    @field_validator("workflow_id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v



class NodesRegistryListItemModel(BaseModel):
    name: str
    description: str
    type: NodesTypeEnum
    service: str
    valid_permissions: list[str] | None = None
    fn_key: str
    input_model: dict  # THis is the json schema
    output_model: dict | None = (
        None  # This is also the json schema, None if output is determined at runtime
    )


class PaginationMetadata(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedWorkflowsResponse(BaseModel):
    data: List[WorkflowListItemModel]
    pagination: PaginationMetadata


class PaginatedNodesResponse(BaseModel):
    data: List[NodesRegistryListItemModel]
    pagination: PaginationMetadata
