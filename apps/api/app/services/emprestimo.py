from __future__ import annotations

from typing import Literal
from uuid import UUID

from app.core.exceptions import AppError
from app.repositories.emprestimo import EmprestimoRepository
from app.repositories.livro import LivroRepository
from app.repositories.pessoa import PessoaRepository
from app.schemas.emprestimo import (
    EmprestimoCreate,
    EmprestimoListResponse,
    EmprestimoRead,
)
from app.schemas.livro import LivroUpdate


class EmprestimoService:
    def __init__(
        self,
        repository: EmprestimoRepository,
        livro_repository: LivroRepository,
        pessoa_repository: PessoaRepository,
    ) -> None:
        self._repository = repository
        self._livro_repository = livro_repository
        self._pessoa_repository = pessoa_repository

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        pessoa_id: UUID | None,
        ativo: bool | None,
        order_by: Literal["created_at", "data_emprestimo"],
        order_direction: Literal["asc", "desc"],
    ) -> EmprestimoListResponse:
        emprestimos, total = await self._repository.list(
            page=page,
            page_size=page_size,
            pessoa_id=pessoa_id,
            ativo=ativo,
            order_by=order_by,
            order_direction=order_direction,
        )

        return EmprestimoListResponse(
            items=[EmprestimoRead.model_validate(e) for e in emprestimos],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get(self, emprestimo_id: UUID) -> EmprestimoRead:
        emprestimo = await self._repository.get_by_id(emprestimo_id)
        if emprestimo is None:
            raise AppError(
                status_code=404,
                code="emprestimo_not_found",
                message="Emprestimo nao encontrado",
                details={"id": str(emprestimo_id)},
            )

        return EmprestimoRead.model_validate(emprestimo)

    async def create(
        self,
        payload: EmprestimoCreate,
        actor_id: UUID | None = None,
    ) -> EmprestimoRead:
        """
        Create a new loan with business rule validation:
        - Person must exist and be active
        - Book must exist and be available
        - Person cannot have another active loan
        """
        # Validate person exists and is active
        pessoa = await self._pessoa_repository.get_by_id(payload.pessoa_id)
        if pessoa is None:
            raise AppError(
                status_code=404,
                code="pessoa_not_found",
                message="Pessoa nao encontrada",
                details={"id": str(payload.pessoa_id)},
            )

        # Validate book exists and is available
        livro = await self._livro_repository.get_by_id(payload.livro_id)
        if livro is None:
            raise AppError(
                status_code=404,
                code="livro_not_found",
                message="Livro nao encontrado",
                details={"id": str(payload.livro_id)},
            )

        if not livro.disponivel:
            raise AppError(
                status_code=409,
                code="livro_indisponivel",
                message="Livro nao esta disponivel para emprestimo",
                details={"livro_id": str(payload.livro_id)},
            )

        # Validate person doesn't have another active loan
        active_loan = await self._repository.get_active_by_pessoa(payload.pessoa_id)
        if active_loan is not None:
            raise AppError(
                status_code=409,
                code="emprestimo_ativo_existente",
                message="Pessoa ja possui um emprestimo ativo",
                details={"pessoa_id": str(payload.pessoa_id)},
            )

        # Create loan
        emprestimo = await self._repository.create(
            pessoa_id=payload.pessoa_id,
            livro_id=payload.livro_id,
            dias_emprestimo=livro.dias_emprestimo_padrao or 7,
            actor_id=actor_id,
        )

        # Mark book as unavailable
        await self._livro_repository.update(
            livro,
            LivroUpdate(disponivel=False),
        )

        return EmprestimoRead.model_validate(emprestimo)

    async def devolucao(
        self,
        emprestimo_id: UUID,
        actor_id: UUID | None = None,
    ) -> EmprestimoRead:
        """
        Mark a loan as returned:
        - Loan must exist and be active
        - Mark as returned with current date
        - Mark book as available again
        """
        emprestimo = await self._repository.get_by_id(emprestimo_id)
        if emprestimo is None:
            raise AppError(
                status_code=404,
                code="emprestimo_not_found",
                message="Emprestimo nao encontrado",
                details={"id": str(emprestimo_id)},
            )

        if not emprestimo.ativo:
            raise AppError(
                status_code=409,
                code="emprestimo_nao_ativo",
                message="Emprestimo nao esta ativo",
                details={"id": str(emprestimo_id)},
            )

        # Mark as returned
        returned = await self._repository.devolucao(emprestimo, actor_id=actor_id)

        # Mark book as available again
        livro = await self._livro_repository.get_by_id(emprestimo.livro_id)
        if livro:
            await self._livro_repository.update(
                livro,
                LivroUpdate(disponivel=True),
            )

        return EmprestimoRead.model_validate(returned)
