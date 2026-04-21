from app.api.routes.v1.auth import router as auth_router
from app.api.routes.v1.emprestimos import router as emprestimos_router
from app.api.routes.v1.livros import router as livros_router
from app.api.routes.v1.pessoas import router as pessoas_router
from app.api.routes.v1.usuarios import router as usuarios_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(auth_router)
router.include_router(emprestimos_router)
router.include_router(livros_router)
router.include_router(pessoas_router)
router.include_router(usuarios_router)
