import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, admin_token: str):
    r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "admin@wificinemas.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, user_token: str):
    r = await client.patch("/api/v1/users/me", json={
        "name": "Updated Name",
        "lang": "en",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"
    assert r.json()["lang"] == "en"


@pytest.mark.asyncio
async def test_list_users_admin_only(client: AsyncClient, user_token: str, admin_token: str):
    # User can't list
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403
    # Admin can
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
