"""
Tables module hook registrations.

Registers actions and filters on the HookRegistry during module load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.hooks.registry import HookRegistry

MODULE_ID = "tables"


def register_hooks(hooks: HookRegistry, module_id: str) -> None:
    """
    Register hooks for the tables module.

    Called by ModuleRuntime during module load.
    """
    # No hooks needed for tables at this time.
    # Future: filter for POS integration (e.g., table assignment on sale).
