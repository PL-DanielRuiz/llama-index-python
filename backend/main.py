import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.api.routers.chat import chat_router
from app.settings import init_settings
from app.observability import init_observability

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar la conexión del debugger (solo en desarrollo)
if os.getenv("ENVIRONMENT", "dev") == "dev":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Esperando a que el debugger se conecte...")
    debugpy.wait_for_client()  # Pausa la ejecución hasta que el cliente del debugger se conecte
    print("Debugger conectado")

# Crear la instancia de la aplicación FastAPI
app = FastAPI()

# Inicializar configuración y observabilidad
init_settings()
init_observability()

# Configurar CORS en entorno de desarrollo
environment = os.getenv("ENVIRONMENT", "dev")  # Por defecto es 'dev'
code_space = os.getenv("CODESPACE_NAME")  # Obtener el nombre del Codespace si está definido
github_api = os.getenv("NEXT_PUBLIC_CHAT_API")  # Obtener el formato de la API de Codespaces

if environment == "dev":
    logger = logging.getLogger("uvicorn")

    if code_space and github_api:
        logger.warning("Modo desarrollo y Codespaces - permitiendo CORS para orígenes de Codespaces")
        origin_8000 = github_api.replace("/api/chat", "")
        origin_8000 = origin_8000.replace("${CODESPACE_NAME}", f"{code_space}")
        origin_3000 = origin_8000.replace("8000", "3000")
        origins = [origin_8000, origin_3000]
    else:
        logger.warning("Modo desarrollo - permitiendo CORS para todos los orígenes")
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Redirigir a la página de documentación al acceder a la URL base
    @app.get("/")
    async def redirect_to_docs():
        return RedirectResponse(url="/docs")


# Montar archivos estáticos si los directorios existen
def mount_static_files(directory, path):
    if os.path.exists(directory):
        app.mount(path, StaticFiles(directory=directory), name=f"{directory}-static")


# Montar archivos de datos y herramientas
mount_static_files("data", "/api/files/data")
mount_static_files("tool-output", "/api/files/tool-output")

# Incluir el enrutador de chat con el prefijo /api/chat
app.include_router(chat_router, prefix="/api/chat")

# Ejecutar la aplicación usando Uvicorn
if __name__ == "__main__":
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = True if environment == "dev" else False

    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload)
