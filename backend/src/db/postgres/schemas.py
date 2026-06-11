from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, UniqueConstraint, ForeignKey, Index
import sqlalchemy.dialects.postgresql as pg
from uuid import uuid4, UUID
from typing import Dict, List, Any, Tuple
from enum import Enum

from .main import Base
from ...types.db_types import (
    WorkflowExecutionStatusEnum,
    WorkflowVisibilityEnum,
    CredentialsTypeEnum,
    LoginProvidersEnum,
)
from src.workflows.types import Node, Edge, NodesTypeEnum


class Users(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(pg.TEXT, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(pg.BOOLEAN, default=False)
    username: Mapped[str] = mapped_column(pg.TEXT, unique=True)

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
    expires_at: Mapped[datetime] = mapped_column(pg.TIMESTAMP(timezone=True))

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
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    service: Mapped[str] = mapped_column(pg.TEXT)

    scopes: Mapped[List[str]] = mapped_column(
        pg.ARRAY(item_type=pg.TEXT), nullable=True
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

    __table_args__ = (Index("idx_user_id_and_service", "user_id", "service"),)

    # The service: str will be in the form of google.gmail, google.drive or simply discord
    def get_provider_and_service(self) -> Tuple[str, str]:
        return self.service.split(".")


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
    nodes: Mapped[List[Node]] = mapped_column(pg.ARRAY(pg.JSONB))
    edges: Mapped[List[Edge]] = mapped_column(pg.ARRAY(pg.JSONB))

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


class WorkflowExecutions(Base):
    __tablename__ = "workflow_executions"
    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[WorkflowExecutionStatusEnum] = mapped_column(
        pg.ENUM(WorkflowExecutionStatusEnum, name="wf_execution_status_enum"),
        nullable=False,
    )


class NodesRegistry(Base):
    __tablename__ = "nodes_registry"
    fn_key: Mapped[str] = mapped_column(pg.TEXT, nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(pg.TEXT, nullable=False)
    description: Mapped[str] = mapped_column(pg.TEXT, nullable=False)
    type: Mapped[NodesTypeEnum] = mapped_column(
        pg.ENUM(NodesTypeEnum, name="nodes_type_enum"), index=True
    )
    service: Mapped[str] = mapped_column(pg.TEXT, nullable=False, index=True)
    valid_permissions: Mapped[list[str] | None] = mapped_column(
        pg.ARRAY(pg.TEXT), nullable=True
    )
    input_model: Mapped[Dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)
    output_model: Mapped[Dict[str, Any]] = mapped_column(pg.JSONB, nullable=False)
