from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.router import api_router
from app.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
