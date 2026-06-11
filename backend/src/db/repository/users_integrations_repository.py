from typing import Any, Dict, Tuple
from sqlalchemy import update, delete, select

from src.db.postgres.schemas import UsersIntegrations
from src.types.db_types import CredentialsTypeEnum
from src.domains.user_integrations.types import MetadataFiltersOptions
from sqlalchemy.ext.asyncio.session import AsyncSession


class UsersIntegrationsRepository:

    def _parse_metadata_options(self, key: str, options: MetadataFiltersOptions):
        if options["criteria"] == "eq":
            return UsersIntegrations.meta[key].as_string() == options["value"]
        elif options["criteria"] == "neq":
            return UsersIntegrations.meta[key].as_string() != options["value"]
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
        meta_filters = []
        if metadata_filters is not None:
            meta_filters = [
                self._parse_metadata_options(key, options)
                for key, options in metadata_filters.items()
            ]

        stmt = (
            update(UsersIntegrations)
            .values(update_values)
            .where(
                UsersIntegrations.user_id == user_id,
                UsersIntegrations.service == service,
                *meta_filters
            )
        ).returning(UsersIntegrations)

        result = await session.execute(stmt)
        updated_integration = result.scalar_one_or_none()
        return updated_integration

    async def create_new_integration(
        self, session: AsyncSession, integration: UsersIntegrations
    ) -> UsersIntegrations:
        session.add(integration)
        await session.commit()
        await session.refresh(integration)
        return integration

    async def load_encrypted_credentials(
        self,
        session: AsyncSession,
        user_id: str,
        service: str,
        metadata_filters: Dict[str, MetadataFiltersOptions],
    ) -> Tuple[CredentialsTypeEnum, str]:
        """Returns the pair of CredentialsType and Encrypted Credentials as string."""
        metadata_filters = []
        if metadata_filters is not None:
            metadata_filters = [
                UsersIntegrations.meta[key]
                == self._parse_metadata_options(key, options)
                for key, options in metadata_filters.items()
            ]

        stmt = select(
            UsersIntegrations.credentials_type, UsersIntegrations.credentials
        ).where(
            UsersIntegrations.user_id == user_id,
            UsersIntegrations.service == service,
            *metadata_filters
        )
        result = (await session.execute(stmt)).all()

        if len(result) != 1:
            raise

        row = result[0]

        return row[0], row[1]
