import psycopg
from psycopg import OperationalError

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    print(f"Host: {settings.DB_HOST}")
    print(f"Puerto: {settings.DB_PORT}")
    print(f"Base de datos: {settings.DB_NAME}")
    print(f"Usuario: {settings.DB_USER}")

    try:
        with psycopg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user")
                database, user = cursor.fetchone()
                print(f"Conexion OK: database={database}, user={user}")
    except OperationalError as error:
        print("Conexion fallida.")
        print(str(error))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
