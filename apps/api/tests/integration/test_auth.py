import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Test successful login returns access token."""
    # First, create a pessoa and usuario
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Test User", "email": "test@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    usuario_response = await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": "testuser",
            "senha": "securepass123",
            "ativo": True,
        },
    )
    assert usuario_response.status_code == 201

    # Now test login
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
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Test login with wrong password returns 401."""
    # First, create a usuario
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Test User", "email": "test2@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": "testuser2",
            "senha": "securepass123",
            "ativo": True,
        },
    )

    # Try login with wrong password
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
async def test_protected_endpoint_success_with_valid_token(client: AsyncClient) -> None:
    """Test POST livros with valid token succeeds."""
    # Create usuario and get token
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Test User", "email": "test3@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": "testuser3",
            "senha": "securepass123",
            "ativo": True,
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser3", "senha": "securepass123"},
    )
    token = login_response.json()["access_token"]

    # Create livro with token
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
async def test_get_livros_public_endpoint_no_auth_required(client: AsyncClient) -> None:
    """Test GET livros doesn't require authentication."""
    # Create a livro with auth
    pessoa_response = await client.post(
        "/api/v1/pessoas",
        json={"nome": "Test User", "email": "test4@example.com"},
    )
    pessoa_id = pessoa_response.json()["id"]

    await client.post(
        "/api/v1/usuarios",
        json={
            "pessoa_id": pessoa_id,
            "username": "testuser4",
            "senha": "securepass123",
            "ativo": True,
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser4", "senha": "securepass123"},
    )
    token = login_response.json()["access_token"]

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

    # Now test GET without auth
    response = await client.get("/api/v1/livros")

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
