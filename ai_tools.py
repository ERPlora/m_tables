"""
AI tools for the Tables module.

Uses @register_tool + AssistantTool class pattern.
All tools are async and use HubQuery for DB access.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import selectinload

from app.ai.registry import AssistantTool, register_tool
from app.core.db.query import HubQuery
from app.core.db.transactions import atomic

from .models import Table, TableSession, Zone


def _q(model, session, hub_id):
    return HubQuery(model, session, hub_id)


@register_tool
class ListZones(AssistantTool):
    name = "list_zones"
    description = (
        "List table zones/areas (e.g., 'Terraza', 'Interior', 'Barra'). "
        "Returns name, table count, available tables. Read-only."
    )
    module_id = "tables"
    required_permission = "tables.view_zone"
    parameters = {
        "type": "object",
        "properties": {
            "is_active": {"type": "boolean", "description": "Filter by active status"},
        },
        "required": [],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        query = _q(Zone, db, hub_id).options(selectinload(Zone.tables))
        if "is_active" in args:
            query = query.filter(Zone.is_active == args["is_active"])
        zones = await query.order_by(Zone.sort_order, Zone.name).all()
        return {
            "zones": [{
                "id": str(z.id),
                "name": z.name,
                "color": z.color,
                "is_active": z.is_active,
                "table_count": sum(1 for t in z.tables if not t.is_deleted),
                "available_tables": z.available_tables_count,
            } for z in zones],
        }


@register_tool
class CreateZone(AssistantTool):
    name = "create_zone"
    description = "Create a new table zone/area (e.g., 'Terraza', 'Sala VIP')."
    module_id = "tables"
    required_permission = "tables.add_zone"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Zone name"},
            "description": {"type": "string", "description": "Zone description"},
            "color": {"type": "string", "description": "Color class (e.g., 'primary', 'success')"},
            "sort_order": {"type": "integer", "description": "Display order"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        async with atomic(db) as session:
            z = Zone(
                hub_id=hub_id,
                name=args["name"],
                description=args.get("description", ""),
                color=args.get("color", "primary"),
                sort_order=args.get("sort_order", 0),
            )
            session.add(z)
            await session.flush()
        return {"id": str(z.id), "name": z.name, "created": True}


@register_tool
class ListTables(AssistantTool):
    name = "list_tables"
    description = (
        "List tables with optional filters. "
        "Returns number, name, capacity, zone, status, shape. Read-only."
    )
    module_id = "tables"
    required_permission = "tables.view_table"
    parameters = {
        "type": "object",
        "properties": {
            "zone_id": {"type": "string", "description": "Filter by zone ID"},
            "status": {"type": "string", "description": "Filter by status: available, occupied, reserved, blocked"},
            "is_active": {"type": "boolean", "description": "Filter by active status"},
        },
        "required": [],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        query = _q(Table, db, hub_id).options(selectinload(Table.zone))
        if args.get("zone_id"):
            query = query.filter(Table.zone_id == uuid.UUID(args["zone_id"]))
        if args.get("status"):
            query = query.filter(Table.status == args["status"])
        if "is_active" in args:
            query = query.filter(Table.is_active == args["is_active"])

        total = await query.count()
        tables = await query.order_by(Table.number).all()
        return {
            "tables": [{
                "id": str(t.id),
                "number": t.number,
                "name": t.name,
                "capacity": t.capacity,
                "shape": t.shape,
                "status": t.status,
                "is_active": t.is_active,
                "zone": t.zone.name if t.zone else None,
                "zone_id": str(t.zone_id) if t.zone_id else None,
            } for t in tables],
            "total": total,
        }


@register_tool
class CreateTable(AssistantTool):
    name = "create_table"
    description = "Create a new table. Specify number, capacity, zone, and shape."
    module_id = "tables"
    required_permission = "tables.add_table"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "number": {"type": "string", "description": "Table number/identifier (e.g., '1', 'T5', 'B3')"},
            "name": {"type": "string", "description": "Friendly name (e.g., 'Mesa ventana')"},
            "capacity": {"type": "integer", "description": "Seating capacity (default 4)"},
            "zone_id": {"type": "string", "description": "Zone ID to assign to"},
            "shape": {"type": "string", "description": "Shape: square, round, rectangle (default square)"},
            "position_x": {"type": "integer", "description": "X position on floor plan"},
            "position_y": {"type": "integer", "description": "Y position on floor plan"},
        },
        "required": ["number"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        async with atomic(db) as session:
            t = Table(
                hub_id=hub_id,
                number=args["number"],
                name=args.get("name", ""),
                capacity=args.get("capacity", 4),
                zone_id=uuid.UUID(args["zone_id"]) if args.get("zone_id") else None,
                shape=args.get("shape", "square"),
                position_x=args.get("position_x", 0),
                position_y=args.get("position_y", 0),
            )
            session.add(t)
            await session.flush()
        return {"id": str(t.id), "number": t.number, "capacity": t.capacity, "created": True}


@register_tool
class UpdateTable(AssistantTool):
    name = "update_table"
    description = "Update a table's properties (capacity, name, zone, status, shape)."
    module_id = "tables"
    required_permission = "tables.change_table"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "table_id": {"type": "string", "description": "Table ID"},
            "number": {"type": "string", "description": "New table number"},
            "name": {"type": "string", "description": "New friendly name"},
            "capacity": {"type": "integer", "description": "New capacity"},
            "zone_id": {"type": "string", "description": "New zone ID"},
            "shape": {"type": "string", "description": "New shape"},
            "status": {"type": "string", "description": "New status: available, occupied, reserved, blocked"},
            "is_active": {"type": "boolean", "description": "Active/inactive"},
        },
        "required": ["table_id"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        t = await _q(Table, db, hub_id).get(uuid.UUID(args["table_id"]))
        if t is None:
            return {"error": "Table not found"}
        for field in ("number", "name", "capacity", "shape", "status", "is_active"):
            if field in args:
                setattr(t, field, args[field])
        if "zone_id" in args:
            t.zone_id = uuid.UUID(args["zone_id"]) if args["zone_id"] else None
        await db.flush()
        return {"id": str(t.id), "number": t.number, "updated": True}


@register_tool
class BulkCreateTables(AssistantTool):
    name = "bulk_create_tables"
    description = (
        "Create multiple tables at once. "
        "Useful for initial setup (e.g., 'create 10 tables for zone Interior')."
    )
    module_id = "tables"
    required_permission = "tables.add_table"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "count": {"type": "integer", "description": "Number of tables to create"},
            "start_number": {"type": "integer", "description": "Starting table number (default 1)"},
            "prefix": {"type": "string", "description": "Number prefix (e.g., 'T' for T1, T2...)"},
            "capacity": {"type": "integer", "description": "Default capacity for all tables (default 4)"},
            "zone_id": {"type": "string", "description": "Zone ID for all tables"},
            "shape": {"type": "string", "description": "Shape for all tables (default square)"},
        },
        "required": ["count"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        count = args["count"]
        start = args.get("start_number", 1)
        prefix = args.get("prefix", "")
        capacity = args.get("capacity", 4)
        zone_id = uuid.UUID(args["zone_id"]) if args.get("zone_id") else None
        shape = args.get("shape", "square")

        created = []
        async with atomic(db) as session:
            for i in range(count):
                num = start + i
                t = Table(
                    hub_id=hub_id,
                    number=f"{prefix}{num}",
                    capacity=capacity,
                    zone_id=zone_id,
                    shape=shape,
                    position_x=(i % 5) * 20,
                    position_y=(i // 5) * 20,
                )
                session.add(t)
                await session.flush()
                created.append({"id": str(t.id), "number": t.number})

        return {"created": created, "total": len(created)}


@register_tool
class OpenTableSession(AssistantTool):
    name = "open_table_session"
    description = "Open a table session (seat guests at a table)."
    module_id = "tables"
    required_permission = "tables.add_tablesession"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "table_id": {"type": "string", "description": "Table ID"},
            "guests_count": {"type": "integer", "description": "Number of guests"},
            "waiter_id": {"type": "string", "description": "Waiter user ID"},
            "notes": {"type": "string", "description": "Session notes"},
        },
        "required": ["table_id", "guests_count"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        table = await _q(Table, db, hub_id).get(uuid.UUID(args["table_id"]))
        if table is None:
            return {"error": "Table not found"}
        if table.status != "available":
            return {"error": "Table is not available"}

        async with atomic(db) as session:
            ts = TableSession(
                hub_id=hub_id,
                table_id=table.id,
                guests_count=args["guests_count"],
                waiter_id=uuid.UUID(args["waiter_id"]) if args.get("waiter_id") else None,
                notes=args.get("notes", ""),
            )
            session.add(ts)
            await session.flush()
            table.set_status("occupied")

        return {
            "session_id": str(ts.id),
            "table_number": table.number,
            "guests": ts.guests_count,
            "opened": True,
        }


@register_tool
class ListTableSessions(AssistantTool):
    name = "list_table_sessions"
    description = "List table sessions (active or historical). Read-only."
    module_id = "tables"
    required_permission = "tables.view_tablesession"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: active, closed, transferred"},
            "zone_id": {"type": "string", "description": "Filter by zone"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        query = _q(TableSession, db, hub_id).options(
            selectinload(TableSession.table).selectinload(Table.zone),
        )
        if args.get("status"):
            query = query.filter(TableSession.status == args["status"])
        if args.get("zone_id"):
            query = query.filter(TableSession.table.has(Table.zone_id == uuid.UUID(args["zone_id"])))
        limit = args.get("limit", 20)
        sessions = await query.order_by(TableSession.opened_at.desc()).limit(limit).all()
        return {
            "sessions": [{
                "id": str(s.id),
                "table_number": s.table.number if s.table else None,
                "guests_count": s.guests_count,
                "status": s.status,
                "waiter_id": str(s.waiter_id) if s.waiter_id else None,
                "opened_at": s.opened_at.isoformat() if s.opened_at else None,
                "duration_minutes": s.duration_minutes,
            } for s in sessions],
        }
