"""
Tables module models — SQLAlchemy 2.0.

Models: Zone, Table, TableSession.
Restaurant floor plan management with zones, tables, and guest sessions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import HubBaseModel

if TYPE_CHECKING:
    pass


# ============================================================================
# Choices
# ============================================================================

SHAPE_CHOICES = ("square", "round", "rectangle")

TABLE_STATUS_CHOICES = ("available", "occupied", "reserved", "blocked")

TABLE_STATUS_LABELS = {
    "available": "Available",
    "occupied": "Occupied",
    "reserved": "Reserved",
    "blocked": "Blocked",
}

TABLE_STATUS_COLORS = {
    "available": "success",
    "occupied": "warning",
    "reserved": "primary",
    "blocked": "error",
}

SHAPE_LABELS = {
    "square": "Square",
    "round": "Round",
    "rectangle": "Rectangle",
}

SESSION_STATUS_CHOICES = ("active", "closed", "transferred")

SESSION_STATUS_LABELS = {
    "active": "Active",
    "closed": "Closed",
    "transferred": "Transferred",
}

SESSION_STATUS_COLORS = {
    "active": "warning",
    "closed": "medium",
    "transferred": "primary",
}


# ============================================================================
# Zone
# ============================================================================

class Zone(HubBaseModel):
    """Zone represents an area (e.g., Main Hall, Terrace, VIP)."""

    __tablename__ = "tables_zone"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    color: Mapped[str] = mapped_column(
        String(20), default="primary", server_default="primary",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )

    # Relationships
    tables: Mapped[list[Table]] = relationship(
        "Table", back_populates="zone", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Zone {self.name!r}>"

    @property
    def available_tables_count(self) -> int:
        """Count of available, active, non-deleted tables in this zone."""
        return sum(
            1 for t in self.tables
            if not t.is_deleted and t.is_active and t.status == "available"
        )


# ============================================================================
# Table
# ============================================================================

class Table(HubBaseModel):
    """Physical table in the restaurant."""

    __tablename__ = "tables_table"
    __table_args__ = (
        Index("ix_tables_hub_status", "hub_id", "status"),
        Index("ix_tables_hub_active", "hub_id", "is_active"),
    )

    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tables_zone.id", ondelete="SET NULL"), nullable=True,
    )
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="", server_default="")
    capacity: Mapped[int] = mapped_column(
        Integer, default=4, server_default="4",
    )

    # Floor plan position
    position_x: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )
    position_y: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )
    width: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10",
    )
    height: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10",
    )
    shape: Mapped[str] = mapped_column(
        String(20), default="square", server_default="square",
    )

    status: Mapped[str] = mapped_column(
        String(20), default="available", server_default="available",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    # Relationships
    zone: Mapped[Zone | None] = relationship(
        "Zone", back_populates="tables",
    )
    sessions: Mapped[list[TableSession]] = relationship(
        "TableSession", back_populates="table", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Table {self.number!r}>"

    @property
    def display_name(self) -> str:
        if self.name:
            return f"{self.number} - {self.name}"
        return f"Table {self.number}"

    @property
    def status_label(self) -> str:
        return TABLE_STATUS_LABELS.get(self.status, self.status)

    @property
    def status_color(self) -> str:
        return TABLE_STATUS_COLORS.get(self.status, "neutral")

    @property
    def shape_label(self) -> str:
        return SHAPE_LABELS.get(self.shape, self.shape)

    def set_status(self, status: str) -> None:
        """Set table status if valid."""
        if status in TABLE_STATUS_CHOICES:
            self.status = status


# ============================================================================
# TableSession
# ============================================================================

class TableSession(HubBaseModel):
    """Customer session at a table."""

    __tablename__ = "tables_session"
    __table_args__ = (
        Index("ix_sessions_hub_status", "hub_id", "status"),
        Index("ix_sessions_hub_opened", "hub_id", "opened_at"),
    )

    table_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tables_table.id", ondelete="CASCADE"), nullable=False,
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default="now()",
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    guests_count: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1",
    )
    waiter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active",
    )
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    transferred_from_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tables_session.id", ondelete="SET NULL"), nullable=True,
    )

    # Relationships
    table: Mapped[Table] = relationship(
        "Table", back_populates="sessions",
    )
    transferred_to: Mapped[list[TableSession]] = relationship(
        "TableSession",
        back_populates="transferred_from",
        foreign_keys="[TableSession.transferred_from_id]",
    )
    transferred_from: Mapped[TableSession | None] = relationship(
        "TableSession",
        back_populates="transferred_to",
        remote_side="TableSession.id",
        foreign_keys="[TableSession.transferred_from_id]",
    )

    def __repr__(self) -> str:
        return f"<TableSession table={self.table_id} opened={self.opened_at}>"

    @property
    def duration(self) -> Any:
        """Return timedelta of session duration."""
        end_time = self.closed_at or datetime.now(UTC)
        return end_time - self.opened_at

    @property
    def duration_minutes(self) -> int:
        return int(self.duration.total_seconds() / 60)

    @property
    def status_label(self) -> str:
        return SESSION_STATUS_LABELS.get(self.status, self.status)

    @property
    def status_color(self) -> str:
        return SESSION_STATUS_COLORS.get(self.status, "neutral")

    def close(self) -> None:
        """Close this session and free the table."""
        self.status = "closed"
        self.closed_at = datetime.now(UTC)
        self.table.set_status("available")

    def transfer_to(
        self,
        new_table: Table,
        hub_id: uuid.UUID,
        waiter_id: uuid.UUID | None = None,
    ) -> TableSession:
        """Transfer session to a new table, returning the new session."""
        self.status = "transferred"
        self.closed_at = datetime.now(UTC)
        self.table.set_status("available")

        new_session = TableSession(
            hub_id=hub_id,
            table_id=new_table.id,
            guests_count=self.guests_count,
            waiter_id=waiter_id or self.waiter_id,
            notes=self.notes,
            transferred_from_id=self.id,
        )
        new_table.set_status("occupied")
        return new_session
