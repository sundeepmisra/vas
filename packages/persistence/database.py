"""Async SQLAlchemy engine, session, and PostgreSQL RLS context utilities."""

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def create_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the configured database URL."""
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def set_database_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """Set the transaction-local tenant used by PostgreSQL RLS policies."""
    await session.execute(text("SELECT set_config('vasilia.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})


async def tenant_transaction(session: AsyncSession, tenant_id: UUID) -> AsyncIterator[AsyncSession]:
    """Yield a session with tenant RLS context inside one transaction."""
    async with session.begin():
        await set_database_tenant(session, tenant_id)
        yield session
