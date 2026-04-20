from fastapi import APIRouter

from app.api.routes.v1.livros import router as livros_router
from app.api.routes.v1.pessoas import router as pessoas_router
from app.api.routes.v1.usuarios import router as usuarios_router

router = APIRouter()
router.include_router(livros_router)
router.include_router(pessoas_router)
router.include_router(usuarios_router)
