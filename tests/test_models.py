"""
Tests for tables module models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, UTC

from tables.models import (
    SESSION_STATUS_COLORS,
    SESSION_STATUS_LABELS,
    TABLE_STATUS_CHOICES,
    TABLE_STATUS_COLORS,
    TABLE_STATUS_LABELS,
    Table,
    TableSession,
)


class TestZone:
    def test_repr(self, sample_zone):
        assert "Main Hall" in repr(sample_zone)


class TestTable:
    def test_display_name_with_name(self, sample_table):
        assert sample_table.display_name == "1 - Window Table"

    def test_display_name_without_name(self, hub_id):
        t = Table(hub_id=hub_id, number="5", name="")
        assert t.display_name == "Table 5"

    def test_status_label(self, sample_table):
        sample_table.status = "available"
        assert sample_table.status_label == "Available"
        sample_table.status = "occupied"
        assert sample_table.status_label == "Occupied"

    def test_status_color(self, sample_table):
        sample_table.status = "available"
        assert sample_table.status_color == "success"
        sample_table.status = "blocked"
        assert sample_table.status_color == "error"

    def test_shape_label(self, sample_table):
        sample_table.shape = "round"
        assert sample_table.shape_label == "Round"

    def test_set_status_valid(self, sample_table):
        sample_table.set_status("occupied")
        assert sample_table.status == "occupied"

    def test_set_status_invalid(self, sample_table):
        sample_table.set_status("invalid_status")
        assert sample_table.status == "available"  # unchanged

    def test_all_statuses_have_labels(self):
        for status in TABLE_STATUS_CHOICES:
            assert status in TABLE_STATUS_LABELS

    def test_all_statuses_have_colors(self):
        for status in TABLE_STATUS_CHOICES:
            assert status in TABLE_STATUS_COLORS


class TestTableSession:
    def test_duration_minutes(self, sample_session):
        sample_session.opened_at = datetime.now(UTC) - timedelta(minutes=45)
        assert 44 <= sample_session.duration_minutes <= 46

    def test_status_label(self, sample_session):
        assert sample_session.status_label == "Active"
        sample_session.status = "closed"
        assert sample_session.status_label == "Closed"

    def test_status_color(self, sample_session):
        assert sample_session.status_color == "warning"
        sample_session.status = "transferred"
        assert sample_session.status_color == "primary"

    def test_close(self, hub_id):
        table = Table(hub_id=hub_id, number="1", status="occupied")
        session = TableSession(
            hub_id=hub_id, table_id=table.id, guests_count=2, status="active",
            opened_at=datetime.now(UTC),
        )
        session.table = table
        session.close()
        assert session.status == "closed"
        assert session.closed_at is not None
        assert table.status == "available"

    def test_transfer_to(self, hub_id):
        table1 = Table(hub_id=hub_id, number="1", status="occupied")
        table1.id = uuid.uuid4()
        table2 = Table(hub_id=hub_id, number="2", status="available")
        table2.id = uuid.uuid4()

        session = TableSession(
            hub_id=hub_id, table_id=table1.id, guests_count=3, status="active",
            opened_at=datetime.now(UTC), notes="VIP guests",
        )
        session.id = uuid.uuid4()
        session.table = table1

        new_session = session.transfer_to(table2, hub_id=hub_id)
        assert session.status == "transferred"
        assert session.closed_at is not None
        assert table1.status == "available"
        assert table2.status == "occupied"
        assert new_session.guests_count == 3
        assert new_session.notes == "VIP guests"
        assert new_session.transferred_from_id == session.id

    def test_all_session_statuses_have_labels(self):
        from tables.models import SESSION_STATUS_CHOICES
        for status in SESSION_STATUS_CHOICES:
            assert status in SESSION_STATUS_LABELS

    def test_all_session_statuses_have_colors(self):
        from tables.models import SESSION_STATUS_CHOICES
        for status in SESSION_STATUS_CHOICES:
            assert status in SESSION_STATUS_COLORS
