import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "name": "New User",
        "password": "test123",
        "lang": "fr",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["access_token"]
    assert data["role"] == "user"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@test.com", "name": "User", "password": "test123"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 200
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_login_existing_user(client: AsyncClient):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com", "name": "Login User", "password": "test123"
    })
    # Login
    r = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com", "password": "test123"
    })
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={
        "email": "ghost@test.com", "password": "test123"
    })
    assert r.status_code == 401
