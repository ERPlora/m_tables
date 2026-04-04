"""Initial tables module schema.

Revision ID: 001
Revises: -
Create Date: 2026-04-04

Creates tables: tables_zone, tables_table, tables_session.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Zone
    op.create_table(
        "tables_zone",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("color", sa.String(20), server_default="primary"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    # Table
    op.create_table(
        "tables_table",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("zone_id", sa.Uuid(), sa.ForeignKey("tables_zone.id", ondelete="SET NULL"), nullable=True),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), server_default=""),
        sa.Column("capacity", sa.Integer(), server_default="4"),
        sa.Column("position_x", sa.Integer(), server_default="0"),
        sa.Column("position_y", sa.Integer(), server_default="0"),
        sa.Column("width", sa.Integer(), server_default="10"),
        sa.Column("height", sa.Integer(), server_default="10"),
        sa.Column("shape", sa.String(20), server_default="square"),
        sa.Column("status", sa.String(20), server_default="available"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )
    op.create_index("ix_tables_hub_status", "tables_table", ["hub_id", "status"])
    op.create_index("ix_tables_hub_active", "tables_table", ["hub_id", "is_active"])

    # TableSession
    op.create_table(
        "tables_session",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("table_id", sa.Uuid(), sa.ForeignKey("tables_table.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guests_count", sa.Integer(), server_default="1"),
        sa.Column("waiter_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("transferred_from_id", sa.Uuid(), sa.ForeignKey("tables_session.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_sessions_hub_status", "tables_session", ["hub_id", "status"])
    op.create_index("ix_sessions_hub_opened", "tables_session", ["hub_id", "opened_at"])


def downgrade() -> None:
    op.drop_table("tables_session")
    op.drop_table("tables_table")
    op.drop_table("tables_zone")
