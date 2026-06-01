from pydantic import BaseModel
from typing import List, Optional, Literal
from src.workflows.types import Node, Edge


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


class StarWorkflowResponseModel(BaseModel):
    workflow_id: str
    stars: int
