"""initial modern stack

Revision ID: 0001_initial_modern_stack
Revises:
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_modern_stack"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("area", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_events_area", "audit_events", ["area"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_idempotency_records_key", "idempotency_records", ["key"])
    op.create_index("ix_idempotency_records_endpoint", "idempotency_records", ["endpoint"])
    op.create_index("ix_idempotency_records_request_hash", "idempotency_records", ["request_hash"])
    op.create_index("ix_idempotency_records_created_at", "idempotency_records", ["created_at"])

    op.create_table(
        "financial_transactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_ref", sa.String(length=64), nullable=False),
        sa.Column("customer_document", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("external_ref", name="uq_financial_transactions_external_ref"),
    )
    op.create_index("ix_financial_transactions_external_ref", "financial_transactions", ["external_ref"])
    op.create_index("ix_financial_transactions_customer_document", "financial_transactions", ["customer_document"])
    op.create_index("ix_financial_transactions_status", "financial_transactions", ["status"])
    op.create_index("ix_financial_transactions_created_at", "financial_transactions", ["created_at"])


def downgrade() -> None:
    op.drop_table("financial_transactions")
    op.drop_table("idempotency_records")
    op.drop_table("audit_events")
