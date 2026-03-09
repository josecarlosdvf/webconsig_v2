"""audit context fields for robust reporting

Revision ID: 0003_audit_ctx_fields
Revises: 0002_idem_unique_endpoint
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_audit_ctx_fields"
down_revision = "0002_idem_unique_endpoint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_events", sa.Column("source", sa.String(length=50), nullable=False, server_default="backend"))
    op.add_column("audit_events", sa.Column("resource", sa.String(length=120), nullable=True))
    op.add_column("audit_events", sa.Column("resource_id", sa.String(length=64), nullable=True))
    op.add_column("audit_events", sa.Column("http_method", sa.String(length=10), nullable=True))
    op.add_column("audit_events", sa.Column("http_path", sa.String(length=255), nullable=True))
    op.add_column("audit_events", sa.Column("status_code", sa.Integer(), nullable=True))
    op.add_column("audit_events", sa.Column("ip_address", sa.String(length=64), nullable=True))
    op.add_column("audit_events", sa.Column("user_agent", sa.String(length=255), nullable=True))
    op.add_column("audit_events", sa.Column("severity", sa.String(length=16), nullable=False, server_default="INFO"))

    op.create_index("ix_audit_events_source", "audit_events", ["source"])
    op.create_index("ix_audit_events_resource", "audit_events", ["resource"])
    op.create_index("ix_audit_events_resource_id", "audit_events", ["resource_id"])
    op.create_index("ix_audit_events_http_path", "audit_events", ["http_path"])
    op.create_index("ix_audit_events_status_code", "audit_events", ["status_code"])
    op.create_index("ix_audit_events_severity", "audit_events", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_severity", table_name="audit_events")
    op.drop_index("ix_audit_events_status_code", table_name="audit_events")
    op.drop_index("ix_audit_events_http_path", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_id", table_name="audit_events")
    op.drop_index("ix_audit_events_resource", table_name="audit_events")
    op.drop_index("ix_audit_events_source", table_name="audit_events")

    op.drop_column("audit_events", "severity")
    op.drop_column("audit_events", "user_agent")
    op.drop_column("audit_events", "ip_address")
    op.drop_column("audit_events", "status_code")
    op.drop_column("audit_events", "http_path")
    op.drop_column("audit_events", "http_method")
    op.drop_column("audit_events", "resource_id")
    op.drop_column("audit_events", "resource")
    op.drop_column("audit_events", "source")
