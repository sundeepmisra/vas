"""Request-scoped identity, tenant, and organization context utilities."""

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    """Trusted context extracted from validated identity and routing data."""

    tenant_id: UUID
    actor_id: str
    role: str
    organization_id: UUID | None = None


_current: ContextVar[RequestContext | None] = ContextVar("vasilia_request_context", default=None)


def set_context(context: RequestContext) -> None:
    """Set the context for the current asynchronous execution flow."""
    _current.set(context)


def get_context() -> RequestContext:
    """Return the current context or fail closed when it is absent."""
    context = _current.get()
    if context is None:
        raise RuntimeError("tenant and actor request context are required")
    return context
