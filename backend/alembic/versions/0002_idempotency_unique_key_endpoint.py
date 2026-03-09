"""idempotency unique key per endpoint

Revision ID: 0002_idem_unique_endpoint
Revises: 0001_initial_modern_stack
Create Date: 2026-03-09
"""

from alembic import op


revision = "0002_idem_unique_endpoint"
down_revision = "0001_initial_modern_stack"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_idempotency_key_endpoint",
        "idempotency_records",
        ["key", "endpoint"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_idempotency_key_endpoint", "idempotency_records", type_="unique")
