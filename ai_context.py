"""
Tables module AI context — injected into the LLM system prompt.

Provides the LLM with knowledge about the module's models, relationships,
and standard operating procedures.
"""

CONTEXT = """
## Tables Module

Models: Zone, Table, TableSession.

### Zone Model
- Fields: name, description, color, is_active, sort_order
- Represents an area: Main Hall, Terrace, VIP, Bar, etc.
- Each zone contains multiple tables

### Table Model
- Fields: number, name, capacity, shape (square/round/rectangle), status, is_active
- Floor plan: position_x, position_y, width, height (0-100 scale)
- Status: available, occupied, reserved, blocked
- Belongs to a zone (optional)

### TableSession Model
- Fields: table_id, opened_at, closed_at, guests_count, waiter_id, status, notes
- Status: active (currently seated), closed (finished), transferred (moved to another table)
- Supports table-to-table transfer with history tracking

### Key Relationships
- Zone 1:N Table (a zone has many tables)
- Table 1:N TableSession (a table has many sessions over time)
- TableSession self-referential (transferred_from → transferred_to)

### Typical Workflow
1. Create zones (areas of the restaurant)
2. Create tables in zones (with positions for floor plan)
3. Open session when guests sit down → table becomes "occupied"
4. Close session when guests leave → table becomes "available"
5. Transfer session if guests move to another table

### Restrictions (enforced by AI tools)

- **Deactivation guard**: Cannot deactivate a table that has an active session (status != "available")
- **Capacity warning**: Opening a session with guests_count > table.capacity produces a warning (but is allowed)
- **Capacity validation**: Table capacity must be > 0
"""

SOPS = [
    {
        "id": "setup_floor_plan",
        "triggers_es": ["configurar plano", "crear zonas", "crear mesas", "montar restaurante"],
        "triggers_en": ["setup floor plan", "create zones", "create tables", "setup restaurant"],
        "steps": ["create_zone", "bulk_create_tables"],
        "modules_required": ["tables"],
    },
    {
        "id": "open_table",
        "triggers_es": ["abrir mesa", "sentar clientes", "mesa ocupada"],
        "triggers_en": ["open table", "seat guests", "table occupied"],
        "steps": ["open_table_session"],
        "modules_required": ["tables"],
    },
    {
        "id": "check_availability",
        "triggers_es": ["mesas disponibles", "mesas libres", "hay mesa"],
        "triggers_en": ["available tables", "free tables", "any table available"],
        "steps": ["list_tables"],
        "modules_required": ["tables"],
    },
]
