import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_usuario(client: AsyncClient) -> None:
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Base", "email": "pessoa.base@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    create_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": "pessoabase",
            "senha": "hash-123",
            "ativo": True,
        },
    )
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["pessoa_id"] == pessoa_id
    assert created["username"] == "pessoabase"
    assert "senha_hash" not in created

    usuario_id = created["id"]
    get_response = await client.get(f"/api/v1/usuarios/{usuario_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == usuario_id


@pytest.mark.asyncio
async def test_create_usuario_fails_if_pessoa_not_found(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": "f732ca0d-ea89-4b6d-84ad-ec18eea12c5f",
            "username": "sem_pessoa",
            "senha": "hash-404",
            "ativo": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "pessoa_not_found"


@pytest.mark.asyncio
async def test_create_usuario_conflict_for_duplicate_username(
    client: AsyncClient,
) -> None:
    pessoa_a_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa A", "email": "pessoa.a@example.com"},
    )
    pessoa_b_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa B", "email": "pessoa.b@example.com"},
    )

    pessoa_a_id = pessoa_a_response.json()["id"]
    pessoa_b_id = pessoa_b_response.json()["id"]

    first_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_a_id,
            "username": "duplicado",
            "senha": "hash-1",
            "ativo": True,
        },
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_b_id,
            "username": "duplicado",
            "senha": "hash-2",
            "ativo": True,
        },
    )
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "usuario_conflict"


@pytest.mark.asyncio
async def test_update_and_delete_usuario(client: AsyncClient) -> None:
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa U", "email": "pessoa.u@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    create_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": "usuario.u",
            "senha": "hash-u",
            "ativo": True,
        },
    )
    usuario_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={"ativo": False, "username": "usuario.u2"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["ativo"] is False
    assert updated["username"] == "usuario.u2"

    delete_response = await client.delete(f"/api/v1/usuarios/{usuario_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/usuarios/{usuario_id}")
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "usuario_not_found"


@pytest.mark.asyncio
async def test_list_usuarios_supports_filters(client: AsyncClient) -> None:
    pessoa_a_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Lista A", "email": "lista.a@example.com"},
    )
    pessoa_b_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Lista B", "email": "lista.b@example.com"},
    )

    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_a_response.json()["id"],
            "username": "alpha_user",
            "senha": "hash-a",
            "ativo": True,
        },
    )
    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_b_response.json()["id"],
            "username": "beta_user",
            "senha": "hash-b",
            "ativo": False,
        },
    )

    response = await client.get(
        "/api/v1/usuarios",
        params={"username": "alpha", "ativo": True, "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["username"] == "alpha_user"


@pytest.mark.asyncio
async def test_update_usuario_with_empty_payload_returns_bad_request(
    client: AsyncClient,
) -> None:
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Vazia", "email": "vazia@example.com"},
    )
    usuario_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_response.json()["id"],
            "username": "vazio",
            "senha": "hash-v",
            "ativo": True,
        },
    )
    usuario_id = usuario_response.json()["id"]

    response = await client.patch(f"/api/v1/usuarios/{usuario_id}", json={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"
