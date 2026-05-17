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


def _register_user(nombre: str, email: str, password: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "nombre": nombre,
            "email": email,
            "password": password,
        },
    )
    _assert_status(response, 200, f"Registro de {email}")
    return response.json()


def _login(email: str, password: str) -> tuple[str, dict]:
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    _assert_status(response, 200, f"Login de {email}")
    data = response.json()
    return data["access_token"], data["usuario"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    suffix = uuid4().hex[:8]
    password = "123456"

    print("Validando reglas reales de acceso...")
    super_token, superadmin = _login("superadmin@example.com", password)

    owner = _register_user("Admin Proyecto", f"owner_{suffix}@example.com", password)
    member = _register_user("Miembro Proyecto", f"member_{suffix}@example.com", password)
    outsider = _register_user("Usuario Externo", f"outsider_{suffix}@example.com", password)

    owner_token, _ = _login(owner["email"], password)
    member_token, _ = _login(member["email"], password)
    outsider_token, _ = _login(outsider["email"], password)

    project_response = client.post(
        "/api/proyectos",
        headers=_auth_headers(owner_token),
        json={
            "nombre": f"Proyecto privado {suffix}",
            "descripcion": "Proyecto creado por usuario comun",
        },
    )
    _assert_status(project_response, 200, "Crear proyecto")
    project = project_response.json()

    outsider_projects = client.get("/api/proyectos", headers=_auth_headers(outsider_token))
    _assert_status(outsider_projects, 200, "Listar proyectos de externo")
    assert all(item["id"] != project["id"] for item in outsider_projects.json())
    print("OK - Usuario externo no ve proyectos ajenos.")

    super_projects = client.get("/api/proyectos", headers=_auth_headers(super_token))
    _assert_status(super_projects, 200, "Superadmin lista proyectos")
    assert any(item["id"] == project["id"] for item in super_projects.json())
    print("OK - SuperAdministrador ve todos los proyectos.")

    board_response = client.post(
        f"/api/proyectos/{project['id']}/tableros",
        headers=_auth_headers(owner_token),
        json={
            "nombre": "Tablero principal",
            "descripcion": "Tablero con columnas fijas",
        },
    )
    _assert_status(board_response, 200, "Crear tablero")
    board = board_response.json()
    column_names = [column["nombre"] for column in sorted(board["columnas"], key=lambda item: item["orden"])]
    assert column_names == ["SOLICITADO", "EN PROGRESO", "EN REVISION", "COMPLETADO"]
    print("OK - Crear tablero genera exactamente las 4 columnas fijas.")

    outsider_board = client.get(f"/api/tableros/{board['id']}", headers=_auth_headers(outsider_token))
    _assert_status(outsider_board, 403, "Externo no puede ver tablero ajeno")
    print("OK - Usuario externo no puede ver tableros de proyecto ajeno.")

    add_member = client.post(
        f"/api/proyectos/{project['id']}/miembros",
        headers=_auth_headers(owner_token),
        json={
            "usuario_id": member["id"],
            "subrol": "miembro",
        },
    )
    _assert_status(add_member, 200, "Agregar miembro")
    print("OK - Administrador de proyecto agrega miembros.")

    member_board = client.get(f"/api/tableros/{board['id']}", headers=_auth_headers(member_token))
    _assert_status(member_board, 200, "Miembro puede ver tablero")
    print("OK - Miembro agregado puede ver el tablero.")

    column_id = board["columnas"][0]["id"]
    task_response = client.post(
        "/api/tareas",
        headers=_auth_headers(owner_token),
        json={
            "titulo": "Tarea asignada a miembro",
            "descripcion": "Debe aceptar solo miembros del proyecto",
            "columna_id": column_id,
            "asignados_ids": [member["id"]],
        },
    )
    _assert_status(task_response, 200, "Crear tarea asignada a miembro")
    task = task_response.json()
    assert task["creador_id"] == owner["id"]
    print("OK - Tarea asignada a un miembro del proyecto.")

    bad_assignment = client.post(
        f"/api/tareas/{task['id']}/asignados",
        headers=_auth_headers(owner_token),
        json={"usuarios_ids": [outsider["id"]]},
    )
    _assert_status(bad_assignment, 400, "No asignar externo")
    print("OK - Usuario no miembro no puede ser asignado a tarea del proyecto.")

    print("\nResultado: reglas reales verificadas correctamente.")
    print(f"Superadmin: id={superadmin['id']}, email={superadmin['email']}")
    print(f"Proyecto: id={project['id']}")
    print(f"Tablero: id={board['id']}")


if __name__ == "__main__":
    main()
