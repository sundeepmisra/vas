"""Capability execution contracts for governed state-changing operations."""

from dataclasses import dataclass, field
from typing import Protocol, TypeVar
from uuid import UUID, uuid4

InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class CapabilityContext:
    """Attribution and tenant context supplied to a capability."""

    tenant_id: UUID
    actor_id: str
    actor_type: str = "user"
    correlation_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class CapabilityResult[ResultT]:
    """Stable result envelope returned by every capability execution."""

    execution_id: UUID
    capability_name: str
    capability_version: str
    status: str
    result: ResultT | None = None
    domain_errors: tuple[str, ...] = ()


class Capability[InputT, ResultT](Protocol):
    """Protocol implemented by governed business capabilities."""

    name: str
    version: str

    def validate(self, value: InputT) -> tuple[str, ...]:
        """Return domain validation errors without mutating state."""
        ...

    async def execute(self, value: InputT, context: CapabilityContext) -> ResultT:
        """Execute a validated state change inside a transaction."""
        ...


async def execute_capability[InputT, ResultT](capability: Capability[InputT, ResultT], value: InputT, context: CapabilityContext) -> CapabilityResult[ResultT]:
    """Run validation before execution and return a governed result envelope."""
    errors = capability.validate(value)
    execution_id = uuid4()
    if errors:
        return CapabilityResult(execution_id, capability.name, capability.version, "FAILED", domain_errors=errors)
    result = await capability.execute(value, context)
    return CapabilityResult(execution_id, capability.name, capability.version, "SUCCEEDED", result=result)
