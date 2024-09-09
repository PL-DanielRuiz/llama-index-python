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


# Configurar el logger
logger = logging.getLogger("uvicorn")


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar la conexión del debugger (solo en desarrollo)
# if os.getenv("ENV", "dev") == "dev":
#     import debugpy
#     # Usa el puerto del entorno o un valor por defecto
#     debugpy_port = int(os.getenv("DEBUGPY_PORT", 5678))
#     debugpy.listen(("0.0.0.0", debugpy_port))
#     print(f"Esperando a que el debugger se conecte en el puerto {debugpy_port}...")
#     debugpy.wait_for_client()  # Pausa la ejecución hasta que el cliente del debugger se conecte
#     print("Debugger conectado")


# Crear la instancia de la aplicación FastAPI
app = FastAPI()


# Inicializar configuración y observabilidad
init_settings()
init_observability()


# Configurar CORS en entorno de desarrollo
environment = os.getenv("ENV", "prod")  # Por defecto es 'dev'
logger.info(f"Entorno: {environment}")


# MODO DE DESARROLLO
if environment == "dev":
    logger.setLevel(logging.DEBUG)

    # Permitir CORS para todos los orígenes en modo desarrollo
    logger.warning("[DEV] Running in development mode - allowing CORS for all origins")
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

else:
    # TODO: Configurar CORS en producción. Esto es temporal...
    logger.warning("[PROD] Running in development mode - allowing CORS for all origins")
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
        logger.info(f"Mounting static files from {directory} at {path}")
        app.mount(path, StaticFiles(directory=directory), name=f"{directory}")
    else:
        logger.warning(f"Directory {directory} does not exist. Static files not mounted.")


# Montar archivos de datos y herramientas
mount_static_files("data", "/api/files/data/")
mount_static_files("tool-output", "/api/files/tool-output")


# Incluir el enrutador de chat con el prefijo /api/chat
app.include_router(chat_router, prefix="/api/chat")


# Ejecutar la aplicación usando Uvicorn
if __name__ == "__main__":
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = True if environment == "dev" else False

    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload)
