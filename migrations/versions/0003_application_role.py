"""Create the non-superuser role used by application connections and RLS."""

from alembic import op

revision = "0003_application_role"
down_revision = "0002_force_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the runtime role and grant least-privilege table access."""
    op.execute("DO $$ BEGIN CREATE ROLE vasilia_app LOGIN PASSWORD 'vasilia-app-development-only'; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("GRANT CONNECT ON DATABASE vasilia TO vasilia_app")
    op.execute("GRANT USAGE ON SCHEMA public TO vasilia_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vasilia_app")


def downgrade() -> None:
    """Remove the runtime role after revoking its database privileges."""
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM vasilia_app")
    op.execute("DROP ROLE IF EXISTS vasilia_app")
