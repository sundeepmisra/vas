"""Keycloak JWT validation and trusted request-context construction."""

from dataclasses import dataclass
from typing import Any

import jwt


class AuthenticationError(ValueError):
    """Raised when a bearer token is absent or invalid."""


@dataclass(frozen=True)
class Claims:
    """Validated identity claims required by Vasilia authorization."""

    subject: str
    tenant_id: str | None
    role: str
    scopes: tuple[str, ...]


def extract_bearer_token(authorization: str | None) -> str:
    """Extract a bearer token from an HTTP Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("bearer token required")
    return authorization[7:].strip()


def decode_claims(token: str, *, key: str, issuer: str, audience: str | None = None) -> Claims:
    """Validate a JWT signature and map Keycloak claims to platform claims."""
    options = {"verify_aud": audience is not None}
    payload: dict[str, Any] = jwt.decode(token, key, algorithms=["RS256", "HS256"], issuer=issuer, audience=audience, options=options)
    subject = payload.get("sub")
    if not subject:
        raise AuthenticationError("token subject is required")
    scopes = tuple(str(payload.get("scope", "")).split())
    role = str(payload.get("role") or payload.get("realm_access", {}).get("roles", ["Employee"])[0])
    return Claims(subject=subject, tenant_id=payload.get("tenant_id"), role=role, scopes=scopes)
