"""Alembic environment for Vasilia PostgreSQL migrations."""
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config

from packages.persistence import models  # noqa: F401
from packages.persistence.base import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Render migration SQL without opening a database connection."""
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations against the configured PostgreSQL database."""
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.")
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection) -> None:
    """Configure Alembic on a synchronous connection supplied by SQLAlchemy."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
