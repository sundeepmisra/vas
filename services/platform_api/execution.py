"""Transactional execution service for governed capabilities."""

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.database import set_database_tenant
from packages.persistence.models import AuditRecord, OutboxEvent

from .capabilities import CapabilityContext, CapabilityResult


class CapabilityExecutionService:
    """Coordinates capability validation, domain writes, audit, and outbox persistence."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with one database session per execution."""
        self.session = session

    async def execute(
        self,
        *,
        capability_name: str,
        capability_version: str,
        context: CapabilityContext,
        validate: Callable[[], tuple[str, ...]],
        apply: Callable[[], Awaitable[tuple[dict[str, Any], list[dict[str, Any]]]]],
    ) -> CapabilityResult[dict[str, Any]]:
        """Execute a capability and atomically persist its audit and event records."""
        execution_id = uuid4()
        errors = validate()
        if errors:
            return CapabilityResult(execution_id, capability_name, capability_version, "FAILED", domain_errors=errors)

        try:
            async with self.session.begin():
                await set_database_tenant(self.session, context.tenant_id)
                result, events = await apply()
                self.session.add(AuditRecord(
                    tenant_id=context.tenant_id,
                    actor_id=context.actor_id,
                    actor_type=context.actor_type,
                    capability_name=capability_name,
                    execution_id=execution_id,
                    outcome="SUCCEEDED",
                    details=result,
                ))
                for event in events:
                    self.session.add(OutboxEvent(
                        tenant_id=context.tenant_id,
                        aggregate_type=str(event["aggregate_type"]),
                        aggregate_id=UUID(str(event["aggregate_id"])),
                        event_type=str(event["event_type"]),
                        payload=dict(event["payload"]),
                    ))
            return CapabilityResult(execution_id, capability_name, capability_version, "SUCCEEDED", result=result)
        except Exception:
            await self.session.rollback()
            raise
