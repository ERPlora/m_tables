"""
Pydantic schemas for tables module.

Replaces Django forms — used for request validation.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


# ============================================================================
# Zone
# ============================================================================

class ZoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    color: str = "primary"
    sort_order: int = 0
    is_active: bool = True


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    color: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


# ============================================================================
# Table
# ============================================================================

class TableCreate(BaseModel):
    zone_id: uuid.UUID | None = None
    number: str = Field(min_length=1, max_length=20)
    name: str = Field(default="", max_length=100)
    capacity: int = Field(default=4, ge=1)
    position_x: int = Field(default=0, ge=0, le=100)
    position_y: int = Field(default=0, ge=0, le=100)
    width: int = Field(default=10, ge=5, le=50)
    height: int = Field(default=10, ge=5, le=50)
    shape: str = "square"
    status: str = "available"
    is_active: bool = True


class TableUpdate(BaseModel):
    zone_id: uuid.UUID | None = None
    number: str | None = Field(default=None, max_length=20)
    name: str | None = None
    capacity: int | None = Field(default=None, ge=1)
    position_x: int | None = Field(default=None, ge=0, le=100)
    position_y: int | None = Field(default=None, ge=0, le=100)
    width: int | None = Field(default=None, ge=5, le=50)
    height: int | None = Field(default=None, ge=5, le=50)
    shape: str | None = None
    status: str | None = None
    is_active: bool | None = None


# ============================================================================
# Session
# ============================================================================

class SessionOpen(BaseModel):
    guests_count: int = Field(default=1, ge=1)
    notes: str = ""


class SessionTransfer(BaseModel):
    target_table_id: uuid.UUID
