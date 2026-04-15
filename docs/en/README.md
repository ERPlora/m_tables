# Tables (module: `tables`)

Restaurant floor plan management with zones, tables, and sessions.

## Purpose

The Tables module manages the physical floor plan of a restaurant or hospitality venue. It defines zones (areas such as Main Hall, Terrace, VIP) and tables within each zone. When a party is seated, a `TableSession` is opened on the table; it tracks covers (guest count), start time, linked sale, and waiter assignment.

The POS uses this module's data when the `tables` dependency is satisfied by `sales` — table selection appears as a step in the POS checkout flow. Managers design the floor plan in the Tables view and monitor which tables are occupied, reserved, or free in real time.

## Models

- `Zone` — Named area with color, sort order, and is_active flag. Contains tables.
- `Table` — Individual table: name/number, zone, shape (square/round/rectangle), capacity (covers), position (x, y, width, height for floor plan rendering), status (available/occupied/reserved/blocked), is_active.
- `TableSession` — Active or closed session on a table: table reference, covers, opened_at, closed_at, waiter reference, linked sale_id, status (active/closed/transferred), transfer notes.

## Routes

`GET /m/tables/` — Floor plan view with real-time table status
`GET /m/tables/zones` — Zone management
`GET /m/tables/tables` — Table list and configuration
`GET /m/tables/sessions` — Session history
`GET /m/tables/settings` — Module settings

## API

`GET /api/v1/m/tables/zones` — List zones (used by POS for table selection)
`GET /api/v1/m/tables/tables` — List tables with status
`POST /api/v1/m/tables/sessions` — Open a table session
`PATCH /api/v1/m/tables/sessions/{id}` — Update session (close, transfer)

## Events

No events consumed or emitted.

## Pricing

Free.
