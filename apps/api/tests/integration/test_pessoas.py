import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.models.pessoa import Pessoa
from app.models.usuario import Usuario


async def _seed_usuario(
    test_session_maker: async_sessionmaker[AsyncSession],
    *,
    username: str,
    senha: str,
    papel: str,
    email: str,
) -> None:
    async with test_session_maker() as session:
        pessoa = Pessoa(nome=f"Pessoa {username}", email=email)
        session.add(pessoa)
        await session.flush()

        usuario = Usuario(
            pessoa_id=pessoa.id,
            username=username,
            senha_hash=hash_password(senha),
            ativo=True,
            papel=papel,
        )
        session.add(usuario)
        await session.commit()


async def _auth_headers(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
    suffix: str,
    *,
    papel: str = "admin",
) -> dict[str, str]:
    username = f"pessoas_{suffix}"
    senha = "securepass123"
    await _seed_usuario(
        test_session_maker,
        username=username,
        senha=senha,
        papel=papel,
        email=f"pessoas.{suffix}@example.com",
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "senha": senha},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_get_pessoa(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "create_get")

    payload = {
        "nome": "Ada Lovelace",
        "email": "ada@example.com",
    }

    create_response = await client.post(
        "/api/v1/pessoas",
        json=payload,
        headers=headers,
    )
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["nome"] == payload["nome"]
    assert created["email"] == payload["email"]
    assert created["created_by"] is not None
    assert created["updated_by"] is not None

    pessoa_id = created["id"]
    get_response = await client.get(f"/api/v1/pessoas/{pessoa_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == pessoa_id


@pytest.mark.asyncio
async def test_list_pessoas_supports_filters(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "list_filters")

    await client.post(
        "/api/v1/pessoas",
        json={"nome": "Grace Hopper", "email": "grace@example.com"},
        headers=headers,
    )
    await client.post(
        "/api/v1/pessoas",
        json={"nome": "Alan Turing", "email": "alan@example.com"},
        headers=headers,
    )

    response = await client.get(
        "/api/v1/pessoas",
        params={"nome": "Grace", "page": 1, "page_size": 10},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["nome"] == "Grace Hopper"


@pytest.mark.asyncio
async def test_update_and_delete_pessoa(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "update_delete")

    create_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Linus Torvalds", "email": "linus@example.com"},
        headers=headers,
    )
    pessoa_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/pessoas/{pessoa_id}",
        json={"nome": "Linus Benedict Torvalds"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome"] == "Linus Benedict Torvalds"
    assert update_response.json()["updated_by"] is not None

    delete_response = await client.delete(
        f"/api/v1/pessoas/{pessoa_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/pessoas/{pessoa_id}", headers=headers)
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "pessoa_not_found"


@pytest.mark.asyncio
async def test_create_pessoa_conflict_for_duplicate_email(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "conflict")

    payload = {
        "nome": "Margaret Hamilton",
        "email": "margaret@example.com",
    }

    first_response = await client.post(
        "/api/v1/pessoas",
        json=payload,
        headers=headers,
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/pessoas",
        json=payload,
        headers=headers,
    )
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "pessoa_conflict"


@pytest.mark.asyncio
async def test_update_pessoa_with_empty_payload_returns_bad_request(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "empty_payload")

    create_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Guido van Rossum", "email": "guido@example.com"},
        headers=headers,
    )
    pessoa_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/pessoas/{pessoa_id}",
        json={},
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"


@pytest.mark.asyncio
async def test_leitor_cannot_access_pessoas(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(
        client,
        test_session_maker,
        "leitor_forbidden",
        papel="leitor",
    )

    response = await client.get("/api/v1/pessoas", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"
