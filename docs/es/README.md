# Tables (módulo: `tables`)

Gestión del plano de sala de restaurante con zonas, mesas y sesiones.

## Propósito

El módulo Tables gestiona el plano de sala físico de un restaurante o establecimiento de hostelería. Define zonas (áreas como Sala Principal, Terraza, VIP) y las mesas dentro de cada zona. Cuando un grupo es acomodado, se abre una `TableSession` en la mesa; registra el número de comensales, la hora de inicio, la venta vinculada y el camarero asignado.

El POS utiliza los datos de este módulo cuando la dependencia `tables` está satisfecha por `sales` — la selección de mesa aparece como un paso en el flujo de cobro del POS. Los gestores diseñan el plano de sala en la vista Tables y monitorizan en tiempo real qué mesas están ocupadas, reservadas o libres.

## Modelos

- `Zone` — Área con nombre, color, orden de visualización y flag is_active. Contiene mesas.
- `Table` — Mesa individual: nombre/número, zona, forma (square/round/rectangle), capacidad (comensales), posición (x, y, width, height para renderizado del plano), estado (available/occupied/reserved/blocked), is_active.
- `TableSession` — Sesión activa o cerrada en una mesa: referencia de mesa, comensales, opened_at, closed_at, referencia de camarero, sale_id vinculado, estado (active/closed/transferred), notas de transferencia.

## Rutas

`GET /m/tables/` — Vista del plano de sala con estado de mesas en tiempo real
`GET /m/tables/zones` — Gestión de zonas
`GET /m/tables/tables` — Lista y configuración de mesas
`GET /m/tables/sessions` — Historial de sesiones
`GET /m/tables/settings` — Configuración del módulo

## API

`GET /api/v1/m/tables/zones` — Listar zonas (usado por el POS para selección de mesa)
`GET /api/v1/m/tables/tables` — Listar mesas con estado
`POST /api/v1/m/tables/sessions` — Abrir una sesión de mesa
`PATCH /api/v1/m/tables/sessions/{id}` — Actualizar sesión (cerrar, transferir)

## Eventos

No consume ni emite eventos.

## Precio

Gratuito.
