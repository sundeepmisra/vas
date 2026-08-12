# Vasilia

Vasilia is a governed Enterprise AI Operating System. Phase 1 establishes the Enterprise Foundation and CSV onboarding vertical slice while preserving contracts for future knowledge, workflow, and enterprise-graph capabilities.

## Development status

This repository contains the Phase 1 foundation scaffold. The current executable surface includes the health endpoint, event-contract example endpoint, tenant-context guard, and CSV parsing/validation logic. Persistence-backed domain APIs, migrations, authentication enforcement, and the full onboarding workflow are the next implementation slice.

## Prerequisites

- Docker Desktop or Docker Engine with the Compose plugin
- Python 3.12 or newer for checks outside Docker
- Git

```bash
docker --version
docker compose version
python3 --version
git --version
```

## Build and run locally

From the repository root:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api
```

Stop services while preserving PostgreSQL data:

```bash
docker compose down
```

To remove the local PostgreSQL volume as well, use this only when local data may be discarded:

```bash
docker compose down -v
```

## Local service endpoints

| Service | Address | Purpose |
| --- | --- | --- |
| Platform API | `http://localhost:8000` | Vasilia HTTP API |
| OpenAPI UI | `http://localhost:8000/docs` | Interactive API documentation |
| PostgreSQL | `localhost:5432` | Transactional database |
| Redpanda Kafka endpoint | `localhost:9092` | Local Kafka-compatible broker |
| Redis | `localhost:6379` | Cache/runtime support |
| Keycloak | `http://localhost:8080` | Local OIDC identity provider |

Local Keycloak administrator credentials are `admin` / `admin`. These are for development only.

## Verify the running API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/contracts/events/example
```

Expected health response:

```json
{"status":"ok"}
```

The event endpoint demonstrates the versioned Kafka-compatible envelope, including tenant, actor, correlation, causation, classification, and payload fields.

## Run checks without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Compile the source:

```bash
python -m compileall -q services packages
```

Run the current smoke verification:

```bash
python - <<'PY'
from io import StringIO
from packages.contracts.events import EventEnvelope
from services.enterprise_foundation.domain import TenantContextError, require_tenant
from services.import_runtime.csv_onboarding import read_employee_csv

rows, errors = read_employee_csv(StringIO("name,email,department\nAda,ada@example.com,Engineering\n"))
assert len(rows) == 1 and not errors
assert EventEnvelope(event_type="test", tenant_id="tenant", actor_id="actor", payload={}).event_version == 1

try:
    require_tenant(None)
except TenantContextError:
    pass
else:
    raise AssertionError("missing tenant context must fail")

print("verification ok")
PY
```

When the test suite is added:

```bash
pytest
```

Linting is configured through Ruff:

```bash
ruff check .
```

## Environment configuration

The Compose file supplies safe local defaults:

| Variable | Local default | Description |
| --- | --- | --- |
| `VASILIA_DATABASE_URL` | `postgresql+asyncpg://vasilia:vasilia@postgres:5432/vasilia` | Async PostgreSQL connection |
| `VASILIA_EVENT_BROKER` | `redpanda:9092` | Kafka-compatible broker address |
| `VASILIA_IDENTITY_ISSUER` | `http://keycloak:8080/realms/vasilia` | OIDC issuer URL |

Do not commit production credentials, tokens, or connection strings. Production secrets should come from AWS Secrets Manager or an equivalent secret manager.

## Architecture notes

Redpanda is used locally instead of a full Kafka installation. It exposes Kafka-compatible protocols while keeping development lightweight; Amazon MSK is the intended AWS production direction.

Keycloak provides the initial Docker-friendly OIDC implementation. Identity should remain behind an adapter so AWS can use managed/containerized Keycloak or Cognito federation without changing domain contracts.

Tenant placement is designed to support shared PostgreSQL with row-level security, a dedicated schema, or a dedicated database per organization. The tenant catalog and routing implementation will select placement during onboarding.

## AWS direction

| Local component | AWS direction |
| --- | --- |
| Dockerized API/services | ECS/Fargate or EKS |
| PostgreSQL | Amazon RDS/Aurora PostgreSQL |
| Redpanda | Amazon MSK or another Kafka-compatible managed service |
| Redis | Amazon ElastiCache for Redis |
| Keycloak | Managed/containerized Keycloak, with Cognito federation evaluated later |
| Object storage | Amazon S3 |
| Secrets | AWS Secrets Manager |

AWS deployment manifests and infrastructure-as-code are intentionally deferred until the Phase 1 domain and contracts stabilize.

## Repository layout

- `services/platform_api`: HTTP entry point and governed capability boundary
- `services/enterprise_foundation`: authoritative organization, department, and employee domain
- `services/import_runtime`: CSV parsing and validation boundary
- `packages/contracts`: event and capability contracts
- `docs/adr`: architecture decision records
- `infra`: local and future deployment configuration

All state-changing operations must pass through a capability and produce an auditable domain event via the transactional outbox.

## Test commands

Unit tests do not require Docker:

```bash
python -m pip install -e '.[dev]'
pytest tests/unit
```

Integration tests require Docker Desktop and the Compose stack:

```bash
docker compose up --build -d
pytest tests/integration -m integration
docker compose down
```

The integration suite is being expanded alongside PostgreSQL repositories, RLS policies, Keycloak authentication, MinIO storage, and the outbox publisher. A test run is only considered complete when both the unit and integration commands pass.

## CSV-based onboarding

CSV onboarding supports two modes:

- `ORGANIZATION_STRUCTURE`: imports organization units, unit types, parent relationships, descriptions, and manager references.
- `PEOPLE_AND_MEMBERSHIP`: imports people, employee types, contact fields, unit assignments, manager references, locations, and presence status.

The intended flow is:

1. Upload the CSV with an idempotency key.
2. Store the source artifact in S3-compatible object storage (MinIO locally, S3 in AWS).
3. Parse headers and sample rows asynchronously.
4. Map columns to Vasilia fields, using AI providers behind the model gateway where enabled.
5. Validate all rows without changing authoritative data.
6. Store row/column issues and present a preview.
7. Apply fixes and revalidate.
8. Convert valid rows into governed capability invocations.
9. Execute dependencies in order, recording per-row success/failure.
10. Write audit records and transactional outbox events in the same database transactions.

Imports are resumable and idempotent: the import execution ID and row number form the capability idempotency key. Partial failures do not discard successful rows.
