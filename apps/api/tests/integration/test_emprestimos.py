import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.models.pessoa import Pessoa
from app.models.usuario import Usuario


async def _auth_headers_with_role(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
    suffix: str,
    papel: str,
) -> tuple[dict[str, str], str]:
    username = f"auth_{suffix}"
    senha = "securepass123"

    async with test_session_maker() as session:
        pessoa = Pessoa(nome=f"Auth {suffix}", email=f"auth.{suffix}@example.com")
        session.add(pessoa)
        await session.flush()
        pessoa_id = str(pessoa.id)

        usuario = Usuario(
            pessoa_id=pessoa.id,
            username=username,
            senha_hash=hash_password(senha),
            ativo=True,
            papel=papel,
        )
        session.add(usuario)
        await session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "senha": senha},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, pessoa_id


async def _auth_headers(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
    suffix: str,
) -> dict[str, str]:
    headers, _ = await _auth_headers_with_role(
        client,
        test_session_maker,
        suffix,
        "admin",
    )
    return headers


async def _create_livro(
    client: AsyncClient, headers: dict[str, str], titulo: str, isbn: str
) -> str:
    response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": titulo,
            "autor": "Test Author",
            "isbn": isbn,
            "ano_publicacao": 2024,
            "disponivel": True,
            "dias_emprestimo_padrao": 7,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_pessoa(
    client: AsyncClient,
    headers: dict[str, str],
    nome: str,
    email: str,
) -> str:
    response = await client.post(
        "/api/v1/pessoas",
        json={"nome": nome, "email": email},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_and_get_emprestimo(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "emp_create_get")

    livro_id = await _create_livro(client, headers, "Test Book", "9780001234567")
    pessoa_id = await _create_pessoa(
        client,
        headers,
        "Reader Name",
        "reader@example.com",
    )

    payload = {
        "pessoa_id": pessoa_id,
        "livro_id": livro_id,
    }

    create_response = await client.post(
        "/api/v1/emprestimos", json=payload, headers=headers
    )
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["pessoa_id"] == pessoa_id
    assert created["livro_id"] == livro_id
    assert created["ativo"] is True
    assert created["data_devolucao_real"] is None
    assert created["created_by"] is not None
    assert created["updated_by"] is not None

    emprestimo_id = created["id"]
    get_response = await client.get(
        f"/api/v1/emprestimos/{emprestimo_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == emprestimo_id


@pytest.mark.asyncio
async def test_list_emprestimos_with_pagination(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "emp_list")

    livro1_id = await _create_livro(client, headers, "Book 1", "9780002111111")
    livro2_id = await _create_livro(client, headers, "Book 2", "9780003222222")
    pessoa_id = await _create_pessoa(client, headers, "Reader", "reader2@example.com")

    # Create two loans
    await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa_id, "livro_id": livro1_id},
        headers=headers,
    )

    # Return the first loan
    loans_response = await client.get("/api/v1/emprestimos", headers=headers)
    first_loan_id = loans_response.json()["items"][0]["id"]
    await client.patch(
        f"/api/v1/emprestimos/{first_loan_id}/devolver",
        headers=headers,
    )

    # Create new pessoa for second loan
    pessoa2_id = await _create_pessoa(client, headers, "Reader2", "reader3@example.com")
    await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa2_id, "livro_id": livro2_id},
        headers=headers,
    )

    response = await client.get(
        "/api/v1/emprestimos",
        params={"ativo": True},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(item["ativo"] for item in body["items"])


@pytest.mark.asyncio
async def test_devolucao_emprestimo(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "emp_devolver")

    livro_id = await _create_livro(client, headers, "Book to Return", "9780004333333")
    pessoa_id = await _create_pessoa(client, headers, "Reader", "reader4@example.com")

    create_response = await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa_id, "livro_id": livro_id},
        headers=headers,
    )
    emprestimo_id = create_response.json()["id"]

    # Verify book is unavailable
    livro_check = await client.get(f"/api/v1/livros/{livro_id}")
    assert livro_check.json()["disponivel"] is False

    # Return the book
    devolucao_response = await client.patch(
        f"/api/v1/emprestimos/{emprestimo_id}/devolver",
        headers=headers,
    )
    assert devolucao_response.status_code == 200

    returned = devolucao_response.json()
    assert returned["ativo"] is False
    assert returned["data_devolucao_real"] is not None
    assert returned["updated_by"] is not None

    # Verify book is available again
    livro_check_after = await client.get(f"/api/v1/livros/{livro_id}")
    assert livro_check_after.json()["disponivel"] is True


@pytest.mark.asyncio
async def test_cannot_borrow_unavailable_book(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "emp_unavailable")

    livro_id = await _create_livro(client, headers, "Unavailable Book", "9780005444444")
    pessoa1_id = await _create_pessoa(client, headers, "Reader1", "reader5@example.com")
    pessoa2_id = await _create_pessoa(client, headers, "Reader2", "reader6@example.com")

    # First person borrows the book
    await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa1_id, "livro_id": livro_id},
        headers=headers,
    )

    # Second person tries to borrow the same book
    response = await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa2_id, "livro_id": livro_id},
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "livro_indisponivel"


@pytest.mark.asyncio
async def test_cannot_borrow_two_books_simultaneously(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "emp_two_books")

    livro1_id = await _create_livro(client, headers, "Book 1", "9780006555555")
    livro2_id = await _create_livro(client, headers, "Book 2", "9780007666666")
    pessoa_id = await _create_pessoa(client, headers, "Reader", "reader7@example.com")

    # First borrow
    await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa_id, "livro_id": livro1_id},
        headers=headers,
    )

    # Try to borrow second book
    response = await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa_id, "livro_id": livro2_id},
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "emprestimo_ativo_existente"


@pytest.mark.asyncio
async def test_cannot_return_inactive_loan(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "emp_return_inactive")

    livro_id = await _create_livro(client, headers, "Test Book", "9780008777777")
    pessoa_id = await _create_pessoa(client, headers, "Reader", "reader8@example.com")

    create_response = await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa_id, "livro_id": livro_id},
        headers=headers,
    )
    emprestimo_id = create_response.json()["id"]

    # First return
    await client.patch(
        f"/api/v1/emprestimos/{emprestimo_id}/devolver",
        headers=headers,
    )

    # Try to return again
    response = await client.patch(
        f"/api/v1/emprestimos/{emprestimo_id}/devolver",
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "emprestimo_nao_ativo"


@pytest.mark.asyncio
async def test_leitor_can_only_access_own_emprestimos(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    admin_headers = await _auth_headers(client, test_session_maker, "emp_scope_admin")
    leitor_headers, leitor_pessoa_id = await _auth_headers_with_role(
        client,
        test_session_maker,
        "emp_scope_reader",
        "leitor",
    )

    livro1_id = await _create_livro(
        client,
        admin_headers,
        "Scope Book 1",
        "9781000000001",
    )
    livro2_id = await _create_livro(
        client,
        admin_headers,
        "Scope Book 2",
        "9781000000002",
    )
    outra_pessoa_id = await _create_pessoa(
        client,
        admin_headers,
        "Outra Pessoa",
        "outra.scope@example.com",
    )

    own_loan_response = await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": leitor_pessoa_id, "livro_id": livro1_id},
        headers=admin_headers,
    )
    own_loan_id = own_loan_response.json()["id"]

    other_loan_response = await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": outra_pessoa_id, "livro_id": livro2_id},
        headers=admin_headers,
    )
    other_loan_id = other_loan_response.json()["id"]

    list_response = await client.get("/api/v1/emprestimos", headers=leitor_headers)
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == own_loan_id
    assert items[0]["pessoa_id"] == leitor_pessoa_id

    filtered_response = await client.get(
        "/api/v1/emprestimos",
        params={"pessoa_id": outra_pessoa_id},
        headers=leitor_headers,
    )
    assert filtered_response.status_code == 403
    assert filtered_response.json()["detail"] == "Leitor can only access own loans"

    own_get_response = await client.get(
        f"/api/v1/emprestimos/{own_loan_id}",
        headers=leitor_headers,
    )
    assert own_get_response.status_code == 200

    forbidden_get_response = await client.get(
        f"/api/v1/emprestimos/{other_loan_id}",
        headers=leitor_headers,
    )
    assert forbidden_get_response.status_code == 403
    assert forbidden_get_response.json()["detail"] == "Leitor can only access own loans"
