"""Unit tests for CreateOrganization validation rules."""

from services.enterprise_foundation.capabilities import (
    CreateOrganizationCapability,
    CreateOrganizationInput,
)


def test_create_organization_rejects_missing_name() -> None:
    """Blank organization names are rejected before database work."""
    capability = CreateOrganizationCapability(None)  # type: ignore[arg-type]
    assert capability.validate(CreateOrganizationInput(" ", "key")) == ("ORG_NAME_REQUIRED",)


def test_create_organization_rejects_missing_idempotency_key() -> None:
    """Missing idempotency keys are rejected before database work."""
    capability = CreateOrganizationCapability(None)  # type: ignore[arg-type]
    assert capability.validate(CreateOrganizationInput("Acme", "")) == ("IDEMPOTENCY_KEY_REQUIRED",)
