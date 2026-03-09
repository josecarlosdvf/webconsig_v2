"""access control tables

Revision ID: 0006_access_control_tables
Revises: 0005_notifications_table
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_access_control_tables"
down_revision = "0005_notifications_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "casbin_rule",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ptype", sa.String(length=16), nullable=False),
        sa.Column("v0", sa.String(length=255), nullable=True),
        sa.Column("v1", sa.String(length=255), nullable=True),
        sa.Column("v2", sa.String(length=255), nullable=True),
        sa.Column("v3", sa.String(length=255), nullable=True),
        sa.Column("v4", sa.String(length=255), nullable=True),
        sa.Column("v5", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_casbin_rule_ptype", "casbin_rule", ["ptype"])
    op.create_index("ix_casbin_rule_v0", "casbin_rule", ["v0"])
    op.create_index("ix_casbin_rule_v1", "casbin_rule", ["v1"])

    op.create_table(
        "access_resources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resource_key", sa.String(length=200), nullable=False),
        sa.Column("resource_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("path", sa.String(length=240), nullable=True),
        sa.Column("http_method", sa.String(length=16), nullable=True),
        sa.Column("parent_key", sa.String(length=200), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_key", name="uq_access_resources_resource_key"),
    )
    op.create_index("ix_access_resources_resource_key", "access_resources", ["resource_key"])
    op.create_index("ix_access_resources_resource_type", "access_resources", ["resource_type"])


def downgrade() -> None:
    op.drop_index("ix_access_resources_resource_type", table_name="access_resources")
    op.drop_index("ix_access_resources_resource_key", table_name="access_resources")
    op.drop_table("access_resources")

    op.drop_index("ix_casbin_rule_v1", table_name="casbin_rule")
    op.drop_index("ix_casbin_rule_v0", table_name="casbin_rule")
    op.drop_index("ix_casbin_rule_ptype", table_name="casbin_rule")
    op.drop_table("casbin_rule")
