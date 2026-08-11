from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Department:
    tenant_id: str
    name: str
    parent_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class Employee:
    tenant_id: str
    name: str
    email: str
    department_id: UUID | None = None
    manager_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)


class TenantContextError(ValueError):
    pass


def require_tenant(tenant_id: str | None) -> str:
    if not tenant_id or not tenant_id.strip():
        raise TenantContextError("tenant context is required")
    return tenant_id
