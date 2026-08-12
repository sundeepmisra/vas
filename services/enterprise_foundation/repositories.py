"""Tenant-scoped repositories for authoritative Enterprise Foundation data."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.context import get_context
from packages.persistence.models import Organization, Tenant


class TenantRepository:
    """Repository for platform tenant lifecycle records."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the database session used by this repository."""
        self.session = session

    async def get(self, tenant_id: UUID) -> Tenant | None:
        """Return a tenant only when it matches the trusted request context."""
        context = get_context()
        if context.tenant_id != tenant_id:
            return None
        return await self.session.scalar(select(Tenant).where(Tenant.tenant_id == tenant_id))


class OrganizationRepository:
    """Repository for organizations within the current tenant context."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the database session used by this repository."""
        self.session = session

    async def get(self, organization_id: UUID) -> Organization | None:
        """Return an organization only if it belongs to the current tenant."""
        tenant_id = get_context().tenant_id
        return await self.session.scalar(select(Organization).where(Organization.organization_id == organization_id, Organization.tenant_id == tenant_id))

    async def list(self) -> list[Organization]:
        """List organizations belonging to the current tenant."""
        tenant_id = get_context().tenant_id
        result = await self.session.scalars(select(Organization).where(Organization.tenant_id == tenant_id).order_by(Organization.name))
        return list(result)
