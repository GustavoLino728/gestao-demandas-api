import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from app.config import settings
from app.core.exceptions import AppException
from app.core.middleware import register_middlewares, logging_middleware
from app.domain.users.router import router as users_router

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Metadados das tags — aparecem como seções no Swagger
TAGS_METADATA = [
    {"name": "Health", "description": "Status da aplicação"},
    {"name": "Auth", "description": "Login, logout e refresh de token"},
    {"name": "Users", "description": "Gestão de usuários"},
    {"name": "Boards", "description": "Quadros Kanban"},
    {"name": "Cards", "description": "Cards e demandas"},
    {"name": "CardsHistory", "description": "Históricos de Alteração dos Cards"},
    {"name": "Audit", "description": "Histórico de alterações"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("demand_manager").info("🚀 Gestão de Demandas - API iniciado")
    yield
    logging.getLogger("demand_manager").info("🛑 Gestão de Demandas - API encerrado")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gestão de Demandas - API",
        version="1.0.0",
        debug=settings.app_debug,
        lifespan=lifespan,
        openapi_tags=TAGS_METADATA,
        # Swagger/ReDoc só disponível fora de produção
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    register_middlewares(app)
    app.middleware("http")(logging_middleware)

    app.include_router(users_router, prefix="/api/v1")


    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.code, content={"detail": exc.message})

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "env": settings.app_env}

    return app


def custom_openapi(app: FastAPI):
    """Configura o schema OpenAPI com suporte a Bearer JWT no Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=(
            "## Gestão de Demandas - API\n\n"
            "Sistema de gestão de demandas no estilo Trello.\n\n"
            "### Autenticação\n"
            "Use o endpoint `/api/v1/auth/login` para obter o token JWT. "
            "Clique em **Authorize** e cole o token no campo `Bearer`."
        ),
        routes=app.routes,
        tags=TAGS_METADATA,
    )

    schema.setdefault("components", {})

    # Adiciona o esquema de segurança Bearer JWT
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    # Aplica autenticação globalmente em todos os endpoints
    schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app = create_app()
app.openapi = lambda: custom_openapi(app)