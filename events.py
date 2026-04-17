"""
Tables module event subscriptions.

Registers handlers on the AsyncEventBus during module load.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.signals.dispatcher import AsyncEventBus

logger = logging.getLogger(__name__)

MODULE_ID = "tables"


def register_events(bus: AsyncEventBus, module_id: str) -> None:
    """
    Register event handlers for the tables module.

    Called by ModuleRuntime during module load.
    """
    # No event subscriptions needed for tables at this time.
    # Future: listen for "sales.completed" to auto-close sessions, etc.
