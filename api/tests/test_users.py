import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, admin_token: str):
    r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, user_token: str):
    r = await client.patch("/api/v1/users/me", json={
        "name": "Updated Name", "lang": "en",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_owner_lists_all_users(client: AsyncClient, owner_token: str, admin_user, regular_user):
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 200
    assert r.json()["total"] >= 3


@pytest.mark.asyncio
async def test_admin_cannot_list_all_users(client: AsyncClient, admin_token: str):
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_list_users(client: AsyncClient, user_token: str):
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_owner_creates_admin(client: AsyncClient, owner_token: str):
    r = await client.post("/api/v1/users/admin", json={
        "email": "newclient@productions.com", "name": "New Client",
    }, headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 201
    assert r.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_admin_cannot_create_admin(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/users/admin", json={
        "email": "hack@evil.com", "name": "Hacker",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_owner_deactivates_user(client: AsyncClient, owner_token: str, regular_user):
    r = await client.delete(f"/api/v1/users/{regular_user.id}",
                            headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_user(client: AsyncClient, admin_token: str, regular_user):
    r = await client.delete(f"/api/v1/users/{regular_user.id}",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_shoot_admin_adds_and_removes_member(client: AsyncClient, admin_token: str):
    """Admin creates shoot, adds a tech, then removes them."""
    # Create shoot
    r = await client.post("/api/v1/shoots", json={
        "name": "Member Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    # Add tech
    r = await client.post(f"/api/v1/users/shoot/{shoot_id}/members", json={
        "email": "techguy@set.com", "name": "Tech Guy", "role": "tech",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    tech_id = r.json()["id"]

    # Remove tech
    r = await client.delete(f"/api/v1/users/shoot/{shoot_id}/members/{tech_id}",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_cannot_add_duplicate_member(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Dup Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    payload = {"email": "dup@set.com", "name": "Dup", "role": "user"}
    r1 = await client.post(f"/api/v1/users/shoot/{shoot_id}/members", json=payload,
                           headers={"Authorization": f"Bearer {admin_token}"})
    assert r1.status_code == 201

    r2 = await client.post(f"/api/v1/users/shoot/{shoot_id}/members", json=payload,
                           headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 409
