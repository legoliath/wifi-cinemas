import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_shoot_as_admin(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Tournage Plateau",
        "client": "Productions ABC",
        "location": "Montréal, Plateau",
        "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Tournage Plateau"
    assert data["ssid"].startswith("WFC-")
    assert data["status"] == "scheduled"


@pytest.mark.asyncio
async def test_create_shoot_as_owner(client: AsyncClient, owner_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Owner Shoot",
        "client": "Direct Client",
        "start_date": "2026-05-01",
    }, headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_shoot_as_user_forbidden(client: AsyncClient, user_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Unauthorized Shoot",
        "client": "Nobody",
        "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_owner_lists_all_shoots(client: AsyncClient, owner_token: str, admin_token: str):
    # Admin creates a shoot
    await client.post("/api/v1/shoots", json={
        "name": "Admin Shoot", "client": "Client A", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    # Owner sees all
    r = await client.get("/api/v1/shoots", headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_admin_sees_only_own_shoots(client: AsyncClient, admin_token: str, owner_token: str):
    # Owner creates a shoot (not the admin's)
    await client.post("/api/v1/shoots", json={
        "name": "Owner Only Shoot", "client": "Secret", "start_date": "2026-06-01",
    }, headers={"Authorization": f"Bearer {owner_token}"})
    # Admin creates their own
    await client.post("/api/v1/shoots", json={
        "name": "Admin Shoot", "client": "My Client", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    # Admin only sees their own
    r = await client.get("/api/v1/shoots", headers={"Authorization": f"Bearer {admin_token}"})
    shoots = r.json()["shoots"]
    assert all(s["name"] != "Owner Only Shoot" for s in shoots)


@pytest.mark.asyncio
async def test_generate_access_codes(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Code Test", "client": "Client", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]
    r = await client.post(f"/api/v1/shoots/{shoot_id}/access-codes", json={
        "count": 5,
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 5


@pytest.mark.asyncio
async def test_unauthenticated_access_rejected(client: AsyncClient):
    r = await client.get("/api/v1/shoots")
    assert r.status_code in (401, 403)
