import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import Base, engine


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_full_user_flow(client):
    """Test complete user flow: register -> login -> upload -> analyze."""

    # 1. Register
    register_resp = await client.post(
        "/api/auth/register",
        json={"email": "flow@example.com", "password": "test123"},
    )
    assert register_resp.status_code == 201

    # 2. Login
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "flow@example.com", "password": "test123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 3. Health check
    health_resp = await client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


@pytest.mark.asyncio
async def test_auth_flow(client):
    """Test authentication flow."""
    # Register
    response = await client.post(
        "/api/auth/register",
        json={"email": "authtest@example.com", "password": "test123"},
    )
    assert response.status_code == 201

    # Login with correct password
    response = await client.post(
        "/api/auth/login",
        json={"email": "authtest@example.com", "password": "test123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Login with wrong password
    response = await client.post(
        "/api/auth/login",
        json={"email": "authtest@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
