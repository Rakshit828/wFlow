from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, UniqueConstraint, ForeignKey, Index
import sqlalchemy.dialects.postgresql as pg
from uuid import uuid4, UUID
from typing import Dict, List
from enum import Enum

from .main import Base
from src.workflows.types import Node, Edge


class LoginProvidersEnum(str, Enum):
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"


class CredentialsTypeEnum(str, Enum):
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"


class WorkflowVisibilityEnum(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class Users(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(pg.TEXT, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(pg.BOOLEAN, default=False)
    password_hash: Mapped[str | None]
    full_name: Mapped[str | None]
    avatar_url: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(pg.BOOLEAN, default=True)
    is_superuser: Mapped[bool] = mapped_column(pg.BOOLEAN, default=False)

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class OAuthAccounts(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    provider: Mapped[LoginProvidersEnum] = mapped_column(
        pg.ENUM(LoginProvidersEnum, name="login_providers_enum")
    )
    provider_sub_id: Mapped[str] = mapped_column(pg.TEXT)
    provider_email: Mapped[str] = mapped_column(pg.TEXT)

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    __table_args__ = (UniqueConstraint("provider", "provider_sub_id"),)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(pg.TEXT, unique=True, index=True)
    user_agent: Mapped[str | None]
    ip_address: Mapped[str | None]
    expires_at: Mapped[datetime]

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class UsersIntegrations(Base):
    __tablename__ = "users_integrations"

    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    service: Mapped[str] = mapped_column(pg.TEXT, index=True)

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IntegrationsCredentials(Base):
    __tablename__ = "integrations_credentials"
    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    integration_id: Mapped[UUID] = mapped_column(
        ForeignKey("users_integrations.id", ondelete="CASCADE"), index=True
    )
    credentials_type: Mapped[CredentialsTypeEnum] = mapped_column(
        pg.ENUM(CredentialsTypeEnum, name="credentials_type_enum")
    )
    credentials: Mapped[str] = mapped_column(pg.TEXT)
    meta: Mapped[Dict[str, str]] = mapped_column(pg.JSONB)

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Workflows(Base):
    __tablename__ = "workflows"
    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(pg.TEXT, index=True)
    description: Mapped[str] = mapped_column(pg.TEXT)
    nodes: Mapped[List[Node]] = mapped_column(pg.JSONB)
    edges: Mapped[List[Edge]] = mapped_column(pg.JSONB)

    visibility: Mapped[WorkflowVisibilityEnum] = mapped_column(
        pg.ENUM(WorkflowVisibilityEnum, name="workflow_visibility_enum")
    )
    stars: Mapped[int] = mapped_column(pg.NUMERIC)


class WorkflowsStars(Base):
    __tablename__ = "workflows_stars"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), primary_key=True
    )

    # Defined as composite key: (user_id, workflow_id)
    # This CompositePrimaryKey will handle two things.
    # 1. It optimizes the serching with (user_id, workflow_id)
    # 2. It optimizes the searching with only user_id because of leftmost rule of composite
    #    indexes. However, we cannot efficiently search with only workflow_id.
    #    If we have a usecase for searching with workflow_id, we can apply single index on that column.
