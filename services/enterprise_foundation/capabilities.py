"""Enterprise Foundation capability implementations."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.models import CapabilityIdempotency, Organization


@dataclass(frozen=True)
class CreateOrganizationInput:
    """Validated input for creating an organization."""

    name: str
    idempotency_key: str


class CreateOrganizationCapability:
    """Create an organization in ONBOARDING state within the current tenant."""

    name = "CreateOrganization"
    version = "1.0"

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the capability with a transaction-owned session."""
        self.session = session

    def validate(self, value: CreateOrganizationInput) -> tuple[str, ...]:
        """Validate required fields before opening a database transaction."""
        errors = []
        if not value.name.strip():
            errors.append("ORG_NAME_REQUIRED")
        if not value.idempotency_key.strip():
            errors.append("IDEMPOTENCY_KEY_REQUIRED")
        return tuple(errors)

    async def execute(self, value: CreateOrganizationInput, tenant_id) -> Organization:
        """Create an organization using a row lock for numbering."""
        existing = await self.session.scalar(select(CapabilityIdempotency).where(CapabilityIdempotency.tenant_id == tenant_id, CapabilityIdempotency.idempotency_key == value.idempotency_key))
        if existing:
            organization = await self.session.get(Organization, existing.result["organization_id"])
            if organization is None:
                raise RuntimeError("idempotency record references a missing organization")
            return organization
        duplicate = await self.session.scalar(select(Organization).where(Organization.tenant_id == tenant_id, func.lower(Organization.name) == value.name.strip().lower()))
        if duplicate:
            raise ValueError("ORG_NAME_ALREADY_EXISTS")
        count = await self.session.scalar(select(func.count()).select_from(Organization).where(Organization.tenant_id == tenant_id).with_for_update())
        organization = Organization(tenant_id=tenant_id, vasilia_org_number=str(1001 + int(count or 0)), name=value.name.strip(), status="ONBOARDING")
        self.session.add(organization)
        await self.session.flush()
        self.session.add(CapabilityIdempotency(tenant_id=tenant_id, idempotency_key=value.idempotency_key, capability_name=self.name, execution_id=organization.organization_id, result={"organization_id": str(organization.organization_id)}))
        return organization
