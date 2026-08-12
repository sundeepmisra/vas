"""Unit tests for foundation contracts and CSV validation."""

from io import StringIO

import pytest

from packages.contracts.events import EventEnvelope
from packages.persistence.context import RequestContext, get_context, set_context
from services.enterprise_foundation.domain import TenantContextError, require_tenant
from services.import_runtime.csv_onboarding import read_employee_csv


def test_csv_parser_normalizes_valid_rows() -> None:
    """Valid employee rows are returned with trimmed values."""
    rows, errors = read_employee_csv(StringIO("name,email,department\n Ada ,ada@example.com,Engineering\n"))
    assert errors == []
    assert rows == [{"name": "Ada", "email": "ada@example.com", "department": "Engineering"}]


def test_csv_parser_reports_missing_columns() -> None:
    """Missing required headers prevent any import rows from being accepted."""
    rows, errors = read_employee_csv(StringIO("name,email\nAda,ada@example.com\n"))
    assert rows == []
    assert "missing required columns: department" in errors[0]


def test_tenant_context_fails_closed() -> None:
    """Missing tenant identity raises before domain work can proceed."""
    with pytest.raises(TenantContextError):
        require_tenant(None)


def test_request_context_is_available() -> None:
    """A trusted request context can be retrieved in the current execution flow."""
    context = RequestContext(tenant_id=__import__("uuid").uuid4(), actor_id="actor", role="Employee")
    set_context(context)
    assert get_context() == context


def test_event_envelope_has_version_and_actor() -> None:
    """Events carry stable versioning and attribution metadata."""
    event = EventEnvelope(event_type="PersonCreated", tenant_id="tenant", actor_id="actor", payload={})
    assert event.event_version == 1
    assert event.actor_type == "user"
