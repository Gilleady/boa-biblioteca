import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_pessoa(client: AsyncClient) -> None:
    payload = {
        "nome": "Ada Lovelace",
        "email": "ada@example.com",
    }

    create_response = await client.post("/api/v1/pessoas", json=payload)
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["nome"] == payload["nome"]
    assert created["email"] == payload["email"]

    pessoa_id = created["id"]
    get_response = await client.get(f"/api/v1/pessoas/{pessoa_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == pessoa_id


@pytest.mark.asyncio
async def test_list_pessoas_supports_filters(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/pessoas",
        json={"nome": "Grace Hopper", "email": "grace@example.com"},
    )
    await client.post(
        "/api/v1/pessoas",
        json={"nome": "Alan Turing", "email": "alan@example.com"},
    )

    response = await client.get(
        "/api/v1/pessoas",
        params={"nome": "Grace", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["nome"] == "Grace Hopper"


@pytest.mark.asyncio
async def test_update_and_delete_pessoa(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Linus Torvalds", "email": "linus@example.com"},
    )
    pessoa_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/pessoas/{pessoa_id}",
        json={"nome": "Linus Benedict Torvalds"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome"] == "Linus Benedict Torvalds"

    delete_response = await client.delete(f"/api/v1/pessoas/{pessoa_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/pessoas/{pessoa_id}")
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "pessoa_not_found"


@pytest.mark.asyncio
async def test_create_pessoa_conflict_for_duplicate_email(client: AsyncClient) -> None:
    payload = {
        "nome": "Margaret Hamilton",
        "email": "margaret@example.com",
    }

    first_response = await client.post("/api/v1/pessoas", json=payload)
    assert first_response.status_code == 201

    second_response = await client.post("/api/v1/pessoas", json=payload)
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "pessoa_conflict"


@pytest.mark.asyncio
async def test_update_pessoa_with_empty_payload_returns_bad_request(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Guido van Rossum", "email": "guido@example.com"},
    )
    pessoa_id = create_response.json()["id"]

    response = await client.patch(f"/api/v1/pessoas/{pessoa_id}", json={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"
