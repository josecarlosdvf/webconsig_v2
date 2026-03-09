"""plugin management tables

Revision ID: 0004_plugin_mgmt_tables
Revises: 0003_audit_ctx_fields
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_plugin_mgmt_tables"
down_revision = "0003_audit_ctx_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plugin_modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("module_path", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_plugin_modules_slug"),
    )
    op.create_index("ix_plugin_modules_slug", "plugin_modules", ["slug"])
    op.create_index("ix_plugin_modules_name", "plugin_modules", ["name"])
    op.create_index("ix_plugin_modules_enabled", "plugin_modules", ["enabled"])
    op.create_index("ix_plugin_modules_created_at", "plugin_modules", ["created_at"])

    op.create_table(
        "plugin_task_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plugin_id", sa.Integer(), nullable=False),
        sa.Column("plugin_slug", sa.String(length=80), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=False, server_default="anonymous"),
        sa.Column("task", sa.String(length=80), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_plugin_task_logs_plugin_id", "plugin_task_logs", ["plugin_id"])
    op.create_index("ix_plugin_task_logs_plugin_slug", "plugin_task_logs", ["plugin_slug"])
    op.create_index("ix_plugin_task_logs_actor", "plugin_task_logs", ["actor"])
    op.create_index("ix_plugin_task_logs_task", "plugin_task_logs", ["task"])
    op.create_index("ix_plugin_task_logs_success", "plugin_task_logs", ["success"])
    op.create_index("ix_plugin_task_logs_request_id", "plugin_task_logs", ["request_id"])
    op.create_index("ix_plugin_task_logs_created_at", "plugin_task_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_plugin_task_logs_created_at", table_name="plugin_task_logs")
    op.drop_index("ix_plugin_task_logs_request_id", table_name="plugin_task_logs")
    op.drop_index("ix_plugin_task_logs_success", table_name="plugin_task_logs")
    op.drop_index("ix_plugin_task_logs_task", table_name="plugin_task_logs")
    op.drop_index("ix_plugin_task_logs_actor", table_name="plugin_task_logs")
    op.drop_index("ix_plugin_task_logs_plugin_slug", table_name="plugin_task_logs")
    op.drop_index("ix_plugin_task_logs_plugin_id", table_name="plugin_task_logs")
    op.drop_table("plugin_task_logs")

    op.drop_index("ix_plugin_modules_created_at", table_name="plugin_modules")
    op.drop_index("ix_plugin_modules_enabled", table_name="plugin_modules")
    op.drop_index("ix_plugin_modules_name", table_name="plugin_modules")
    op.drop_index("ix_plugin_modules_slug", table_name="plugin_modules")
    op.drop_table("plugin_modules")
