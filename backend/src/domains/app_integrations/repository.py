from typing import TypeVar, Any, Dict, TypedDict, Literal
from pydantic import BaseModel
from sqlalchemy import select, update, delete

from src.db.postgres.schemas import UsersIntegrations
from src.domains.app_integrations.schemas import MetadataFiltersOptions
from sqlalchemy.ext.asyncio.session import AsyncSession

ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)


class MetadataFiltersOption(TypedDict):
    criteria: Literal["eq", "lt", "lte", "gt", "gte", "neq"]
    value: str | int | float


class UsersIntegrationsRepository:

    def _parse_metadata_options(self, key: str, options: MetadataFiltersOption):
        if options["criteria"] == "eq":
            return UsersIntegrations.meta[key] == options["value"]
        elif options["criteria"] == "neq":
            return UsersIntegrations.meta[key] != options["value"]
        elif options["criteria"] == "gt":
            return UsersIntegrations.meta[key] > options["value"]
        elif options["criteria"] == "lt":
            return UsersIntegrations.meta[key] < options["value"]
        elif options["criteria"] == "lte":
            return UsersIntegrations.meta[key] <= options["value"]
        elif options["criteria"] == "gte":
            return UsersIntegrations.meta[key] >= options["value"]
        else:
            raise

    async def remove_integrations(
        self, session: AsyncSession, user_id: str, service: str
    ):
        stmt = delete(UsersIntegrations).where(
            UsersIntegrations.user_id == user_id, UsersIntegrations.service == service
        )
        result = await session.execute(stmt)
        return True

    async def update_integration(
        self,
        session: AsyncSession,
        user_id: str,
        service: str,
        update_values: Dict[str, Any],
        metadata_filters: Dict[str, MetadataFiltersOptions] | None = None,
    ) -> UsersIntegrations | None:
        metadata_filters = []
        if metadata_filters is not None:
            metadata_filters = [
                UsersIntegrations.meta[key]
                == self._parse_metadata_options(key, options)
                for key, options in metadata_filters.items()
            ]

        stmt = (
            update(UsersIntegrations)
            .values(update_values)
            .where(
                UsersIntegrations.user_id == user_id,
                UsersIntegrations.service == service,
                *metadata_filters
            )
        ).returning(UsersIntegrations)

        result = await session.execute(stmt)
        updated_integration = result.scalar_one_or_none()
        return updated_integration

    async def create_new_integration(
        self, session: AsyncSession, integration: UsersIntegrations
    ) -> UsersIntegrations:
        session.add(integration)
        integration = await session.commit(integration)
        await session.refresh(integration)
        return integration

    async def find_integration_by_id(
        self,
        session: AsyncSession,
        integration_id: str,
    ) -> UsersIntegrations | None:
        stmt = select(UsersIntegrations).where(UsersIntegrations.id == integration_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
