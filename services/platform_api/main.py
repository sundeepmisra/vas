from fastapi import FastAPI, Header, HTTPException, status

from packages.contracts.events import EventEnvelope

from .auth import AuthenticationError, Claims, require_identity, require_tenant_identity

app = FastAPI(title="Vasilia Platform API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/auth/me", response_model=Claims)
async def current_identity(authorization: str | None = Header(default=None)) -> Claims:
    """Return validated identity claims for local authentication verification."""
    try:
        return require_tenant_identity(require_identity(authorization))
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/contracts/events/example", response_model=EventEnvelope)
async def event_contract_example() -> EventEnvelope:
    return EventEnvelope(
        event_type="vasilia.example.v1",
        tenant_id="example-tenant",
        actor_id="example-actor",
        payload={"status": "contract-valid"},
    )
