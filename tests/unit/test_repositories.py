"""Repository unit tests for fail-closed tenant scoping."""

import asyncio
from uuid import uuid4

from packages.persistence.context import RequestContext, set_context
from services.enterprise_foundation.repositories import TenantRepository


def test_tenant_repository_rejects_other_tenant_without_query() -> None:
    """A repository refuses a tenant ID different from trusted request context."""
    class UnexpectedSession:
        """Test session that fails if a query is attempted."""

        async def scalar(self, _query):
            """Fail because the repository should return before querying."""
            raise AssertionError("cross-tenant query attempted")

    current = uuid4()
    set_context(RequestContext(current, "actor", "Organization Administrator"))
    result = asyncio.run(TenantRepository(UnexpectedSession()).get(uuid4()))
    assert result is None
