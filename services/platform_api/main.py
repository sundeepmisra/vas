from fastapi import FastAPI

from packages.contracts.events import EventEnvelope

app = FastAPI(title="Vasilia Platform API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/contracts/events/example", response_model=EventEnvelope)
async def event_contract_example() -> EventEnvelope:
    return EventEnvelope(
        event_type="vasilia.example.v1",
        tenant_id="example-tenant",
        actor_id="example-actor",
        payload={"status": "contract-valid"},
    )
