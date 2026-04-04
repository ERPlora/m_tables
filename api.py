"""
Tables module REST API — FastAPI router.

JSON endpoints for external consumers (Cloud sync, CLI, webhooks).
Mounted at /api/v1/m/tables/ by ModuleRuntime.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.core.db.query import HubQuery
from app.core.db.transactions import atomic
from app.core.dependencies import CurrentUser, DbSession, HubId

from .models import Table, TableSession, Zone
from .schemas import TableCreate, TableUpdate, ZoneCreate, ZoneUpdate

api_router = APIRouter()


def _q(model, session, hub_id):
    return HubQuery(model, session, hub_id)


# ============================================================================
# Zones API
# ============================================================================

@api_router.get("/zones")
async def list_zones(
    request: Request, db: DbSession, hub_id: HubId,
    q: str = "", offset: int = 0, limit: int = Query(default=50, le=100),
):
    """List zones."""
    query = _q(Zone, db, hub_id)
    if q:
        query = query.filter(Zone.name.ilike(f"%{q}%"))
    total = await query.count()
    zones = await query.order_by(Zone.sort_order, Zone.name).offset(offset).limit(limit).all()
    return {
        "zones": [{
            "id": str(z.id), "name": z.name, "description": z.description,
            "color": z.color, "is_active": z.is_active, "sort_order": z.sort_order,
            "created_at": z.created_at.isoformat(),
        } for z in zones],
        "total": total,
    }


@api_router.post("/zones")
async def create_zone(
    request: Request, body: ZoneCreate,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Create a zone."""
    async with atomic(db) as session:
        zone = Zone(hub_id=hub_id, **body.model_dump())
        session.add(zone)
        await session.flush()
    return JSONResponse(
        {"id": str(zone.id), "name": zone.name, "created": True},
        status_code=201,
    )


@api_router.patch("/zones/{zone_id}")
async def update_zone(
    zone_id: uuid.UUID, body: ZoneUpdate,
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update a zone."""
    zone = await _q(Zone, db, hub_id).get(zone_id)
    if zone is None:
        return JSONResponse({"error": "Zone not found"}, status_code=404)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(zone, key, value)
    await db.flush()
    return {"id": str(zone.id), "name": zone.name, "updated": True}


@api_router.delete("/zones/{zone_id}")
async def delete_zone(
    zone_id: uuid.UUID, request: Request,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Soft-delete a zone."""
    deleted = await _q(Zone, db, hub_id).delete(zone_id)
    if not deleted:
        return JSONResponse({"error": "Zone not found"}, status_code=404)
    return {"deleted": True}


# ============================================================================
# Tables API
# ============================================================================

@api_router.get("/tables")
async def list_tables(
    request: Request, db: DbSession, hub_id: HubId,
    q: str = "", zone_id: str = "", status: str = "",
    offset: int = 0, limit: int = Query(default=50, le=100),
):
    """List tables with filters."""
    query = _q(Table, db, hub_id).options(selectinload(Table.zone))
    if q:
        query = query.filter(or_(
            Table.number.ilike(f"%{q}%"),
            Table.name.ilike(f"%{q}%"),
        ))
    if zone_id:
        query = query.filter(Table.zone_id == uuid.UUID(zone_id))
    if status:
        query = query.filter(Table.status == status)

    total = await query.count()
    tables = await query.order_by(Table.number).offset(offset).limit(limit).all()
    return {
        "tables": [{
            "id": str(t.id), "number": t.number, "name": t.name,
            "capacity": t.capacity, "shape": t.shape, "status": t.status,
            "is_active": t.is_active,
            "zone": {"id": str(t.zone.id), "name": t.zone.name} if t.zone else None,
            "position_x": t.position_x, "position_y": t.position_y,
            "width": t.width, "height": t.height,
            "created_at": t.created_at.isoformat(),
        } for t in tables],
        "total": total,
    }


@api_router.get("/tables/{table_id}")
async def get_table(
    table_id: uuid.UUID, request: Request, db: DbSession, hub_id: HubId,
):
    """Get table details."""
    table = await _q(Table, db, hub_id).options(
        selectinload(Table.zone),
    ).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)
    return {
        "id": str(table.id), "number": table.number, "name": table.name,
        "display_name": table.display_name, "capacity": table.capacity,
        "shape": table.shape, "status": table.status, "is_active": table.is_active,
        "zone": {"id": str(table.zone.id), "name": table.zone.name} if table.zone else None,
        "position_x": table.position_x, "position_y": table.position_y,
        "width": table.width, "height": table.height,
        "created_at": table.created_at.isoformat(),
    }


@api_router.post("/tables")
async def create_table(
    request: Request, body: TableCreate,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Create a table."""
    async with atomic(db) as session:
        table = Table(hub_id=hub_id, **body.model_dump())
        session.add(table)
        await session.flush()
    return JSONResponse(
        {"id": str(table.id), "number": table.number, "created": True},
        status_code=201,
    )


@api_router.patch("/tables/{table_id}")
async def update_table(
    table_id: uuid.UUID, body: TableUpdate,
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update a table."""
    table = await _q(Table, db, hub_id).get(table_id)
    if table is None:
        return JSONResponse({"error": "Table not found"}, status_code=404)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(table, key, value)
    await db.flush()
    return {"id": str(table.id), "number": table.number, "updated": True}


@api_router.delete("/tables/{table_id}")
async def delete_table(
    table_id: uuid.UUID, request: Request,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Soft-delete a table."""
    deleted = await _q(Table, db, hub_id).delete(table_id)
    if not deleted:
        return JSONResponse({"error": "Table not found"}, status_code=404)
    return {"deleted": True}


# ============================================================================
# Sessions API
# ============================================================================

@api_router.get("/sessions")
async def list_sessions(
    request: Request, db: DbSession, hub_id: HubId,
    status: str = "", table_id: str = "",
    offset: int = 0, limit: int = Query(default=50, le=100),
):
    """List sessions."""
    query = _q(TableSession, db, hub_id).options(
        selectinload(TableSession.table),
    )
    if status:
        query = query.filter(TableSession.status == status)
    if table_id:
        query = query.filter(TableSession.table_id == uuid.UUID(table_id))

    total = await query.count()
    sessions = await query.order_by(
        TableSession.opened_at.desc(),
    ).offset(offset).limit(limit).all()
    return {
        "sessions": [{
            "id": str(s.id),
            "table_number": s.table.number if s.table else None,
            "table_id": str(s.table_id),
            "guests_count": s.guests_count,
            "status": s.status,
            "waiter_id": str(s.waiter_id) if s.waiter_id else None,
            "opened_at": s.opened_at.isoformat() if s.opened_at else None,
            "closed_at": s.closed_at.isoformat() if s.closed_at else None,
            "duration_minutes": s.duration_minutes,
            "notes": s.notes,
        } for s in sessions],
        "total": total,
    }
