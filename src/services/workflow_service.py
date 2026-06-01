from src.repositories.workflows import WorkflowRepository, UserRepository
from src.schemas.workflow import CreateNewWorkflowModel
from src.db.models import Users, Workflows, WorkflowsStars
from beanie.odm.operators.update.general import Set
from beanie.operators import Inc
from loguru import logger
from beanie.odm.queries.update import UpdateResponse
from pymongo.results import UpdateResult
from beanie import PydanticObjectId
from fastapi import HTTPException, status


class WorkflowService:
    def __init__(self):
        self._user_repo = UserRepository()
        self._workflow_repo = WorkflowRepository()

    async def star_workflow(self, workflow_id: str, user_id: str) -> Workflows | None:
        wf_id_obj = PydanticObjectId(workflow_id)
        user_id_obj = PydanticObjectId(user_id)

        result: UpdateResult = await WorkflowsStars.find_one(
            WorkflowsStars.workflow_id == wf_id_obj,
            WorkflowsStars.user_id == user_id_obj,
        ).update(
            {
                "$setOnInsert": {
                    "workflow_id": wf_id_obj,
                    "user_id": user_id_obj,
                }
            },
            upsert=True,
        )

        if result.upserted_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow already starred by this user",
            )

        updated_workflow = await Workflows.find_one(Workflows.id == wf_id_obj).update(
            Inc({Workflows.stars: 1}), response_type=UpdateResponse.NEW_DOCUMENT
        )

        if not updated_workflow:
            await WorkflowsStars.find_one(
                WorkflowsStars.workflow_id == wf_id_obj,
                WorkflowsStars.user_id == user_id_obj,
            ).delete()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
            )

        return updated_workflow

    async def create_new_workflow(self, workflow: CreateNewWorkflowModel, user_id: str):
        user: Users | None = await self._user_repo.get_user_by_id(user_id=user_id)

        if not user:
            raise Exception("User not found")

        doc: Workflows = Workflows(
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=workflow.edges,
            visibility=workflow.visibility,
            created_by=user.id,
        )
        new_workflow = await Workflows.insert_one(doc)

        return new_workflow
