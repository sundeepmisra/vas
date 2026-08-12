from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    tenant_id: UUID
    actor_id: str
    role: str
    organization_id: UUID | None = None


_current: ContextVar[RequestContext | None] = ContextVar("vasilia_request_context", default=None)


def set_context(context: RequestContext) -> None:
    _current.set(context)


def get_context() -> RequestContext:
    context = _current.get()
    if context is None:
        raise RuntimeError("tenant and actor request context are required")
    return context
