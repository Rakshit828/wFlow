from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.db.postgres.schemas import Users, Session, OAuthAccounts


class SessionRepository:
    async def get_user_by_token(
        self, session: AsyncSession, token_hash: str
    ) -> Users | None:
        stmt = (
            select(Users)
            .join(Session, Session.user_id == Users.id)
            .where(
                Session.token_hash == token_hash,
                Session.expires_at > datetime.now(UTC),
                Users.is_active.is_(True),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_session(
        self,
        session: AsyncSession,
        new_session: Session,
    ) -> Users:
        session.add(new_session)
        await session.commit()
        return new_session


class UserRepository:
    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: str | UUID,
    ) -> Users | None:
        stmt = select(Users).where(Users.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> Users | None:
        stmt = select(Users).where(Users.email == email.lower())
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self, 
        session: AsyncSession,
        user: Users,
    ) -> Users:
        session.add(user)
        await session.commit()
        return user


class OAuthAccountRepository:
    async def create_oauthaccount(
        self,
        session: AsyncSession,
        oauth_acc: OAuthAccounts,
    ) -> Users:
        session.add(oauth_acc)
        await session.commit()
        return oauth_acc
