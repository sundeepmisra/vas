# Integration tests

Integration tests run against the Docker Compose services and will cover PostgreSQL, RLS, Keycloak JWT validation, MinIO, outbox publication, and API flows as those components are implemented.

Run the stack first:

```bash
docker compose up --build -d
pytest tests/integration -m integration
```
