from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.master_data import router as master_data_router
from app.routers.chat import router as chat_router
from app.routers.dashboard import router as dashboard_router
from app.routers.job_title_roles import router as job_title_roles_router
from app.routers.debug import router as debug_router
from app.routers.admin import router as admin_router
from app.routers.stress_test import router as stress_test_router
from app.routers.user_preferences import router as user_preferences_router
from app.routers.prompts import router as prompts_router
from app.routers.e42_evaluation import router as e42_evaluation_router
import os
import logging
import asyncio

# Configure logging para aparecer no console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log startup info
logger.info("[main] STARTING LUZ BACKEND")
print("🚀 STARTING LUZ BACKEND")


tags_metadata = [
    {
        "name": "documents",
        "description": "Operações de ingestão e gerenciamento de documentos. Upload, preview, confirmação, listagem, exclusão."
    },
    {
        "name": "auth",
        "description": "Autenticação com Entra ID e gerenciamento de sessão. Login, logout, renovação de token."
    },
    {
        "name": "master-data",
        "description": "Dados mestres do sistema. Localizações, cargos, categorias para filtro semântico."
    },
    {
        "name": "chat",
        "description": "Chat com LLM Server. Perguntas, histórico de conversas, gerenciamento de sessões."
    },
    {
        "name": "dashboard",
        "description": "Dashboard e análise de conversas. Resumo de métricas, dados detalhados, export."
    },
]

app = FastAPI(
    title="Secure Document & Identity Platform",
    version="1.0.0",
    description="Azure-only secure document management, identity authentication, and master data service",
    openapi_tags=tags_metadata,
    redirect_slashes=False  # Desabilita redirect automático de trailing slash
)

# CORS Configuration - Allow frontend requests
# Em desenvolvimento: Allow localhost:4200
# Em produção: Configure as orígems específicas
origins = [
    "http://localhost:4200",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://peoplechatbot-dev-latam001-a6etf8dwgybtb0eu.brazilsouth-01.azurewebsites.net"
]

# Add CORS origins from environment if specified
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    origins.extend(cors_origins_env.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)


@app.get("/")
def root():
    """Secure Document & Identity Platform"""
    return {
        "service": "Secure Document & Identity Platform",
        "version": "1.0.0",
        "description": "Azure-only: secure document management with identity authentication and master data",
        "endpoints": {
            "documents": "/api/v1/documents",
            "auth": "/api/v1/login",
            "master_data": "/api/v1/master-data",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health_check():
    """Simple health check - app is running"""
    return {"status": "healthy", "service": "luz-backend"}


@app.get("/health/ready")
def readiness_check():
    """Readiness check - all critical services available"""
    try:
        # Just check if app is loaded
        # Full connectivity checks can happen in separate endpoint
        return {"status": "ready", "service": "luz-backend"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e)}


# Exception handler para erros de validação do Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Log detalhado de erros de validação para debug.
    Pydantic retorna 422 quando a validação falha.
    """
    logger.error(f"[validation_exception_handler] Validation failed for {request.method} {request.url.path}")
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]
        input_val = error.get("input", "N/A")
        logger.error(f"   Field: {field}, Error: {msg}, Input: {input_val}")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


# Include routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(master_data_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(job_title_roles_router)
app.include_router(admin_router)
app.include_router(stress_test_router)
app.include_router(user_preferences_router)
app.include_router(prompts_router)
app.include_router(e42_evaluation_router)


# Background tasks
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    logger.info("[startup_event] Starting background tasks...")
    
    # Iniciar cleanup de uploads temporários expirados
    from app.tasks.cleanup_temp_uploads import start_cleanup_task
    asyncio.create_task(start_cleanup_task())
    
    logger.info("[startup_event] Background tasks initialized")
