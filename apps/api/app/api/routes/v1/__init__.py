from fastapi import APIRouter

from app.api.routes.v1.livros import router as livros_router

router = APIRouter()
router.include_router(livros_router)
