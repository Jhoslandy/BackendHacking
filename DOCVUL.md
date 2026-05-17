# DOCVUL - Guia de vulnerabilidades del mini Kanban

Este backend fue dejado vulnerable de forma intencional para una demostracion academica de API Hacking con Postman y Burp Suite.

Base URL local:

```text
http://127.0.0.1:8000/api
```

Usuario inicial:

```text
email: superadmin@example.com
password: 123456
```

Todas las pruebas autenticadas usan:

```http
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

## 1. Autenticacion debil

### Donde esta

Archivos:

- `app/api/v1/endpoints/auth.py`
- `app/core/security.py`

### Como funciona

La autenticacion existe, pero es deliberadamente debil:

- Las passwords se guardan y comparan como texto simple en `password_hash`.
- El JWT usa `HS256` con una clave de demo debil desde `.env`.
- El backend confia en el campo `user_id` del token.

### Prueba con Postman

Login:

```http
POST /api/auth/login
```

Body:

```json
{
  "email": "superadmin@example.com",
  "password": "123456"
}
```

Respuesta esperada:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "email": "superadmin@example.com"
  }
}
```

### Prueba con Burp Suite

1. Iniciar sesion desde el frontend.
2. Interceptar una peticion autenticada.
3. Observar el header `Authorization: Bearer <TOKEN>`.
4. Enviar el token a Repeater para reutilizarlo contra otros endpoints.

## 2. Exposicion excesiva de datos

### Donde esta

Endpoints:

- `GET /api/usuarios`
- `GET /api/proyectos/{proyecto_id}/miembros`
- `GET /api/tareas`
- `GET /api/tareas/{tarea_id}`
- `GET /api/solicitudes-movimiento`

### Como funciona

Algunos endpoints devuelven mas datos de los necesarios para la interfaz:

- Usuarios con `id`, `email`, `rol_id`, `rol` y `creado_en`.
- Miembros de proyecto con datos completos del usuario.
- Tareas con `creador` y `asignados`.
- Solicitudes con nombre de proyecto, tablero, usuario solicitante, columnas y estado.

Esto permite recolectar IDs y datos utiles para otros ataques.

### Pruebas con Postman

Listar usuarios:

```http
GET /api/usuarios
```

Listar miembros de un proyecto:

```http
GET /api/proyectos/1/miembros
```

Consultar tarea por ID:

```http
GET /api/tareas/1
```

## 3. BOLA / IDOR

### Donde esta

Endpoints vulnerables:

- `GET /api/proyectos/{proyecto_id}`
- `GET /api/proyectos/{proyecto_id}/miembros`
- `GET /api/proyectos/{proyecto_id}/tableros`
- `GET /api/tableros/{tablero_id}`
- `GET /api/tableros/{tablero_id}/columnas`
- `GET /api/tareas/{tarea_id}`
- `PUT /api/tareas/{tarea_id}`

### Como funciona

El sistema recibe un ID en la URL y devuelve o modifica el recurso sin validar correctamente si el usuario autenticado pertenece al proyecto o tablero.

### Escenario recomendado

1. Crear dos usuarios comunes: `usuario_a` y `usuario_b`.
2. Iniciar sesion como `usuario_a`.
3. Crear un proyecto, tablero y tarea.
4. Iniciar sesion como `usuario_b`.
5. Usar IDs del proyecto, tablero o tarea de `usuario_a`.

### Pruebas con Postman

Acceder a proyecto ajeno cambiando el ID:

```http
GET /api/proyectos/1
```

Listar miembros de proyecto ajeno:

```http
GET /api/proyectos/1/miembros
```

Listar tableros de proyecto ajeno:

```http
GET /api/proyectos/1/tableros
```

Consultar tablero ajeno:

```http
GET /api/tableros/1
```

Consultar columnas de tablero ajeno:

```http
GET /api/tableros/1/columnas
```

Consultar tarea ajena:

```http
GET /api/tareas/1
```

Modificar tarea ajena:

```http
PUT /api/tareas/1
```

Body:

```json
{
  "titulo": "Tarea modificada por IDOR"
}
```

### Prueba con Burp Suite

1. Abrir el frontend con un usuario comun.
2. Entrar a un proyecto o tablero propio.
3. Interceptar una peticion, por ejemplo:

```http
GET /api/proyectos/2
```

4. Cambiar el ID por otro:

```http
GET /api/proyectos/1
```

5. Enviar la peticion modificada.

## 4. Asignacion masiva

### Donde esta

Archivos:

- `app/schemas/project.py`
- `app/schemas/board.py`
- `app/schemas/task.py`
- `app/api/v1/endpoints/projects.py`
- `app/api/v1/endpoints/boards.py`
- `app/api/v1/endpoints/tasks.py`

### Como funciona

Los esquemas aceptan campos extra con `extra="allow"`, y algunos endpoints aplican esos campos si coinciden con atributos del modelo.

Esto permite enviar campos que el frontend no muestra.

### Prueba 1: crear proyecto con `creador_id` manipulado

```http
POST /api/proyectos
```

Body:

```json
{
  "nombre": "Proyecto con creador manipulado",
  "descripcion": "Demo de asignacion masiva",
  "creador_id": 1
}
```

Resultado esperado:

- El proyecto se crea.
- El campo `creador_id` puede quedar con el valor enviado en el body.

### Prueba 2: crear tablero en otro proyecto usando `proyecto_id`

Requisito:

- El usuario debe administrar al menos un proyecto propio.
- Se usa ese proyecto propio en la URL.
- En el body se fuerza otro `proyecto_id`.

```http
POST /api/proyectos/MI_PROYECTO_ID/tableros
```

Body:

```json
{
  "nombre": "Tablero inyectado",
  "descripcion": "Creado usando asignacion masiva",
  "proyecto_id": PROYECTO_VICTIMA_ID
}
```

Resultado esperado:

- La validacion se hace contra `MI_PROYECTO_ID`.
- Luego el body puede sobrescribir `proyecto_id`.
- El tablero puede terminar asociado a otro proyecto.

### Prueba 3: modificar campos no expuestos de una tarea

```http
PUT /api/tareas/1
```

Body:

```json
{
  "titulo": "Tarea modificada",
  "creador_id": 1
}
```

Resultado esperado:

- La tarea se actualiza.
- El body puede modificar atributos que el frontend no deberia controlar.

## 5. Relacion backend - frontend

El frontend mantiene el flujo funcional normal:

```text
Proyecto -> Tablero -> Tareas -> Solicitudes / Notificaciones
```

El frontend no necesita mostrar botones para explotar las vulnerabilidades. La demostracion se hace interceptando o repitiendo peticiones:

- Con Postman: cambiar IDs en URL y campos en JSON.
- Con Burp Suite: interceptar peticiones del frontend, modificar IDs o body, y reenviar.

Puntos utiles desde el frontend:

- El login entrega el token Bearer.
- La navegacion normal genera peticiones a proyectos, tableros, columnas, tareas y solicitudes.
- Burp puede modificar esas peticiones antes de enviarlas al backend.

## 6. Estado de las vulnerabilidades

| Vulnerabilidad | Estado | Principal punto de prueba |
| --- | --- | --- |
| BOLA / IDOR | Lista | Cambiar IDs en `/proyectos`, `/tableros`, `/tareas` |
| Asignacion masiva | Lista | Enviar campos extra en body JSON |
| Exposicion excesiva | Lista | Consultar usuarios, miembros, tareas y solicitudes |
| Autenticacion debil | Lista | Password simple, JWT debil y confianza en `user_id` |

## 7. Notas para la exposicion

- Usar datos pequenos y IDs visibles para que el ataque sea claro.
- Crear dos usuarios comunes ayuda a demostrar acceso cruzado.
- SuperAdministrador ayuda a preparar datos y ver todos los usuarios.
- No ejecutar herramientas de hardening antes de la demo porque podrian eliminar los escenarios vulnerables.
