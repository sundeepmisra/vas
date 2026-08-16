"""Unit tests for authentication mapping and capability execution contracts."""

import asyncio
from dataclasses import dataclass
from uuid import uuid4

import jwt
import pytest

from services.platform_api.auth import (
    AuthenticationError,
    Claims,
    decode_claims,
    extract_bearer_token,
    require_tenant_identity,
)
from services.platform_api.capabilities import CapabilityContext, execute_capability


def test_bearer_header_is_required() -> None:
    """Malformed authorization headers fail closed."""
    with pytest.raises(AuthenticationError):
        extract_bearer_token("Basic token")


def test_keycloak_claims_are_mapped() -> None:
    """Validated JWT fields become platform identity claims."""
    secret = "a-development-secret-that-is-at-least-32-bytes-long"
    token = jwt.encode({"sub": "user-1", "tenant_id": "tenant-1", "role": "Employee", "iss": "issuer"}, secret, algorithm="HS256")
    claims = decode_claims(token, key=secret, issuer="issuer")
    assert claims.subject == "user-1"
    assert claims.tenant_id == "tenant-1"


def test_tenant_identity_requires_tenant_claim() -> None:
    """Tenant endpoints reject platform identities without a tenant claim."""
    with pytest.raises(AuthenticationError):
        require_tenant_identity(Claims(subject="admin", tenant_id=None, role="Platform Admin", scopes=()))


@dataclass
class ExampleCapability:
    """Test capability demonstrating validate-before-execute behavior."""

    name: str = "Example"
    version: str = "1.0"

    def validate(self, value: str) -> tuple[str, ...]:
        """Reject empty values before execution."""
        return ("VALUE_REQUIRED",) if not value else ()

    async def execute(self, value: str, context: CapabilityContext) -> str:
        """Return a deterministic test result."""
        return f"{context.tenant_id}:{value}"


def test_capability_validates_before_execution() -> None:
    """Invalid capability input produces no execution result."""
    result = asyncio.run(execute_capability(ExampleCapability(), "", CapabilityContext(uuid4(), "actor")))
    assert result.status == "FAILED"
    assert result.domain_errors == ("VALUE_REQUIRED",)
