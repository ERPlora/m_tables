"""
Tables module manifest.

Restaurant floor plan management with zones, tables, and sessions.
"""


# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------
MODULE_ID = "tables"
MODULE_NAME = "Tables"
MODULE_VERSION = "2.0.4"
MODULE_ICON = "material:table_restaurant"
MODULE_DESCRIPTION = "Restaurant floor plan management with zones, tables, and sessions"
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
    "label": "Tables",
    "icon": "material:table_restaurant",
    "order": 20,
}

# ---------------------------------------------------------------------------
# Navigation tabs (bottom tabbar in module views)
# ---------------------------------------------------------------------------
NAVIGATION = [
    {"id": "floor_plan", "label": "Floor Plan", "icon": "map-outline", "view": ""},
    {"id": "zones", "label": "Zones", "icon": "layers-outline", "view": "zones"},
    {"id": "tables", "label": "Tables", "icon": "grid-outline", "view": "tables"},
    {"id": "sessions", "label": "Sessions", "icon": "time-outline", "view": "sessions"},
    {"id": "settings", "label": "Settings", "icon": "settings-outline", "view": "settings"},
]

# ---------------------------------------------------------------------------
# Dependencies (other modules required to be active)
# ---------------------------------------------------------------------------
DEPENDENCIES: list[str] = []

# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
PERMISSIONS = [
    ("view_zone", "View zones"),
    ("add_zone", "Add zones"),
    ("change_zone", "Edit zones"),
    ("delete_zone", "Delete zones"),
    ("view_table", "View tables"),
    ("add_table", "Add tables"),
    ("change_table", "Edit tables"),
    ("delete_table", "Delete tables"),
    ("view_tablesession", "View table sessions"),
    ("add_tablesession", "Add table sessions"),
    ("change_tablesession", "Edit table sessions"),
    ("delete_tablesession", "Delete table sessions"),
    ("manage_settings", "Manage settings"),
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
