"""Tables module service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import selectinload

from runtime.orm.transactions import atomic
from runtime.apps.service_facade import ModuleService, action

from .models import Table, TableSession, Zone


class TableService(ModuleService):
    """Restaurant floor plan, table, and session management."""

    # ==================================================================
    # ZONES
    # ==================================================================

    @action(permission="view_zone")
    async def list_zones(self, *, is_active: bool | None = None):
        """List table zones/areas."""
        query = self.q(Zone).options(selectinload(Zone.tables))
        if is_active is not None:
            query = query.filter(Zone.is_active == is_active)
        zones = await query.order_by(Zone.sort_order, Zone.name).all()
        return {
            "zones": [
                {
                    "id": str(z.id),
                    "name": z.name,
                    "color": z.color,
                    "is_active": z.is_active,
                    "table_count": sum(1 for t in z.tables if not t.is_deleted),
                    "available_tables": z.available_tables_count,
                }
                for z in zones
            ],
        }

    @action(permission="add_zone", mutates=True)
    async def create_zone(
        self,
        *,
        name: str,
        description: str = "",
        color: str = "primary",
        sort_order: int = 0,
    ):
        """Create a new table zone/area."""
        async with atomic(self.db) as session:
            z = Zone(
                hub_id=self.hub_id,
                name=name,
                description=description,
                color=color,
                sort_order=sort_order,
            )
            session.add(z)
            await session.flush()
        return {"id": str(z.id), "name": z.name, "created": True}

    # ==================================================================
    # TABLES
    # ==================================================================

    @action(permission="view_table")
    async def list_tables(
        self,
        *,
        zone_id: str = "",
        status: str = "",
        is_active: bool | None = None,
    ):
        """List tables with optional filters."""
        query = self.q(Table).options(selectinload(Table.zone))
        if zone_id:
            query = query.filter(Table.zone_id == uuid.UUID(zone_id))
        if status:
            query = query.filter(Table.status == status)
        if is_active is not None:
            query = query.filter(Table.is_active == is_active)

        total = await query.count()
        tables = await query.order_by(Table.number).all()
        return {
            "tables": [
                {
                    "id": str(t.id),
                    "number": t.number,
                    "name": t.name,
                    "capacity": t.capacity,
                    "shape": t.shape,
                    "status": t.status,
                    "is_active": t.is_active,
                    "zone": t.zone.name if t.zone else None,
                    "zone_id": str(t.zone_id) if t.zone_id else None,
                }
                for t in tables
            ],
            "total": total,
        }

    @action(permission="add_table", mutates=True)
    async def create_table(
        self,
        *,
        number: str,
        name: str = "",
        capacity: int = 4,
        zone_id: str = "",
        shape: str = "square",
        position_x: int = 0,
        position_y: int = 0,
    ):
        """Create a new table."""
        async with atomic(self.db) as session:
            t = Table(
                hub_id=self.hub_id,
                number=number,
                name=name,
                capacity=capacity,
                zone_id=uuid.UUID(zone_id) if zone_id else None,
                shape=shape,
                position_x=position_x,
                position_y=position_y,
            )
            session.add(t)
            await session.flush()
        return {"id": str(t.id), "number": t.number, "capacity": t.capacity, "created": True}

    @action(permission="change_table", mutates=True)
    async def update_table(
        self,
        *,
        table_id: str,
        number: str | None = None,
        name: str | None = None,
        capacity: int | None = None,
        zone_id: str | None = None,
        shape: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
    ):
        """Update a table's properties."""
        t = await self.q(Table).get(uuid.UUID(table_id))
        if t is None:
            return {"error": "Table not found"}

        if capacity is not None and capacity <= 0:
            return {"error": "Capacity must be greater than 0"}

        if is_active is not None and is_active is False and t.status != "available":
            return {
                "error": "Cannot deactivate table with active session. "
                "Close or transfer the session first.",
            }

        for field_name, value in [
            ("number", number), ("name", name), ("capacity", capacity),
            ("shape", shape), ("status", status), ("is_active", is_active),
        ]:
            if value is not None:
                setattr(t, field_name, value)
        if zone_id is not None:
            t.zone_id = uuid.UUID(zone_id) if zone_id else None
        await self.db.flush()
        return {"id": str(t.id), "number": t.number, "updated": True}

    @action(permission="add_table", mutates=True)
    async def bulk_create_tables(
        self,
        *,
        count: int,
        start_number: int = 1,
        prefix: str = "",
        capacity: int = 4,
        zone_id: str = "",
        shape: str = "square",
    ):
        """Create multiple tables at once."""
        created = []
        async with atomic(self.db) as session:
            for i in range(count):
                num = start_number + i
                t = Table(
                    hub_id=self.hub_id,
                    number=f"{prefix}{num}",
                    capacity=capacity,
                    zone_id=uuid.UUID(zone_id) if zone_id else None,
                    shape=shape,
                    position_x=(i % 5) * 20,
                    position_y=(i // 5) * 20,
                )
                session.add(t)
                await session.flush()
                created.append({"id": str(t.id), "number": t.number})

        return {"created": created, "total": len(created)}

    # ==================================================================
    # TABLE SESSIONS
    # ==================================================================

    @action(permission="add_tablesession", mutates=True)
    async def open_session(
        self,
        *,
        table_id: str,
        guests_count: int,
        waiter_id: str = "",
        notes: str = "",
    ):
        """Open a table session (seat guests)."""
        table = await self.q(Table).get(uuid.UUID(table_id))
        if table is None:
            return {"error": "Table not found"}
        if table.status != "available":
            return {"error": "Table is not available"}

        capacity_warning = None
        if guests_count > table.capacity:
            capacity_warning = (
                f"Guest count ({guests_count}) exceeds table capacity ({table.capacity}). "
                f"Proceeding anyway."
            )

        async with atomic(self.db) as session:
            ts = TableSession(
                hub_id=self.hub_id,
                table_id=table.id,
                guests_count=guests_count,
                waiter_id=uuid.UUID(waiter_id) if waiter_id else None,
                notes=notes,
            )
            session.add(ts)
            await session.flush()
            table.set_status("occupied")

        result = {
            "session_id": str(ts.id),
            "table_number": table.number,
            "guests": ts.guests_count,
            "opened": True,
        }
        if capacity_warning:
            result["warning"] = capacity_warning
        return result

    @action(permission="view_tablesession")
    async def list_sessions(
        self,
        *,
        status: str = "",
        zone_id: str = "",
        limit: int = 20,
    ):
        """List table sessions (active or historical)."""
        query = self.q(TableSession).options(
            selectinload(TableSession.table).selectinload(Table.zone),
        )
        if status:
            query = query.filter(TableSession.status == status)
        if zone_id:
            query = query.filter(
                TableSession.table.has(Table.zone_id == uuid.UUID(zone_id)),
            )
        sessions = await query.order_by(TableSession.opened_at.desc()).limit(limit).all()
        return {
            "sessions": [
                {
                    "id": str(s.id),
                    "table_number": s.table.number if s.table else None,
                    "guests_count": s.guests_count,
                    "status": s.status,
                    "waiter_id": str(s.waiter_id) if s.waiter_id else None,
                    "opened_at": s.opened_at.isoformat() if s.opened_at else None,
                    "duration_minutes": s.duration_minutes,
                }
                for s in sessions
            ],
        }
