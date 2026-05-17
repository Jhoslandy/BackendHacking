# BackendHacking

Mini Kanban vulnerable construido con FastAPI, SQLAlchemy y PostgreSQL para una demostracion academica de API Hacking con Postman y Burp Suite.

El objetivo no es seguridad real. El objetivo es tener una API pequena, entendible y vulnerable para explicar fallas comunes en clase.

## Requisitos

- Python 3.11 o superior
- PostgreSQL
- Postman o Burp Suite para la demostracion

## Estructura

```text
BackendHacking/
|-- app/
|   |-- api/
|   |   `-- v1/endpoints/
|   |-- core/
|   |-- db/
|   |-- models/
|   |-- schemas/
|   `-- main.py
|-- alembic/
|   `-- versions/
|-- database/
|   `-- schema.sql
|-- migrations/
|   |-- 001_create_kanban_schema.sql
|   `-- 001_drop_kanban_schema.sql
|-- seeders/
|   `-- 001_seed_roles.sql
|-- scripts/
|   `-- verify_vulnerabilities.py
|-- alembic.ini
|-- .env.example
|-- README.md
`-- requirements.txt
```

## Levantar el proyecto

1. Crear y activar entorno virtual.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias.

```bash
pip install -r requirements.txt
```

3. Crear el archivo `.env`.

Windows:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

4. Configurar PostgreSQL en `.env`.

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=BDKANBAN
DB_USER=postgres
DB_PASSWORD=123456

JWT_SECRET=clave_insegura_demo
JWT_EXPIRES_IN=7d
```

5. Crear la base de datos `BDKANBAN`.

Puedes crearla desde pgAdmin o desde cualquier cliente de PostgreSQL. El proyecto ya no depende de tener `psql` instalado en la terminal para crear las tablas.

6. Probar la conexion a PostgreSQL.

```bash
python -m app.db.check_connection
```

Si este comando falla con `password failed`, el problema no es la migracion: el usuario o password del `.env` no coincide con PostgreSQL.

7. Ejecutar migraciones y seeders.

```bash
python -m alembic upgrade head
```

Este comando ejecuta:

- `migrations/001_create_kanban_schema.sql`
- `seeders/001_seed_roles.sql`

Roles iniciales:

- `Administrador`
- `Usuario_Regular`

8. Levantar la API.

```bash
uvicorn app.main:app --reload
```

Documentacion interactiva:

```text
http://127.0.0.1:8000/docs
```

## Flujo basico para probar

1. Registrar usuarios con `POST /api/auth/register`.
2. Iniciar sesion con `POST /api/auth/login`.
3. Copiar el token y usarlo como `Authorization: Bearer <token>`.
4. Crear tableros con `POST /api/tableros`.
5. Crear columnas con `POST /api/columnas`.
6. Crear tareas con `POST /api/tareas`.
7. Asignar usuarios con `POST /api/tareas/{tarea_id}/asignados`.

## Verificar vulnerabilidades

Antes de la exposicion puedes ejecutar una prueba automatica:

```bash
python scripts/verify_vulnerabilities.py
```

El script crea usuarios demo con emails unicos, inicia sesion, crea un tablero privado y verifica:

- BOLA / IDOR: un atacante lee un tablero de otro usuario cambiando el ID.
- Asignacion masiva: el backend acepta `rol_id=1` y `creador_id` desde el body.
- Exposicion de datos: `GET /api/usuarios` devuelve `password_hash`.

Salida esperada:

```text
OK - Registro acepto rol_id=1 y devolvio password_hash.
OK - Atacante pudo leer un tablero ajeno cambiando el ID.
OK - GET /api/usuarios expone password_hash y datos de usuarios.
OK - Tarea creada con creador_id manipulado desde el body.
```

Si aparece una advertencia sobre `InsecureKeyLengthWarning`, es esperada: el secreto JWT es debil a proposito para la demo academica.

## Endpoints principales

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/usuarios`
- `GET /api/usuarios/{usuario_id}`
- `PUT /api/usuarios/{usuario_id}`
- `POST /api/tableros`
- `GET /api/tableros`
- `GET /api/tableros/{tablero_id}`
- `PUT /api/tableros/{tablero_id}`
- `POST /api/columnas`
- `GET /api/tableros/{tablero_id}/columnas`
- `PUT /api/columnas/{columna_id}`
- `POST /api/tareas`
- `GET /api/tareas`
- `GET /api/tareas/{tarea_id}`
- `PUT /api/tareas/{tarea_id}`
- `POST /api/tareas/{tarea_id}/asignados`
- `DELETE /api/tareas/{tarea_id}`

## Migraciones

El proyecto usa Alembic como runner de migraciones, pero la logica SQL esta separada en carpetas claras:

- `migrations/`: creacion o cambios de estructura.
- `seeders/`: datos iniciales.

Crear o actualizar tablas:

```bash
python -m alembic upgrade head
```

Ver migraciones disponibles:

```bash
python -m alembic history
```

Volver atras una migracion:

```bash
python -m alembic downgrade -1
```

El archivo `database/schema.sql` queda como referencia manual, pero el flujo recomendado es Alembic.

## Problemas de conexion

Si ves un error similar a:

```text
FATAL: la autentificacion password fallo para el usuario "postgrest"
```

PostgreSQL si esta respondiendo, pero rechazo las credenciales. Revisa:

- Que `DB_USER` en `.env` sea el usuario real de PostgreSQL.
- Que `DB_PASSWORD` sea la contrasena real.
- Que no estes usando `postgrest` si tu usuario real es `postgres`.
- Que `python -m app.db.check_connection` conecte antes de migrar.

En este proyecto `.env` tiene prioridad sobre variables del sistema para evitar que una variable vieja como `DB_USER=postgrest` pise la configuracion del archivo.

## Vulnerabilidades intencionales

Esta seccion esta pensada para una demostracion manual en Postman o Burp Suite. Usa `http://127.0.0.1:8000` como base URL.

### Preparacion para Postman

Registra una victima:

```http
POST /api/auth/register
```

```json
{
  "nombre": "Victima",
  "email": "victima@example.com",
  "password": "123456",
  "rol_id": 2
}
```

Registra un atacante:

```http
POST /api/auth/register
```

```json
{
  "nombre": "Atacante",
  "email": "atacante@example.com",
  "password": "123456",
  "rol_id": 2
}
```

Inicia sesion con ambos usuarios:

```http
POST /api/auth/login
```

```json
{
  "email": "atacante@example.com",
  "password": "123456"
}
```

Copia el `access_token` y usalo en las peticiones protegidas:

```http
Authorization: Bearer TOKEN_AQUI
```

### 1. BOLA / IDOR

Codigo relevante:

- `app/api/v1/endpoints/users.py`
- `app/api/v1/endpoints/boards.py`
- `app/api/v1/endpoints/tasks.py`

Como explotarlo:

1. Con token de la victima, crea un tablero.

```http
POST /api/tableros
```

```json
{
  "nombre": "Tablero privado de Victima",
  "descripcion": "No deberia verlo otro usuario",
  "propietario_id": 1
}
```

2. Copia el `id` del tablero creado.
3. Cambia al token del atacante.
4. Consulta el tablero de la victima cambiando el ID en la URL.

```http
GET /api/tableros/1
```

Resultado vulnerable:

- La API responde `200 OK`.
- Devuelve el tablero aunque el token sea del atacante.
- El backend no valida que `propietario_id` coincida con el usuario autenticado.

En un sistema seguro:

- El backend deberia verificar que el recurso pertenece al usuario autenticado.
- No deberia confiar solo en IDs enviados por URL o body.

### 2. Asignacion masiva

Codigo relevante:

- `POST /api/auth/register` acepta `rol_id`.
- `PUT /api/usuarios/{usuario_id}` acepta `rol_id` y `password_hash`.
- `POST /api/tableros` acepta `propietario_id`.
- `POST /api/tareas` acepta `creador_id`.

Como explotarlo:

Registro con rol manipulado:

```http
POST /api/auth/register
```

```json
{
  "nombre": "Alumno Admin",
  "email": "alumno.admin@example.com",
  "password": "123456",
  "rol_id": 1
}
```

Resultado vulnerable:

- El usuario queda con `rol_id=1`.
- El cliente controla el rol desde el body.

Tarea con creador manipulado:

```http
POST /api/tareas
```

```json
{
  "titulo": "Tarea creada por atacante",
  "descripcion": "El atacante envia creador_id ajeno",
  "columna_id": 1,
  "creador_id": 1,
  "asignados_ids": [1, 2]
}
```

Resultado vulnerable:

- La API acepta `creador_id`.
- El atacante puede hacer que la tarea parezca creada por otro usuario.

En un sistema seguro:

- El backend deberia ignorar campos sensibles enviados por el cliente.
- Roles, propietario y creador deberian salir del usuario autenticado o de reglas internas.

### 3. Exposicion excesiva de datos

Codigo relevante:

- `UsuarioExpuesto` en `app/schemas/user.py`.
- Respuestas de usuarios, tableros y tareas.

Como explotarlo:

1. Inicia sesion.
2. Llama `GET /api/usuarios`.

```http
GET /api/usuarios
```

Resultado vulnerable:

```json
[
  {
    "id": 1,
    "nombre": "Victima",
    "email": "victima@example.com",
    "rol_id": 2,
    "creado_en": "2026-05-17T00:00:00",
    "password_hash": "123456",
    "rol": {
      "id": 2,
      "nombre": "Usuario_Regular"
    }
  }
]
```

La respuesta incluye `password_hash`, `rol_id` y datos internos del rol.

En un sistema seguro:

- Nunca se deberia devolver `password_hash`.
- Las respuestas deberian usar schemas publicos con datos minimos.

### 4. Autenticacion debil

Codigo relevante:

- `app/core/security.py`
- `.env`

Como explotarlo:

1. Observa que `JWT_SECRET=clave_insegura_demo`.
2. El token dura `7d`.
3. Con Burp Suite se puede capturar el token y reutilizarlo durante mucho tiempo.

En un sistema seguro:

- El secreto JWT deberia ser fuerte y privado.
- La expiracion deberia ser corta.
- Las contrasenas no deberian guardarse en texto plano.
- El backend deberia validar permisos en cada recurso.

## Nota academica

Este backend esta disenado para laboratorio local. No debe publicarse en internet ni usarse como base de un sistema real sin corregir las vulnerabilidades.
