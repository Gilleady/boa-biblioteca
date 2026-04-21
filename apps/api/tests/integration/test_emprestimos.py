import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, suffix: str) -> dict[str, str]:
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": f"Auth {suffix}", "email": f"auth.{suffix}@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    usuario_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": f"auth_{suffix}",
            "senha": "securepass123",
            "ativo": True,
        },
    )
    assert usuario_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": f"auth_{suffix}", "senha": "securepass123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


async def _create_pessoa(client: AsyncClient, nome: str, email: str) -> str:
    response = await client.post(
        "/api/v1/pessoas",
        json={"nome": nome, "email": email},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_and_get_emprestimo(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "emp_create_get")

    livro_id = await _create_livro(client, headers, "Test Book", "9780001234567")
    pessoa_id = await _create_pessoa(client, "Reader Name", "reader@example.com")

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

    emprestimo_id = created["id"]
    get_response = await client.get(f"/api/v1/emprestimos/{emprestimo_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == emprestimo_id


@pytest.mark.asyncio
async def test_list_emprestimos_with_pagination(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "emp_list")

    livro1_id = await _create_livro(client, headers, "Book 1", "9780002111111")
    livro2_id = await _create_livro(client, headers, "Book 2", "9780003222222")
    pessoa_id = await _create_pessoa(client, "Reader", "reader2@example.com")

    # Create two loans
    await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa_id, "livro_id": livro1_id},
        headers=headers,
    )

    # Return the first loan
    loans_response = await client.get("/api/v1/emprestimos")
    first_loan_id = loans_response.json()["items"][0]["id"]
    await client.patch(
        f"/api/v1/emprestimos/{first_loan_id}/devolver",
        headers=headers,
    )

    # Create new pessoa for second loan
    pessoa2_id = await _create_pessoa(client, "Reader2", "reader3@example.com")
    await client.post(
        "/api/v1/emprestimos",
        json={"pessoa_id": pessoa2_id, "livro_id": livro2_id},
        headers=headers,
    )

    response = await client.get("/api/v1/emprestimos", params={"ativo": True})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(item["ativo"] for item in body["items"])


@pytest.mark.asyncio
async def test_devolucao_emprestimo(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "emp_devolver")

    livro_id = await _create_livro(client, headers, "Book to Return", "9780004333333")
    pessoa_id = await _create_pessoa(client, "Reader", "reader4@example.com")

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

    # Verify book is available again
    livro_check_after = await client.get(f"/api/v1/livros/{livro_id}")
    assert livro_check_after.json()["disponivel"] is True


@pytest.mark.asyncio
async def test_cannot_borrow_unavailable_book(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "emp_unavailable")

    livro_id = await _create_livro(client, headers, "Unavailable Book", "9780005444444")
    pessoa1_id = await _create_pessoa(client, "Reader1", "reader5@example.com")
    pessoa2_id = await _create_pessoa(client, "Reader2", "reader6@example.com")

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
async def test_cannot_borrow_two_books_simultaneously(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "emp_two_books")

    livro1_id = await _create_livro(client, headers, "Book 1", "9780006555555")
    livro2_id = await _create_livro(client, headers, "Book 2", "9780007666666")
    pessoa_id = await _create_pessoa(client, "Reader", "reader7@example.com")

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
async def test_cannot_return_inactive_loan(client: AsyncClient) -> None:
    headers = await _auth_headers(client, "emp_return_inactive")

    livro_id = await _create_livro(client, headers, "Test Book", "9780008777777")
    pessoa_id = await _create_pessoa(client, "Reader", "reader8@example.com")

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
