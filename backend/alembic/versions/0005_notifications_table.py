"""notifications table

Revision ID: 0005_notifications_table
Revises: 0004_plugin_mgmt_tables
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_notifications_table"
down_revision = "0004_plugin_mgmt_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sender", sa.String(length=100), nullable=False),
        sa.Column("recipient", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_notifications_sender", "notifications", ["sender"])
    op.create_index("ix_notifications_recipient", "notifications", ["recipient"])
    op.create_index("ix_notifications_category", "notifications", ["category"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_read_at", "notifications", ["read_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_read_at", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_category", table_name="notifications")
    op.drop_index("ix_notifications_recipient", table_name="notifications")
    op.drop_index("ix_notifications_sender", table_name="notifications")
    op.drop_table("notifications")
