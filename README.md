# BackendHacking

Backend FastAPI para un mini Kanban con proyectos privados, roles reales y tableros por proyecto.

## Requisitos

- Python 3.11 o superior
- PostgreSQL
- Entorno virtual activo

## Estructura

```text
BackendHacking/
|-- app/
|   |-- api/v1/endpoints/
|   |-- core/
|   |-- db/
|   |-- models/
|   `-- schemas/
|-- alembic/
|-- database/
|-- migrations/
|-- seeders/
|-- scripts/
|-- .env.example
|-- alembic.ini
|-- README.md
`-- requirements.txt
```

## Configuracion

Crear `.env` desde `.env.example` y ajustar PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=BDKANBAN
DB_USER=postgres
DB_PASSWORD=123456

JWT_SECRET=clave_insegura_demo
JWT_EXPIRES_IN=7d
```

Probar conexion:

```powershell
python -m app.db.check_connection
```

## Migraciones

Este cambio usa reset de entorno dev. Borra las tablas gestionadas por la migracion y vuelve a crearlas con el esquema nuevo:

```powershell
python -m alembic downgrade base
python -m alembic upgrade head
python -m alembic current
```

La migracion ejecuta:

- `migrations/001_create_kanban_schema.sql`
- `seeders/001_seed_roles.sql`

El rollback usa:

- `migrations/001_drop_kanban_schema.sql`

## Roles

Existen dos roles globales:

- `SuperAdministrador`: acceso total al sistema.
- `Usuario_Comun`: acceso solo a proyectos donde participa.

Seeder inicial:

```text
email: superadmin@example.com
password: 123456
rol: SuperAdministrador
```

Los usuarios registrados por `POST /api/auth/register` siempre nacen como `Usuario_Comun`.

## Modelo Funcional

- Un `Usuario_Comun` puede crear proyectos.
- El creador del proyecto queda como `administrador_proyecto`.
- Un proyecto puede tener varios tableros.
- Nadie puede ver tableros de un proyecto si no es miembro, salvo `SuperAdministrador`.
- El administrador del proyecto puede agregar usuarios comunes como miembros.
- Las columnas de cada tablero son fijas y se crean automaticamente:
  - `SOLICITADO`
  - `EN PROGRESO`
  - `EN REVISION`
  - `COMPLETADO`
- Las tareas solo pueden asignarse a usuarios que pertenecen al proyecto.

## Endpoints Principales

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Usuarios:

- `GET /api/usuarios`
- `GET /api/usuarios/{usuario_id}`
- `PUT /api/usuarios/{usuario_id}`

Proyectos:

- `POST /api/proyectos`
- `GET /api/proyectos`
- `GET /api/proyectos/{proyecto_id}`
- `GET /api/proyectos/{proyecto_id}/miembros`
- `POST /api/proyectos/{proyecto_id}/miembros`

Tableros:

- `POST /api/proyectos/{proyecto_id}/tableros`
- `GET /api/proyectos/{proyecto_id}/tableros`
- `GET /api/tableros`
- `GET /api/tableros/{tablero_id}`
- `PUT /api/tableros/{tablero_id}`
- `GET /api/tableros/{tablero_id}/columnas`

Tareas:

- `POST /api/tareas`
- `GET /api/tareas`
- `GET /api/tareas/{tarea_id}`
- `PUT /api/tareas/{tarea_id}`
- `POST /api/tareas/{tarea_id}/asignados`
- `DELETE /api/tareas/{tarea_id}`

## Flujo De Uso

1. Login como `superadmin@example.com` o registrar un usuario comun.
2. Un usuario comun crea un proyecto con `POST /api/proyectos`.
3. Ese usuario queda como `administrador_proyecto`.
4. Crea un tablero con `POST /api/proyectos/{proyecto_id}/tableros`.
5. El backend crea automaticamente las cuatro columnas fijas.
6. Agrega miembros con `POST /api/proyectos/{proyecto_id}/miembros`.
7. Crea tareas en columnas con `POST /api/tareas`.
8. Asigna tareas solo a usuarios miembros del proyecto.

## Verificar Reglas Reales

Ejecutar:

```powershell
python scripts/verify_vulnerabilities.py
```

El script valida:

- Usuario externo no ve proyectos ajenos.
- `SuperAdministrador` ve todos los proyectos.
- Crear tablero genera exactamente las 4 columnas fijas.
- Usuario externo no puede ver tableros de proyecto ajeno.
- Administrador de proyecto agrega miembros.
- Miembro agregado puede ver el tablero.
- Tarea puede asignarse a miembros del proyecto.
- Usuario no miembro no puede ser asignado.

Salida esperada:

```text
OK - Usuario externo no ve proyectos ajenos.
OK - SuperAdministrador ve todos los proyectos.
OK - Crear tablero genera exactamente las 4 columnas fijas.
OK - Usuario externo no puede ver tableros de proyecto ajeno.
OK - Administrador de proyecto agrega miembros.
OK - Miembro agregado puede ver el tablero.
OK - Tarea asignada a un miembro del proyecto.
OK - Usuario no miembro no puede ser asignado a tarea del proyecto.
```

La advertencia `InsecureKeyLengthWarning` puede aparecer porque el `JWT_SECRET` sigue siendo debil en `.env`.

## Levantar API

```powershell
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Nota Sobre El Frontend

El frontend anterior consumia tableros directamente. Ahora debe adaptarse al flujo:

```text
proyectos -> tableros -> columnas -> tareas
```

Hasta adaptar el frontend, prueba el backend desde Swagger, Postman o el script de verificacion.
