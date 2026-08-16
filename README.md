# Vasilia

Vasilia is a governed Enterprise AI Operating System. Phase 1 establishes the Enterprise Foundation and CSV onboarding vertical slice while preserving contracts for future knowledge, workflow, and enterprise-graph capabilities.

## Development status

This repository contains the Phase 1 foundation implementation in progress. The current executable surface includes the health endpoint, event-contract endpoint, tenant context, SQLAlchemy persistence models, an initial Alembic migration, JWT claim validation utilities, capability contracts, repositories, and CSV parsing/validation logic. Full HTTP authentication middleware, repository integration tests, and the asynchronous import worker remain in progress.

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
| MinIO API | `http://localhost:9000` | S3-compatible object storage |
| MinIO Console | `http://localhost:9001` | Local object-storage administration |

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

Authenticated identity verification is available at:

```text
GET /api/v1/auth/me
Authorization: Bearer <Keycloak access token>
```

The endpoint validates the token signature through the Keycloak realm JWKS endpoint, checks the issuer, extracts the actor and tenant claims, and rejects tokens without tenant context. A valid tenant token returns the normalized subject, tenant ID, role, and scopes.

## Database migrations

With PostgreSQL running, install the project dependencies and run:

```bash
alembic upgrade head
```

The initial migration creates tenant-aware foundation tables, the organization placement field, organization units and closure storage, people and memberships, import tracking, audit records, the transactional outbox, and PostgreSQL RLS policies.

To inspect generated SQL without applying it:

```bash
alembic upgrade head --sql
```

The current RLS policies use the transaction-local PostgreSQL setting `vasilia.tenant_id`. Application transactions must set that value before querying tenant-owned tables.

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

Run all current unit tests:

```bash
python -m pytest tests/unit -q
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
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest tests/unit -q
```

Integration tests require Docker Desktop, the Compose stack, and a migrated database:

```bash
source .venv/bin/activate
docker compose up --build -d
alembic upgrade head
python -m pytest tests/integration -m integration -q
docker compose down
```

The integration suite is being expanded alongside PostgreSQL repositories, RLS policies, Keycloak authentication, MinIO storage, and the outbox publisher. The current `tests/integration/README.md` documents the expected Docker-backed test environment; the suite is not yet complete. A release test run is only considered complete when both unit and integration commands pass.

Run source compilation and linting:

```bash
python -m compileall -q services packages migrations
ruff check .
```

The current unit suite contains 10 tests. The latest verified result is `10 passed`, and Ruff currently reports `All checks passed`.

## Authentication and authorization

Keycloak is the local OIDC provider. The platform expects a validated JWT with at least:

- `sub`: actor identity
- `tenant_id`: tenant scope for tenant users
- `role`: one of `Platform Admin`, `Organization Administrator`, `Department Manager`, or `Employee`
- `scope`: optional space-separated scopes
- `iss`: configured Keycloak issuer

JWT claim mapping utilities are in `services/platform_api/auth.py`, and the verification endpoint is in `services/platform_api/main.py`. Platform-admin flows and tenant-data flows must remain separate; a platform administrator cannot be used as a tenant-data actor. Production deployments validate Keycloak JWKS public keys rather than use development signing secrets.

## Tenant and organization placement

Every request requires trusted tenant context. Each organization has an independent placement profile:

- `SHARED_RLS`: shared PostgreSQL tables protected by RLS
- `DEDICATED_SCHEMA`: organization-specific PostgreSQL schema
- `DEDICATED_DATABASE`: organization-specific database

The tenant catalog remains the control-plane boundary, while an organization placement resolver selects the data route. This permits one tenant to contain multiple organizations while isolating selected organizations when required.

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
