from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Stable Kafka-compatible envelope; payload schemas evolve independently."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_version: int = 1
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    actor_id: str
    actor_type: str = "user"
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    source: str = "vasilia"
    data_classification: str = "internal"
    payload: dict[str, Any]
