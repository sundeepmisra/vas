"""CSV parsing primitives for the organization onboarding import pipeline."""

import csv
from io import TextIOBase

REQUIRED_COLUMNS = {"name", "email", "department"}


def read_employee_csv(stream: TextIOBase) -> tuple[list[dict[str, str]], list[str]]:
    """Parse employee rows and return normalized records plus validation errors."""
    reader = csv.DictReader(stream)
    columns = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        return [], [f"missing required columns: {', '.join(missing)}"]
    rows = []
    errors = []
    for line_number, row in enumerate(reader, start=2):
        if not row.get("name") or not row.get("email"):
            errors.append(f"line {line_number}: name and email are required")
            continue
        rows.append({key: (value or "").strip() for key, value in row.items()})
    return rows, errors
