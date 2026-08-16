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


def decode_keycloak_jwt(token: str, *, issuer: str, audience: str | None = None) -> Claims:
    """Validate a Keycloak token using the issuer's published JWKS keys."""
    jwks_client = jwt.PyJWKClient(f"{issuer.rstrip('/')}/protocol/openid-connect/certs")
    signing_key = jwks_client.get_signing_key_from_jwt(token).key
    return decode_claims(token, key=signing_key, issuer=issuer, audience=audience)


def require_identity(authorization: str | None, issuer: str = "http://keycloak:8080/realms/vasilia") -> Claims:
    """Convert a bearer header into trusted claims for an API adapter."""
    try:
        token = extract_bearer_token(authorization)
        return decode_keycloak_jwt(token, issuer=issuer)
    except (AuthenticationError, jwt.PyJWTError) as exc:
        raise AuthenticationError("invalid authentication credentials") from exc


def require_tenant_identity(claims: Claims) -> Claims:
    """Reject platform-only identities from tenant data operations."""
    if not claims.tenant_id:
        raise AuthenticationError("tenant context is required")
    return claims
