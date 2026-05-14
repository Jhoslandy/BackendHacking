# Mi Backend con FastAPI

## Instalación

1. Clonar repositorio
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno: `source venv/bin/activate` (Linux/Mac) o `venv\Scripts\activate` (Windows)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Crear archivo `.env` con tus variables de entorno
6. Ejecutar: `uvicorn app.main:app --reload`

## Endpoints

- `GET /` - Ruta principal
- `GET /docs` - Documentación interactiva
