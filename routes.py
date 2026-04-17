"""
Tables module HTMX views — FastAPI router.

Replaces Django views.py + urls.py. Uses @htmx_view decorator
(partial for HTMX requests, full page for direct navigation).
Mounted at /m/tables/ by ModuleRuntime.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from runtime.models.queryset import HubQuery
from runtime.orm.transactions import atomic
from runtime.auth.current_user import CurrentUser, DbSession, HubId
from runtime.views.responses import add_message, htmx_redirect, htmx_view

from .models import (
    TABLE_STATUS_CHOICES,
    TABLE_STATUS_LABELS,
    Table,
    TableSession,
    Zone,
)
from .schemas import TableCreate, ZoneCreate

router = APIRouter()


def _q(model, db, hub_id):
    return HubQuery(model, db, hub_id)


# ============================================================================
# Floor Plan
# ============================================================================

@router.get("/")
@htmx_view(module_id="tables", view_id="floor_plan")
async def index(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Floor plan — redirect to floor_plan."""
    return await floor_plan(request, db, user, hub_id)


@router.get("/floor-plan")
@htmx_view(module_id="tables", view_id="floor_plan")
async def floor_plan(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
    zone: str = "",
):
    """Floor plan view with table positioning and status overview."""
    zones = await _q(Zone, db, hub_id).filter(
        Zone.is_active == True,  # noqa: E712
    ).order_by(Zone.sort_order, Zone.name).all()

    tables_query = _q(Table, db, hub_id).filter(
        Table.is_active == True,  # noqa: E712
    ).options(selectinload(Table.zone))

    if zone:
        tables_query = tables_query.filter(Table.zone_id == uuid.UUID(zone))

    tables = await tables_query.order_by(Table.number).all()

    status_counts = {
        "available": sum(1 for t in tables if t.status == "available"),
        "occupied": sum(1 for t in tables if t.status == "occupied"),
        "reserved": sum(1 for t in tables if t.status == "reserved"),
        "blocked": sum(1 for t in tables if t.status == "blocked"),
    }

    tables_json = json.dumps([{
        "id": str(t.id),
        "number": t.number,
        "name": t.name,
        "display_name": t.display_name,
        "capacity": t.capacity,
        "position_x": t.position_x,
        "position_y": t.position_y,
        "width": t.width,
        "height": t.height,
        "shape": t.shape,
        "status": t.status,
        "zone_id": str(t.zone_id) if t.zone_id else None,
        "zone_name": t.zone.name if t.zone else None,
    } for t in tables])

    return {
        "zones": zones,
        "tables": tables,
        "tables_json": tables_json,
        "zone_filter": zone,
        "status_counts": status_counts,
        "total_tables": len(tables),
    }


# ============================================================================
# Zones
# ============================================================================

@router.get("/zones")
@htmx_view(module_id="tables", view_id="zones")
async def zones_list(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """List all zones with table counts."""
    zones = await _q(Zone, db, hub_id).options(
        selectinload(Zone.tables),
    ).order_by(Zone.sort_order, Zone.name).all()

    # Compute table_count for each zone (non-deleted tables)
    zone_data = []
    for z in zones:
        z.table_count = sum(1 for t in z.tables if not t.is_deleted)
        zone_data.append(z)

    return {"zones": zone_data}


@router.get("/zones/add")
@htmx_view(module_id="tables", view_id="zones")
async def zone_add(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Zone create form."""
    return {"is_new": True}


@router.post("/zones/add")
async def zone_add_post(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Create a zone."""
    form = await request.form()
    try:
        data = ZoneCreate(
            name=form.get("name", ""),
            description=form.get("description", ""),
            color=form.get("color", "primary"),
            sort_order=int(form.get("sort_order", 0)),
            is_active=form.get("is_active") in ("on", "true", None),
        )
    except (ValidationError, ValueError) as e:
        add_message(request, "error", str(e))
        return htmx_redirect("/m/tables/zones/add")

    async with atomic(db) as session:
        zone = Zone(hub_id=hub_id, **data.model_dump())
        session.add(zone)

    add_message(request, "success", f"Zone {data.name} created")
    return htmx_redirect("/m/tables/zones")


@router.get("/zones/{zone_id}/edit")
@htmx_view(module_id="tables", view_id="zones")
async def zone_edit(
    request: Request, zone_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Zone edit form."""
    zone = await _q(Zone, db, hub_id).get(zone_id)
    if zone is None:
        return JSONResponse({"error": "Zone not found"}, status_code=404)
    return {"zone": zone, "is_new": False}


@router.post("/zones/{zone_id}/edit")
async def zone_edit_post(
    request: Request, zone_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update a zone."""
    zone = await _q(Zone, db, hub_id).get(zone_id)
    if zone is None:
        return JSONResponse({"error": "Zone not found"}, status_code=404)

    form = await request.form()
    for field_name in ("name", "description", "color"):
        value = form.get(field_name)
        if value is not None:
            setattr(zone, field_name, value)

    sort_order = form.get("sort_order")
    if sort_order is not None:
        zone.sort_order = int(sort_order)

    is_active = form.get("is_active")
    if is_active is not None:
        zone.is_active = is_active in ("on", "true")

    await db.flush()
    add_message(request, "success", f"Zone {zone.name} updated")
    return htmx_redirect("/m/tables/zones")


@router.post("/zones/{zone_id}/delete")
async def zone_delete(
    request: Request, zone_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Soft-delete a zone."""
    await _q(Zone, db, hub_id).delete(zone_id)
    return JSONResponse({"success": True, "message": "Zone deleted"})


# ============================================================================
# Tables
# ============================================================================

@router.get("/tables")
@htmx_view(module_id="tables", view_id="tables")
async def tables_list(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
    q: str = "", zone: str = "", status: str = "",
):
    """Table list with filters."""
    tables_query = _q(Table, db, hub_id).options(
        selectinload(Table.zone),
    )

    if q:
        tables_query = tables_query.filter(or_(
            Table.number.ilike(f"%{q}%"),
            Table.name.ilike(f"%{q}%"),
        ))
    if zone:
        tables_query = tables_query.filter(Table.zone_id == uuid.UUID(zone))
    if status:
        tables_query = tables_query.filter(Table.status == status)

    tables = await tables_query.order_by(Table.number).all()

    zones = await _q(Zone, db, hub_id).filter(
        Zone.is_active == True,  # noqa: E712
    ).order_by(Zone.sort_order, Zone.name).all()

    status_choices = [(s, TABLE_STATUS_LABELS[s]) for s in TABLE_STATUS_CHOICES]

    return {
        "tables": tables,
        "zones": zones,
        "search_query": q,
        "zone_filter": zone,
        "status_filter": status,
        "status_choices": status_choices,
    }


@router.get("/tables/add")
@htmx_view(module_id="tables", view_id="tables")
async def table_add(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Table create form."""
    zones = await _q(Zone, db, hub_id).filter(
        Zone.is_active == True,  # noqa: E712
    ).order_by(Zone.sort_order, Zone.name).all()

    status_choices = [(s, TABLE_STATUS_LABELS[s]) for s in TABLE_STATUS_CHOICES]
    shape_choices = [("square", "Square"), ("round", "Round"), ("rectangle", "Rectangle")]

    return {
        "zones": zones, "is_new": True,
        "status_choices": status_choices, "shape_choices": shape_choices,
    }


@router.post("/tables/add")
async def table_add_post(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Create a table."""
    form = await request.form()
    try:
        zone_id_str = form.get("zone_id", "")
        data = TableCreate(
            zone_id=uuid.UUID(zone_id_str) if zone_id_str else None,
            number=form.get("number", ""),
            name=form.get("name", ""),
            capacity=int(form.get("capacity", 4)),
            position_x=int(form.get("position_x", 0)),
            position_y=int(form.get("position_y", 0)),
            width=int(form.get("width", 10)),
            height=int(form.get("height", 10)),
            shape=form.get("shape", "square"),
            status=form.get("status", "available"),
            is_active=form.get("is_active") in ("on", "true", None),
        )
    except (ValidationError, ValueError) as e:
        add_message(request, "error", str(e))
        return htmx_redirect("/m/tables/tables/add")

    async with atomic(db) as session:
        table = Table(hub_id=hub_id, **data.model_dump())
        session.add(table)

    add_message(request, "success", f"Table {data.number} created")
    return htmx_redirect("/m/tables/tables")


@router.get("/tables/{table_id}")
@htmx_view(module_id="tables", view_id="tables", partial_template="tables/partials/table_detail.html")
async def table_detail(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Table detail view with current session and history."""
    table = await _q(Table, db, hub_id).options(
        selectinload(Table.zone),
        selectinload(Table.sessions),
    ).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)

    # Current active session
    current_session = None
    for s in table.sessions:
        if not s.is_deleted and s.status == "active":
            current_session = s
            break

    # Recent past sessions
    recent_sessions = await _q(TableSession, db, hub_id).filter(
        TableSession.table_id == table_id,
        TableSession.status != "active",
    ).order_by(TableSession.opened_at.desc()).limit(10).all()

    # Available tables for transfer
    available_tables = await _q(Table, db, hub_id).filter(
        Table.is_active == True,  # noqa: E712
        Table.status == "available",
        Table.id != table_id,
    ).options(selectinload(Table.zone)).order_by(Table.number).all()

    return {
        "table": table,
        "current_session": current_session,
        "recent_sessions": recent_sessions,
        "available_tables": available_tables,
    }


@router.get("/tables/{table_id}/edit")
@htmx_view(module_id="tables", view_id="tables")
async def table_edit(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Table edit form."""
    table = await _q(Table, db, hub_id).options(
        selectinload(Table.zone),
    ).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)

    zones = await _q(Zone, db, hub_id).filter(
        Zone.is_active == True,  # noqa: E712
    ).order_by(Zone.sort_order, Zone.name).all()

    status_choices = [(s, TABLE_STATUS_LABELS[s]) for s in TABLE_STATUS_CHOICES]
    shape_choices = [("square", "Square"), ("round", "Round"), ("rectangle", "Rectangle")]

    return {
        "table": table, "zones": zones, "is_new": False,
        "status_choices": status_choices, "shape_choices": shape_choices,
    }


@router.post("/tables/{table_id}/edit")
async def table_edit_post(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update a table."""
    table = await _q(Table, db, hub_id).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)

    form = await request.form()
    for field_name in ("number", "name", "shape", "status"):
        value = form.get(field_name)
        if value is not None:
            setattr(table, field_name, value)

    for int_field in ("capacity", "position_x", "position_y", "width", "height"):
        value = form.get(int_field)
        if value is not None:
            setattr(table, int_field, int(value))

    zone_id_str = form.get("zone_id", "")
    if zone_id_str:
        table.zone_id = uuid.UUID(zone_id_str)
    elif "zone_id" in dict(form):
        table.zone_id = None

    is_active = form.get("is_active")
    if is_active is not None:
        table.is_active = is_active in ("on", "true")

    await db.flush()
    add_message(request, "success", f"Table {table.display_name} updated")
    return htmx_redirect(f"/m/tables/tables/{table.id}")


@router.post("/tables/{table_id}/delete")
async def table_delete(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Soft-delete a table."""
    await _q(Table, db, hub_id).delete(table_id)
    return JSONResponse({"success": True, "message": "Table deleted"})


@router.post("/tables/{table_id}/status")
async def table_update_status(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update table status."""
    table = await _q(Table, db, hub_id).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)

    form = await request.form()
    new_status = form.get("status")
    if new_status in TABLE_STATUS_CHOICES:
        table.set_status(new_status)
        await db.flush()
        return JSONResponse({"success": True, "message": "Status updated", "status": new_status})
    return JSONResponse({"success": False, "message": "Invalid status"}, status_code=400)


@router.post("/tables/{table_id}/position")
async def table_update_position(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update table position on floor plan."""
    table = await _q(Table, db, hub_id).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)

    form = await request.form()
    try:
        position_x = max(0, min(100, int(form.get("position_x", table.position_x))))
        position_y = max(0, min(100, int(form.get("position_y", table.position_y))))
        table.position_x = position_x
        table.position_y = position_y
        await db.flush()
        return JSONResponse({"success": True, "position_x": position_x, "position_y": position_y})
    except (ValueError, TypeError):
        return JSONResponse({"success": False, "message": "Invalid position"}, status_code=400)


# ============================================================================
# Sessions
# ============================================================================

@router.get("/sessions")
@htmx_view(module_id="tables", view_id="sessions")
async def sessions_list(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
    show_closed: str = "",
):
    """List sessions (active or all)."""
    sessions_query = _q(TableSession, db, hub_id).options(
        selectinload(TableSession.table).selectinload(Table.zone),
    )

    if show_closed != "true":
        sessions_query = sessions_query.filter(TableSession.status == "active")

    sessions = await sessions_query.order_by(
        TableSession.opened_at.desc(),
    ).limit(100).all()

    return {"sessions": sessions, "show_closed": show_closed == "true"}


@router.post("/tables/{table_id}/open")
async def session_open(
    request: Request, table_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Open a session at a table."""
    table = await _q(Table, db, hub_id).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)

    if table.status != "available":
        return JSONResponse(
            {"success": False, "message": "Table is not available"}, status_code=400,
        )

    form = await request.form()
    guests_count = int(form.get("guests_count", 1))
    notes = form.get("notes", "")

    async with atomic(db) as session:
        table_session = TableSession(
            hub_id=hub_id,
            table_id=table.id,
            guests_count=guests_count,
            waiter_id=user.id,
            notes=notes,
        )
        session.add(table_session)
        await session.flush()
        table.set_status("occupied")

    return JSONResponse({
        "success": True,
        "message": "Table opened",
        "session_id": str(table_session.id),
    })


@router.post("/sessions/{session_id}/close")
async def session_close(
    request: Request, session_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Close a table session."""
    table_session = await _q(TableSession, db, hub_id).options(
        selectinload(TableSession.table),
    ).filter(
        TableSession.status == "active",
    ).get(session_id)
    if table_session is None:
        return JSONResponse({"error": "Active session not found"}, status_code=404)

    table_session.close()
    await db.flush()
    return JSONResponse({"success": True, "message": "Table closed"})


@router.post("/sessions/{session_id}/transfer")
async def session_transfer(
    request: Request, session_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Transfer a session to another table."""
    table_session = await _q(TableSession, db, hub_id).options(
        selectinload(TableSession.table),
    ).filter(
        TableSession.status == "active",
    ).get(session_id)
    if table_session is None:
        return JSONResponse({"error": "Active session not found"}, status_code=404)

    form = await request.form()
    target_table_id = form.get("target_table_id")
    if not target_table_id:
        return JSONResponse({"error": "Target table required"}, status_code=400)

    target_table = await _q(Table, db, hub_id).filter(
        Table.is_active == True,  # noqa: E712
        Table.status == "available",
    ).get(uuid.UUID(target_table_id))
    if target_table is None:
        return JSONResponse({"error": "Target table not available"}, status_code=404)

    async with atomic(db) as session:
        new_session = table_session.transfer_to(target_table, hub_id=hub_id, waiter_id=user.id)
        session.add(new_session)
        await session.flush()

    return JSONResponse({
        "success": True,
        "message": "Session transferred",
        "new_session_id": str(new_session.id),
    })


# ============================================================================
# Settings
# ============================================================================

@router.get("/settings")
@htmx_view(module_id="tables", view_id="settings")
async def settings_view(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Tables settings overview."""
    zones = await _q(Zone, db, hub_id).options(
        selectinload(Zone.tables),
    ).order_by(Zone.sort_order, Zone.name).all()

    for z in zones:
        z.table_count = sum(1 for t in z.tables if not t.is_deleted)

    total_tables = await _q(Table, db, hub_id).count()
    active_tables = await _q(Table, db, hub_id).filter(
        Table.is_active == True,  # noqa: E712
    ).count()
    active_sessions = await _q(TableSession, db, hub_id).filter(
        TableSession.status == "active",
    ).count()

    return {
        "zones": zones,
        "total_tables": total_tables,
        "active_tables": active_tables,
        "active_sessions": active_sessions,
    }
