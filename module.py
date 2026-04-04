"""
Tables module manifest.

Restaurant floor plan management with zones, tables, and sessions.
"""

from app.core.i18n import LazyString

# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------
MODULE_ID = "tables"
MODULE_NAME = LazyString("Tables", module_id="tables")
MODULE_VERSION = "2.0.0"
MODULE_ICON = "material:table_restaurant"
MODULE_DESCRIPTION = LazyString(
    "Restaurant floor plan management with zones, tables, and sessions",
    module_id="tables",
)
MODULE_AUTHOR = "ERPlora"
MODULE_CATEGORY = "hospitality"

# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------
HAS_MODELS = True
MIDDLEWARE = ""

# ---------------------------------------------------------------------------
# Menu (sidebar entry)
# ---------------------------------------------------------------------------
MENU = {
    "label": LazyString("Tables", module_id="tables"),
    "icon": "material:table_restaurant",
    "order": 20,
}

# ---------------------------------------------------------------------------
# Navigation tabs (bottom tabbar in module views)
# ---------------------------------------------------------------------------
NAVIGATION = [
    {"id": "floor_plan", "label": LazyString("Floor Plan", module_id="tables"), "icon": "map-outline", "view": ""},
    {"id": "zones", "label": LazyString("Zones", module_id="tables"), "icon": "layers-outline", "view": "zones"},
    {"id": "tables", "label": LazyString("Tables", module_id="tables"), "icon": "grid-outline", "view": "tables"},
    {"id": "sessions", "label": LazyString("Sessions", module_id="tables"), "icon": "time-outline", "view": "sessions"},
    {"id": "settings", "label": LazyString("Settings", module_id="tables"), "icon": "settings-outline", "view": "settings"},
]

# ---------------------------------------------------------------------------
# Dependencies (other modules required to be active)
# ---------------------------------------------------------------------------
DEPENDENCIES: list[str] = []

# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
PERMISSIONS = [
    ("view_zone", LazyString("View zones", module_id="tables")),
    ("add_zone", LazyString("Add zones", module_id="tables")),
    ("change_zone", LazyString("Edit zones", module_id="tables")),
    ("delete_zone", LazyString("Delete zones", module_id="tables")),
    ("view_table", LazyString("View tables", module_id="tables")),
    ("add_table", LazyString("Add tables", module_id="tables")),
    ("change_table", LazyString("Edit tables", module_id="tables")),
    ("delete_table", LazyString("Delete tables", module_id="tables")),
    ("view_tablesession", LazyString("View table sessions", module_id="tables")),
    ("add_tablesession", LazyString("Add table sessions", module_id="tables")),
    ("change_tablesession", LazyString("Edit table sessions", module_id="tables")),
    ("delete_tablesession", LazyString("Delete table sessions", module_id="tables")),
    ("manage_settings", LazyString("Manage settings", module_id="tables")),
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "add_table", "add_tablesession", "add_zone",
        "change_table", "change_tablesession", "change_zone",
        "view_table", "view_tablesession", "view_zone",
    ],
    "employee": [
        "add_zone",
        "view_table", "view_tablesession", "view_zone",
    ],
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
SCHEDULED_TASKS: list[dict] = []

# ---------------------------------------------------------------------------
# Pricing (free module)
# ---------------------------------------------------------------------------
# PRICING = {"monthly": 0, "yearly": 0}
