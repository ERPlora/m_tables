"""
Tables module slot registrations.

Injects table UI into POS and other modules via the SlotRegistry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.templating.slots import SlotRegistry

MODULE_ID = "tables"


def register_slots(slots: SlotRegistry, module_id: str) -> None:
    """
    Register POS slot content for the tables module.

    Called by ModuleRuntime during module load.
    """
    # Future: inject table selector into POS toolbar.
    # slots.register(
    #     "sales.pos_toolbar",
    #     template="tables/pos/toolbar_button.html",
    #     priority=30,
    #     module_id=module_id,
    # )
