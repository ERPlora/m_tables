"""
Test fixtures for the tables module.
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC

import pytest

from tables.models import Table, TableSession, Zone


@pytest.fixture
def hub_id():
    """Test hub UUID."""
    return uuid.uuid4()


@pytest.fixture
def sample_zone(hub_id):
    """Create a sample zone instance (not persisted)."""
    return Zone(
        hub_id=hub_id,
        name="Main Hall",
        description="Indoor dining area",
        color="primary",
        sort_order=0,
    )


@pytest.fixture
def sample_table(hub_id, sample_zone):
    """Create a sample table instance (not persisted)."""
    return Table(
        hub_id=hub_id,
        zone_id=sample_zone.id,
        number="1",
        name="Window Table",
        capacity=4,
        shape="square",
        status="available",
        position_x=10,
        position_y=20,
        width=10,
        height=10,
    )


@pytest.fixture
def sample_session(hub_id, sample_table):
    """Create a sample active session (not persisted)."""
    return TableSession(
        hub_id=hub_id,
        table_id=sample_table.id,
        guests_count=2,
        status="active",
        opened_at=datetime.now(UTC),
    )
