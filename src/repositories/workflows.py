from src.db.models import Workflows, WorkflowsStars, Users
from src.schemas.workflow import CreateNewWorkflowModel
from src.repositories.auth_repository import UserRepository
from beanie import PydanticObjectId


class WorkflowRepository:
    def __init__(self):
        pass

    async def get_workflow_by_id(self, workflow_id: str) -> Workflows | None:
        workflow = await Users.find_one(Workflows.id == PydanticObjectId(workflow_id))
        return workflow
