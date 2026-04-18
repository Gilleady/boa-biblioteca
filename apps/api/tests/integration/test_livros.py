import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_livro(client: AsyncClient) -> None:
    payload = {
        "titulo": "Clean Architecture",
        "autor": "Robert C. Martin",
        "isbn": "9780134494166",
        "ano_publicacao": 2017,
        "disponivel": True,
    }

    create_response = await client.post("/api/v1/livros", json=payload)
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["titulo"] == payload["titulo"]
    assert created["isbn"] == payload["isbn"]

    livro_id = created["id"]
    get_response = await client.get(f"/api/v1/livros/{livro_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == livro_id


@pytest.mark.asyncio
async def test_list_livros_supports_pagination_and_filters(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Domain-Driven Design",
            "autor": "Eric Evans",
            "isbn": "9780321125217",
            "ano_publicacao": 2003,
            "disponivel": True,
        },
    )
    await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Refactoring",
            "autor": "Martin Fowler",
            "isbn": "9780201485677",
            "ano_publicacao": 1999,
            "disponivel": False,
        },
    )

    response = await client.get(
        "/api/v1/livros",
        params={"page": 1, "page_size": 1, "disponivel": True, "titulo": "Domain"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["titulo"] == "Domain-Driven Design"


@pytest.mark.asyncio
async def test_update_and_delete_livro(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "The Pragmatic Programmer",
            "autor": "Andrew Hunt",
            "isbn": "9780201616224",
            "ano_publicacao": 1999,
            "disponivel": True,
        },
    )
    livro_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/livros/{livro_id}",
        json={"disponivel": False, "autor": "Dave Thomas"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["disponivel"] is False
    assert updated["autor"] == "Dave Thomas"

    delete_response = await client.delete(f"/api/v1/livros/{livro_id}")
    assert delete_response.status_code == 204

    not_found_response = await client.get(f"/api/v1/livros/{livro_id}")
    assert not_found_response.status_code == 404
    assert not_found_response.json()["error"]["code"] == "livro_not_found"


@pytest.mark.asyncio
async def test_create_livro_returns_conflict_for_duplicate_isbn(
    client: AsyncClient,
) -> None:
    payload = {
        "titulo": "Patterns of Enterprise Application Architecture",
        "autor": "Martin Fowler",
        "isbn": "9780321127426",
        "ano_publicacao": 2002,
        "disponivel": True,
    }

    first_response = await client.post("/api/v1/livros", json=payload)
    assert first_response.status_code == 201

    second_response = await client.post("/api/v1/livros", json=payload)
    assert second_response.status_code == 409

    body = second_response.json()
    assert body["error"]["code"] == "livro_conflict"


@pytest.mark.asyncio
async def test_update_livro_with_empty_payload_returns_bad_request(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Working Effectively with Legacy Code",
            "autor": "Michael Feathers",
            "isbn": "9780131177055",
            "ano_publicacao": 2004,
            "disponivel": True,
        },
    )
    livro_id = create_response.json()["id"]

    response = await client.patch(f"/api/v1/livros/{livro_id}", json={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"


@pytest.mark.asyncio
async def test_validation_error_payload_shape(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "",
            "autor": "Autor Valido",
            "isbn": "123",
            "ano_publicacao": 2025,
            "disponivel": True,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed"
    assert isinstance(body["error"]["details"], list)
