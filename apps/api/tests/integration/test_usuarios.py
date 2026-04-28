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
    username = f"usuarios_{suffix}"
    senha = "securepass123"
    await _seed_usuario(
        test_session_maker,
        username=username,
        senha=senha,
        papel=papel,
        email=f"usuarios.{suffix}@example.com",
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "senha": senha},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_get_usuario(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "create_get")

    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Base", "email": "pessoa.base@example.com"},
        headers=headers,
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
        headers=headers,
    )
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["pessoa_id"] == pessoa_id
    assert created["username"] == "pessoabase"
    assert "senha_hash" not in created
    assert created["created_by"] is not None
    assert created["updated_by"] is not None

    usuario_id = created["id"]
    get_response = await client.get(f"/api/v1/usuarios/{usuario_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == usuario_id


@pytest.mark.asyncio
async def test_create_usuario_fails_if_pessoa_not_found(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "pessoa_not_found")

    response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": "f732ca0d-ea89-4b6d-84ad-ec18eea12c5f",
            "username": "sem_pessoa",
            "senha": "hash-404",
            "ativo": True,
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "pessoa_not_found"


@pytest.mark.asyncio
async def test_create_usuario_conflict_for_duplicate_username(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "duplicate")

    pessoa_a_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa A", "email": "pessoa.a@example.com"},
        headers=headers,
    )
    pessoa_b_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa B", "email": "pessoa.b@example.com"},
        headers=headers,
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
        headers=headers,
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
        headers=headers,
    )
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "usuario_conflict"


@pytest.mark.asyncio
async def test_update_and_delete_usuario(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "update_delete")

    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa U", "email": "pessoa.u@example.com"},
        headers=headers,
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
        headers=headers,
    )
    usuario_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={"ativo": False, "username": "usuario.u2"},
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["ativo"] is False
    assert updated["username"] == "usuario.u2"
    assert updated["updated_by"] is not None

    delete_response = await client.delete(
        f"/api/v1/usuarios/{usuario_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/usuarios/{usuario_id}", headers=headers)
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "usuario_not_found"


@pytest.mark.asyncio
async def test_list_usuarios_supports_filters(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "list_filters")

    pessoa_a_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Lista A", "email": "lista.a@example.com"},
        headers=headers,
    )
    pessoa_b_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Lista B", "email": "lista.b@example.com"},
        headers=headers,
    )

    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_a_response.json()["id"],
            "username": "alpha_user",
            "senha": "hash-a",
            "ativo": True,
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_b_response.json()["id"],
            "username": "beta_user",
            "senha": "hash-b",
            "ativo": False,
        },
        headers=headers,
    )

    response = await client.get(
        "/api/v1/usuarios",
        params={"username": "alpha", "ativo": True, "page": 1, "page_size": 10},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["username"] == "alpha_user"


@pytest.mark.asyncio
async def test_update_usuario_with_empty_payload_returns_bad_request(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    headers = await _auth_headers(client, test_session_maker, "empty_payload")

    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Vazia", "email": "vazia@example.com"},
        headers=headers,
    )
    usuario_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_response.json()["id"],
            "username": "vazio",
            "senha": "hash-v",
            "ativo": True,
        },
        headers=headers,
    )
    usuario_id = usuario_response.json()["id"]

    response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={},
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_payload"


@pytest.mark.asyncio
async def test_atendente_create_usuario_forces_leitor_role(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    atendente_headers = await _auth_headers(
        client,
        test_session_maker,
        "atendente_create",
        papel="atendente",
    )

    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Alvo", "email": "pessoa.alvo@example.com"},
        headers=atendente_headers,
    )

    response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_response.json()["id"],
            "username": "novo_usuario",
            "senha": "senha-nova",
            "ativo": True,
            "papel": "admin",
        },
        headers=atendente_headers,
    )

    assert response.status_code == 201
    assert response.json()["papel"] == "leitor"
    assert response.json()["created_by"] is not None
    assert response.json()["updated_by"] is not None


@pytest.mark.asyncio
async def test_atendente_cannot_change_usuario_role_or_pessoa(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    admin_headers = await _auth_headers(client, test_session_maker, "admin_setup")
    atendente_headers = await _auth_headers(
        client,
        test_session_maker,
        "atendente_update",
        papel="atendente",
    )

    pessoa1_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa 1", "email": "pessoa1.role@example.com"},
        headers=admin_headers,
    )
    pessoa2_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa 2", "email": "pessoa2.role@example.com"},
        headers=admin_headers,
    )

    usuario_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa1_response.json()["id"],
            "username": "alvo_update",
            "senha": "senha-alvo",
            "ativo": True,
            "papel": "leitor",
        },
        headers=admin_headers,
    )
    usuario_id = usuario_response.json()["id"]

    role_response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={"papel": "admin"},
        headers=atendente_headers,
    )
    assert role_response.status_code == 403

    pessoa_response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={"pessoa_id": pessoa2_response.json()["id"]},
        headers=atendente_headers,
    )
    assert pessoa_response.status_code == 403


@pytest.mark.asyncio
async def test_atendente_can_update_username_ativo_and_senha(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    admin_headers = await _auth_headers(client, test_session_maker, "admin_setup_2")
    atendente_headers = await _auth_headers(
        client,
        test_session_maker,
        "atendente_update_ok",
        papel="atendente",
    )

    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Pessoa Update", "email": "pessoa.update@example.com"},
        headers=admin_headers,
    )

    usuario_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_response.json()["id"],
            "username": "usuario_update",
            "senha": "senha-antiga",
            "ativo": True,
            "papel": "leitor",
        },
        headers=admin_headers,
    )
    usuario_id = usuario_response.json()["id"]

    patch_response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={"username": "usuario_update_2", "ativo": False, "senha": "senha-nova"},
        headers=atendente_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["username"] == "usuario_update_2"
    assert patch_response.json()["ativo"] is False

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "usuario_update_2", "senha": "senha-nova"},
    )
    assert login_response.status_code == 200
