from src.db.models import Workflows, WorkflowsStars, Users
from src.schemas.workflow import CreateNewWorkflowModel
from src.repositories.auth_repository import UserRepository
from beanie import PydanticObjectId
from typing import Tuple


class WorkflowRepository:
    def __init__(self):
        pass

    async def get_workflow_by_id(self, workflow_id: str) -> Workflows | None:
        workflow = await Workflows.find_one(Workflows.id == PydanticObjectId(workflow_id))
        return workflow

    async def get_all_workflows(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[list[Workflows], int]:
        """
        Fetch all workflows with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (workflows list, total count)
        """
        skip = (page - 1) * page_size
        workflows = await Workflows.find().skip(skip).limit(page_size).to_list()
        total = await Workflows.find().count()
        return workflows, total

    async def search_workflows_by_name(
        self, query: str, page: int = 1, page_size: int = 10
    ) -> Tuple[list[Workflows], int]:
        """
        Search workflows by name using text search (case-insensitive).
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (workflows list, total count)
        """
        skip = (page - 1) * page_size
        workflows = (
            await Workflows.find(
                Workflows.name.as_regex(query, "i")
            )
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        total = await Workflows.find(
            Workflows.name.as_regex(query, "i")
        ).count()
        return workflows, total
