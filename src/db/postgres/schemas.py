from sqlalchemy.orm import declarative_base, mapped_column, Mapped, relationship
from sqlalchemy import Boolean, ForeignKey, UniqueConstraint, String
import uuid
from datetime import datetime, timezone
import sqlalchemy.dialects.postgresql as pg
from typing import List, Optional

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    email: Mapped[str] = mapped_column(
        pg.VARCHAR(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(pg.VARCHAR(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(pg.VARCHAR(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        pg.TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        pg.TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship attirbutes
    integrations: Mapped[List["AppIntegrationsCredentials"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[List["OAuthAccounts"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AppIntegrationsCredentials(Base):
    __tablename__ = "app_integrations_credentials"
    id: Mapped[uuid.UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        pg.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(pg.TEXT, nullable=False, index=True)

    access_token_enc: Mapped[str] = mapped_column(pg.TEXT, nullable=False)
    refresh_token_enc: Mapped[str | None] = mapped_column(pg.TEXT, nullable=True)

    token_type: Mapped[str] = mapped_column(
        pg.VARCHAR(20), default="Bearer", nullable=False
    )

    scopes: Mapped[list] = mapped_column(pg.ARRAY(String), nullable=False)
    access_token_expiry: Mapped[datetime | None] = mapped_column(
        pg.TIMESTAMP(timezone=True), nullable=True
    )
    refresh_token_expiry: Mapped[datetime | None] = mapped_column(
        pg.TIMESTAMP(timezone=True), nullable=True
    )

    # Relationship attributes
    user: Mapped["User"] = relationship(back_populates="integrations")
    oauth_link: Mapped[Optional["OAuthAccounts"]] = relationship(
        back_populates="integration", uselist=False
    )

    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)


# Where foreign key is used, that is considered a many table
class OAuthAccounts(Base):
    __tablename__ = "oauth_accounts"
    id: Mapped[uuid.UUID] = mapped_column(
        pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        pg.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        pg.UUID(as_uuid=True),
        ForeignKey("app_integrations_credentials.id", ondelete="SET NULL"),
        unique=True,  # This forces 1:1 relationship from db level.
    )
    provider: Mapped[str] = mapped_column(pg.TEXT, nullable=False, index=True)
    provider_sub: Mapped[str] = mapped_column(pg.TEXT, nullable=False)
    provider_email: Mapped[str] = mapped_column(pg.TEXT, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_sub", name="uq_provider_sub"
        ),  # composite unique
    )

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
    integration: Mapped["AppIntegrationsCredentials"] = relationship(
        back_populates="oauth_link"
    )
