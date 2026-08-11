# Phase 1 Foundation ADR Index

Status: Accepted for initial implementation

1. Capability-driven architecture: all state changes use governed capabilities.
2. Agent/domain separation: agents plan; domain services authorize business integrity and execute commands.
3. Modular-first Python services: clear bounded-context contracts precede deployment separation.
4. Event integration: meaningful domain changes emit versioned events.
5. Transactional outbox: domain write and outbox record commit atomically.
6. Enterprise graph: future graph is a non-authoritative projection.
7. AI gateway: providers are replaceable behind one internal contract.
8. Capability registry/gateway: capabilities are discoverable, attributable, and policy-checked.
9. Durable workflows: long-running coordination will use a workflow runtime, not agent memory.
10. Tenant placement: a control-plane catalog selects shared RLS, dedicated schema, or dedicated database per tenant.
11. Identity: Keycloak/OIDC is the initial Docker identity provider; identity remains behind an adapter for AWS deployment.
12. Transactional platform: PostgreSQL is authoritative for Phase 1.
13. Strategic runtime: Docker Compose locally; AWS container/Kubernetes deployment remains compatible.
14. Observability: OpenTelemetry-compatible traces, metrics, and logs are required at service boundaries.
15. External capability exposure: future MCP/API adapters cannot redefine capability semantics.
16. Provenance: imported and retrieved data retain source and classification metadata.
17. Risk autonomy: policy determines approval and autonomy level.
18. Search/vector: projections are never authoritative facts.
19. Event envelope: events carry tenant, actor, correlation, causation, version, and classification metadata.
20. Phase 1 topology: API, foundation, import runtime, outbox, and broker contracts are modular and may initially share a deployable image.

## Deferred decisions

- AWS identity target: managed Keycloak versus Cognito federation.
- Workflow runtime selection.
- Search/vector implementation.
- Production Kafka choice: Amazon MSK versus another managed Kafka-compatible service.
