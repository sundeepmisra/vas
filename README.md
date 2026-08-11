# Vasilia

Vasilia is a governed Enterprise AI Operating System. Phase 1 establishes the Enterprise Foundation and CSV onboarding vertical slice while preserving contracts for future knowledge, workflow, and enterprise-graph capabilities.

## Local development

```bash
docker compose up --build
```

The API is exposed at `http://localhost:8000`. OpenAPI is available at `/docs`.

The initial local infrastructure uses PostgreSQL, Redis, Redpanda (Kafka-compatible), and Keycloak. AWS deployment targets are Amazon RDS/Aurora PostgreSQL, ElastiCache, Amazon MSK, and a managed/containerized Keycloak deployment behind the identity port.

## Repository layout

- `services/platform_api`: HTTP entry point and governed capability boundary
- `services/enterprise_foundation`: authoritative organization, department, and employee domain
- `services/import_runtime`: CSV parsing and validation boundary
- `packages/contracts`: event and capability contracts
- `docs/adr`: architecture decision records
- `infra`: local and future deployment configuration

All state-changing operations must pass through a capability and produce an auditable domain event via the transactional outbox.
