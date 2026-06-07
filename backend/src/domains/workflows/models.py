from beanie import Document, PydanticObjectId, Indexed
from typing import Optional, Dict, Annotated, Literal, List, Any
from pydantic import Field
from datetime import datetime, timezone

from src.workflows.types import Node, Edge


class NodesRegistry(Document):
    """List of application nodes for data consistency and single source of truth."""

    name: str
    description: str
    type: Annotated[str, Indexed()]
    service: Annotated[str, Indexed()]
    valid_permissions: list[str] | None = None
    fn_key: Annotated[str, Indexed(unique=True)]
    input_model: Dict[str, Any]
    output_model: Optional[Dict[str, Any]] = None


class Workflows(Document):
    name: str
    description: str
    nodes: List[Node]
    edges: List[Edge]
    visibility: Literal["public", "private"]
    stars: int = Field(default=0)
    created_by: Annotated[PydanticObjectId, Indexed()]


class WorkflowsStars(Document):
    user_id: Annotated[PydanticObjectId, Indexed()]
    workflow_id: Annotated[PydanticObjectId, Indexed()]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowRuns(Document):
    user_id: Annotated[PydanticObjectId, Indexed()]
    workflow_id: Annotated[PydanticObjectId, Indexed()]
    outputs: Optional[Dict[str, Any]] = None 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
