"""Unit tests for atomic capability execution orchestration."""

import asyncio
from uuid import uuid4

from services.platform_api.capabilities import CapabilityContext
from services.platform_api.execution import CapabilityExecutionService


class FakeSession:
    """Minimal session double used to verify execution ordering."""

    def __init__(self) -> None:
        """Initialize an empty operation log."""
        self.operations: list[str] = []

    def begin(self):
        """Return this session as an async transaction context."""
        return self

    async def __aenter__(self):
        """Record transaction entry."""
        self.operations.append("begin")
        return self

    async def __aexit__(self, _type, _value, _traceback):
        """Record transaction exit without suppressing errors."""
        self.operations.append("commit" if _type is None else "rollback")
        return False

    def add(self, value):
        """Record an object scheduled for persistence."""
        self.operations.append(type(value).__name__)

    async def execute(self, _statement, _parameters):
        """Record the RLS context statement."""
        self.operations.append("rls")

    async def rollback(self):
        """Record an explicit rollback request."""
        self.operations.append("rollback")


def test_execution_writes_audit_and_outbox_after_apply() -> None:
    """Successful domain work is followed by audit and event persistence."""
    session = FakeSession()
    tenant_id = uuid4()

    async def apply():
        """Return a result and one domain event."""
        session.operations.append("apply")
        return {"created": True}, [{"aggregate_type": "Organization", "aggregate_id": uuid4(), "event_type": "OrganizationCreated", "payload": {}}]

    result = asyncio.run(CapabilityExecutionService(session).execute(
        capability_name="CreateOrganization",
        capability_version="1.0",
        context=CapabilityContext(tenant_id, "actor"),
        validate=lambda: (),
        apply=apply,
    ))
    assert result.status == "SUCCEEDED"
    assert session.operations[0:3] == ["begin", "rls", "apply"]
    assert "AuditRecord" in session.operations
    assert "OutboxEvent" in session.operations
    assert session.operations[-1] == "commit"

