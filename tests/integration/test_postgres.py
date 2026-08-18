"""PostgreSQL integration tests for migration and tenant RLS behavior."""

from uuid import uuid4

import asyncpg
import pytest

DATABASE_URL = "postgresql://vasilia_app:vasilia-app-development-only@127.0.0.1:55432/vasilia"


@pytest.mark.integration
def test_migration_created_required_tables() -> None:
    """The applied migration exposes the Phase 1 persistence tables."""
    import asyncio

    async def check() -> None:
        """Query PostgreSQL catalog for required tables."""
        connection = await asyncpg.connect(DATABASE_URL)
        try:
            names = await connection.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = {row["tablename"] for row in names}
            assert {"tenant", "organization", "outbox_event", "audit_record", "organization_import"} <= tables
        finally:
            await connection.close()

    asyncio.run(check())


@pytest.mark.integration
def test_rls_hides_another_tenant_organization() -> None:
    """A tenant context cannot read another tenant's organization rows."""
    import asyncio

    async def check() -> None:
        """Insert isolated rows and query them under one tenant context."""
        connection = await asyncpg.connect(DATABASE_URL)
        tenant_a, tenant_b = uuid4(), uuid4()
        try:
            await connection.execute("BEGIN")
            await connection.execute("INSERT INTO tenant(tenant_id, name) VALUES($1, $2), ($3, $4)", tenant_a, "A", tenant_b, "B")
            await connection.execute("SELECT set_config('vasilia.tenant_id', $1, false)", str(tenant_a))
            await connection.execute("INSERT INTO organization(tenant_id, vasilia_org_number, name) VALUES($1, '1001', 'Org A')", tenant_a)
            await connection.execute("SELECT set_config('vasilia.tenant_id', $1, false)", str(tenant_b))
            await connection.execute("INSERT INTO organization(tenant_id, vasilia_org_number, name) VALUES($1, '1001', 'Org B')", tenant_b)
            await connection.execute("SELECT set_config('vasilia.tenant_id', $1, false)", str(tenant_a))
            rows = await connection.fetch("SELECT name FROM organization")
            assert [row["name"] for row in rows] == ["Org A"]
        finally:
            await connection.execute("ROLLBACK")
            await connection.close()

    asyncio.run(check())
