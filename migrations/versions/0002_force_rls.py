"""Force row-level security for the application database role."""

from alembic import op

revision = "0002_force_rls"
down_revision = "0001_phase1_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Prevent the table owner from bypassing tenant policies."""
    for table in ("organization", "organization_unit", "person", "organization_membership", "outbox_event", "audit_record", "organization_import"):
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Restore ordinary RLS behavior while retaining policies."""
    for table in ("organization", "organization_unit", "person", "organization_membership", "outbox_event", "audit_record", "organization_import"):
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
