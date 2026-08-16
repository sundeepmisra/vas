"""Create the initial tenant-aware Vasilia persistence schema."""

from alembic import op

revision = "0001_phase1_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create authoritative tables, outbox, audit, imports, and RLS policies."""
    op.execute("""
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE TABLE tenant (tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PROVISIONING', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
    CREATE TABLE organization (organization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), vasilia_org_number TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ONBOARDING', placement TEXT NOT NULL DEFAULT 'SHARED_RLS' CHECK (placement IN ('SHARED_RLS','DEDICATED_SCHEMA','DEDICATED_DATABASE')), created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), version INTEGER NOT NULL DEFAULT 1, UNIQUE(tenant_id, vasilia_org_number), UNIQUE(tenant_id, name));
    CREATE TABLE capability_idempotency (tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), idempotency_key TEXT NOT NULL, capability_name TEXT NOT NULL, execution_id UUID NOT NULL, result JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id, idempotency_key));
    CREATE TABLE organization_unit (unit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), organization_id UUID NOT NULL REFERENCES organization(organization_id), vasilia_unit_number TEXT NOT NULL, parent_unit_id UUID REFERENCES organization_unit(unit_id), unit_type TEXT NOT NULL, name TEXT NOT NULL, description TEXT, status TEXT NOT NULL DEFAULT 'ACTIVE', version INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(organization_id, vasilia_unit_number));
    CREATE TABLE organization_unit_closure (ancestor_id UUID NOT NULL REFERENCES organization_unit(unit_id), descendant_id UUID NOT NULL REFERENCES organization_unit(unit_id), depth INTEGER NOT NULL CHECK(depth >= 0), PRIMARY KEY(ancestor_id, descendant_id));
    CREATE TABLE person (person_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), organization_id UUID NOT NULL REFERENCES organization(organization_id), vasilia_person_number TEXT NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL, display_name TEXT, employee_type TEXT NOT NULL, phone TEXT, mobile TEXT, presence_status TEXT NOT NULL DEFAULT 'IN_OFFICE', status TEXT NOT NULL DEFAULT 'ACTIVE', version INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(organization_id, vasilia_person_number));
    CREATE TABLE organization_membership (membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), person_id UUID NOT NULL REFERENCES person(person_id), organization_unit_id UUID NOT NULL REFERENCES organization_unit(unit_id), is_primary BOOLEAN NOT NULL DEFAULT TRUE, effective_from DATE NOT NULL, effective_to DATE, status TEXT NOT NULL DEFAULT 'ACTIVE', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
    CREATE UNIQUE INDEX one_active_primary_membership ON organization_membership(person_id) WHERE is_primary AND effective_to IS NULL;
    CREATE TABLE outbox_event (event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), aggregate_type TEXT NOT NULL, aggregate_id UUID NOT NULL, event_type TEXT NOT NULL, payload JSONB NOT NULL, published BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), published_at TIMESTAMPTZ);
    CREATE INDEX outbox_unpublished_idx ON outbox_event(published, created_at);
    CREATE TABLE audit_record (audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), actor_id TEXT NOT NULL, actor_type TEXT NOT NULL, capability_name TEXT NOT NULL, execution_id UUID NOT NULL, outcome TEXT NOT NULL, details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
    CREATE TABLE organization_import (import_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL REFERENCES tenant(tenant_id), organization_id UUID NOT NULL REFERENCES organization(organization_id), import_mode TEXT NOT NULL, import_execution_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'PENDING', file_name TEXT, object_key TEXT, row_count INTEGER, applied_count INTEGER NOT NULL DEFAULT 0, failed_count INTEGER NOT NULL DEFAULT 0, column_mapping JSONB, ai_mapping_confidence JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
    CREATE TABLE organization_import_issue (issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), import_id UUID NOT NULL REFERENCES organization_import(import_id), row_number INTEGER, column_name TEXT, issue_type TEXT NOT NULL, severity TEXT NOT NULL, message TEXT NOT NULL, raw_value TEXT, suggested_fix TEXT, resolution_status TEXT NOT NULL DEFAULT 'OPEN');
    ALTER TABLE organization ENABLE ROW LEVEL SECURITY;
    ALTER TABLE organization_unit ENABLE ROW LEVEL SECURITY;
    ALTER TABLE person ENABLE ROW LEVEL SECURITY;
    ALTER TABLE organization_membership ENABLE ROW LEVEL SECURITY;
    ALTER TABLE outbox_event ENABLE ROW LEVEL SECURITY;
    ALTER TABLE audit_record ENABLE ROW LEVEL SECURITY;
    ALTER TABLE organization_import ENABLE ROW LEVEL SECURITY;
    CREATE POLICY organization_tenant_isolation ON organization USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    CREATE POLICY unit_tenant_isolation ON organization_unit USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    CREATE POLICY person_tenant_isolation ON person USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    CREATE POLICY membership_tenant_isolation ON organization_membership USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    CREATE POLICY outbox_tenant_isolation ON outbox_event USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    CREATE POLICY audit_tenant_isolation ON audit_record USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    CREATE POLICY import_tenant_isolation ON organization_import USING (tenant_id = NULLIF(current_setting('vasilia.tenant_id', true), '')::uuid);
    """)


def downgrade() -> None:
    """Drop the initial schema in dependency-safe order."""
    op.execute("DROP TABLE IF EXISTS organization_import_issue, organization_import, audit_record, outbox_event, organization_membership, person, organization_unit_closure, organization_unit, capability_idempotency, organization, tenant CASCADE")
