import re
from typing import Tuple, Optional, List, Type, TypeVar
from loguru import logger
from pydantic import BaseModel
from src.workflows.types import ApplicationNode, NodesTypeEnum
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio.session import AsyncSession
from uuid import UUID
from src.db.postgres.schemas import (
    Workflows,
    WorkflowsStars,
    NodesRegistry,
    WorkflowVisibilityEnum,
    Users,
)

ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)


class WorkflowRepository:
    def __init__(self):
        pass

    async def create_workflow(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        name: str,
        description: str,
        nodes: list,
        edges: list,
        visibility,
    ) -> Workflows:

        workflow = Workflows(
            user_id=UUID(user_id),
            name=name,
            description=description,
            nodes=[node.model_dump() for node in nodes],
            edges=[edge.model_dump() for edge in edges],
            visibility=visibility,
            stars=0,
        )

        session.add(workflow)

        await session.commit()
        await session.refresh(workflow)

        return workflow

    async def star_workflow(
        self,
        session: AsyncSession,
        workflow: Workflows,
        user_id: str,
    ) -> Workflows | None:

        user_uuid = UUID(user_id)

        existing_stmt = select(WorkflowsStars).where(
            WorkflowsStars.workflow_id == workflow.id,
            WorkflowsStars.user_id == user_uuid,
        )

        existing = await session.scalar(existing_stmt)

        if existing:
            return None

        session.add(
            WorkflowsStars(
                workflow_id=workflow.id,
                user_id=user_uuid,
            )
        )

        workflow.stars += 1

        await session.commit()
        await session.refresh(workflow)

        return workflow

    async def get_workflow_by_id(
        self, session: AsyncSession, workflow_id: str
    ) -> Workflows | None:
        stmt = select(Workflows).where(Workflows.id == workflow_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_workflows(
        self,
        session: AsyncSession,
        projection_model: Type[ProjectionModelT],
        page: int = 1,
        page_size: int = 10,
        user_id: str | None = None,
        query: str | None = None,
    ) -> tuple[list[ProjectionModelT], int]:
        skip = (page - 1) * page_size
        filters = []

        if user_id is not None:
            filters.append(Workflows.user_id == user_id)
        else:
            filters.append(Workflows.visibility == WorkflowVisibilityEnum.PUBLIC)

        if query:
            filters.append(Workflows.name.ilike(f"%{query}%"))

        # Total count
        count_stmt = select(func.count()).select_from(Workflows).where(*filters)
        total = await session.scalar(count_stmt) or 0

        # Fetch workflows + creator username
        stmt = (
            select(Workflows, Users.username.label("created_by"))
            .join(Users, Users.id == Workflows.user_id)
            .where(*filters)
            .offset(skip)
            .limit(page_size)
        )

        result = await session.execute(stmt)

        workflows = []

        for workflow, created_by in result.all():
            data = {}

            for field in projection_model.model_fields:
                if field == "workflow_id":
                    data["workflow_id"] = str(workflow.id)
                elif field == "created_by":
                    data["created_by"] = created_by
                else:
                    data[field] = getattr(workflow, field)

            workflows.append(projection_model(**data))

        return workflows, total


class NodeRegistryRepository:
    async def delete_all(self, session: AsyncSession):
        stmt = delete(NodesRegistry)
        await session.execute(stmt)
        return None

    async def create_new_node(
        self, session: AsyncSession, node: ApplicationNode
    ) -> NodesRegistry | None:
        new_node = NodesRegistry(
            fn_key=node.key,
            name=node.name,
            description=node.description,
            service=node.service,
            type=node.type,
            valid_permissions=node.valid_permissions,
            input_model=node.node_input_model.model_json_schema(),
            output_model=node.node_output_model.model_json_schema(),
        )

        session.add(new_node)
        await session.commit()
        await session.refresh(new_node)
        return new_node

    async def create_nodes(
        self, session: AsyncSession, nodes: List[ApplicationNode]
    ) -> None:
        nodes_to_register: List[NodesRegistry] = [
            NodesRegistry(
                name=node.name,
                description=node.description,
                type=node.type,
                service=node.service,
                valid_permissions=node.valid_permissions,
                fn_key=node.key,
                input_model=node.node_input_model.model_json_schema(),
                output_model=node.node_output_model.model_json_schema(),
            )
            for node in nodes
        ]
        session.add_all(nodes_to_register)
        await session.commit()
        return None

    async def search_nodes_by_type_and_service(
        self,
        session: AsyncSession,
        node_type: NodesTypeEnum,
        service: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[NodesRegistry], int]:

        skip = (page - 1) * page_size

        filters = [NodesRegistry.type == node_type]

        if service:
            filters.append(NodesRegistry.service.ilike(f"%{service}%"))

        count_stmt = select(func.count()).select_from(NodesRegistry).where(*filters)
        total = await session.scalar(count_stmt) or 0

        stmt = select(NodesRegistry).where(*filters).offset(skip).limit(page_size)

        result = await session.execute(stmt)

        nodes = result.scalars().all()

        return nodes, total

    async def get_all_nodes(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[NodesRegistry], int]:

        skip = (page - 1) * page_size

        count_stmt = select(func.count()).select_from(NodesRegistry)
        total = await session.scalar(count_stmt) or 0

        stmt = select(NodesRegistry).offset(skip).limit(page_size)
        result = await session.execute(stmt)
        nodes = result.scalars().all()
        return nodes, total

    async def get_node(
        self,
        session: AsyncSession,
        fn_key: str,
    ) -> NodesRegistry | None:
        stmt = select(NodesRegistry).where(NodesRegistry.fn_key == fn_key)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
