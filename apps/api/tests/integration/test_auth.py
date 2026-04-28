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


async def _seed_pessoa_without_usuario(
    test_session_maker: async_sessionmaker[AsyncSession],
    *,
    nome: str,
    email: str,
) -> None:
    async with test_session_maker() as session:
        pessoa = Pessoa(nome=nome, email=email)
        session.add(pessoa)
        await session.commit()


async def _login(client: AsyncClient, *, username: str, senha: str) -> str:
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "senha": senha},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Test successful login returns access token."""
    await _seed_usuario(
        test_session_maker,
        username="testuser",
        senha="securepass123",
        papel="leitor",
        email="test@example.com",
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "senha": "securepass123"},
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_credentials(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Test login with wrong password returns 401."""
    await _seed_usuario(
        test_session_maker,
        username="testuser2",
        senha="securepass123",
        papel="leitor",
        email="test2@example.com",
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser2", "senha": "wrongpassword"},
    )

    assert login_response.status_code == 401
    assert login_response.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_login_nonexistent_usuario(client: AsyncClient) -> None:
    """Test login with nonexistent user returns 401."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "senha": "somepassword"},
    )

    assert login_response.status_code == 401
    assert login_response.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_protected_endpoint_401_without_token(client: AsyncClient) -> None:
    """Test POST livros without token returns 401."""
    response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Test Book",
            "autor": "Test Author",
            "isbn": "1234567890",
            "ano_publicacao": 2024,
            "disponivel": True,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_emprestimos_list_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/emprestimos")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_protected_endpoint_success_with_valid_token(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Test POST livros with valid token succeeds."""
    await _seed_usuario(
        test_session_maker,
        username="testuser3",
        senha="securepass123",
        papel="admin",
        email="test3@example.com",
    )
    token = await _login(client, username="testuser3", senha="securepass123")

    response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Test Book",
            "autor": "Test Author",
            "isbn": "9876543210",
            "ano_publicacao": 2024,
            "disponivel": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["titulo"] == "Test Book"
    assert body["autor"] == "Test Author"


@pytest.mark.asyncio
async def test_protected_endpoint_fails_with_invalid_token(client: AsyncClient) -> None:
    """Test endpoint with invalid token returns 401."""
    response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Test Book",
            "autor": "Test Author",
            "isbn": "1111111111",
            "ano_publicacao": 2024,
            "disponivel": True,
        },
        headers={"Authorization": "Bearer invalid_token_here"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_get_livros_public_endpoint_no_auth_required(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Test GET livros doesn't require authentication."""
    await _seed_usuario(
        test_session_maker,
        username="testuser4",
        senha="securepass123",
        papel="admin",
        email="test4@example.com",
    )
    token = await _login(client, username="testuser4", senha="securepass123")

    await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Public Book",
            "autor": "Test Author",
            "isbn": "5555555555",
            "ano_publicacao": 2024,
            "disponivel": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get("/api/v1/livros")

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_protected_endpoint_403_for_leitor_role(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Test POST livros with leitor role returns 403."""
    await _seed_usuario(
        test_session_maker,
        username="readerrole",
        senha="securepass123",
        papel="leitor",
        email="reader.role@example.com",
    )
    token = await _login(client, username="readerrole", senha="securepass123")

    response = await client.post(
        "/api/v1/livros",
        json={
            "titulo": "Forbidden Book",
            "autor": "Test Author",
            "isbn": "2222222222",
            "ano_publicacao": 2024,
            "disponivel": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


@pytest.mark.asyncio
async def test_register_new_email_creates_leitor_user_and_allows_login(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Novo Leitor",
            "email": "novo.leitor@example.com",
            "username": "novo_leitor",
            "senha": "senha123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "created"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "novo_leitor", "senha": "senha123"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_register_existing_email_without_user_requires_verification(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    email = "claim.leitor@example.com"
    await _seed_pessoa_without_usuario(
        test_session_maker,
        nome="Pessoa Existente",
        email=email,
    )

    start_response = await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Nome Ignorado",
            "email": email,
            "username": "claim_user",
            "senha": "senha123",
        },
    )
    assert start_response.status_code == 201
    start_body = start_response.json()
    assert start_body["status"] == "verification_required"
    assert start_body["verification_code"] is not None

    verify_response = await client.post(
        "/api/v1/auth/register/verify",
        json={"email": email, "code": start_body["verification_code"]},
    )
    assert verify_response.status_code == 201
    assert verify_response.json()["status"] == "created"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "claim_user", "senha": "senha123"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_register_existing_email_with_user_returns_conflict(
    client: AsyncClient,
    test_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_usuario(
        test_session_maker,
        username="existing_user",
        senha="securepass123",
        papel="leitor",
        email="existing.user@example.com",
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Pessoa Tentativa",
            "email": "existing.user@example.com",
            "username": "outro_username",
            "senha": "senha123",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pessoa_already_has_user"
