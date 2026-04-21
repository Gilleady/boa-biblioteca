from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_exception_handlers
from app.api.router import api_router
from app.settings import get_settings

OPENAPI_TAGS = [
    {"name": "health", "description": "Health checks and service availability."},
    {
        "name": "auth",
        "description": "JWT authentication and current session endpoints.",
    },
    {"name": "livros", "description": "Book catalog operations."},
    {"name": "pessoas", "description": "Person records used by user accounts."},
    {"name": "usuarios", "description": "Application users and account management."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=OPENAPI_TAGS,
        servers=[
            {"url": "http://localhost:8000", "description": "Local development"},
            {"url": "https://api.boabiblioteca.com", "description": "Production"},
        ],
        swagger_ui_parameters={"persistAuthorization": True},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
