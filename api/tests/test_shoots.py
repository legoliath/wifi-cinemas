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
async def test_create_shoot_as_user_forbidden(client: AsyncClient, user_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Unauthorized Shoot",
        "client": "Nobody",
        "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_list_shoots(client: AsyncClient, admin_token: str):
    # Create one
    await client.post("/api/v1/shoots", json={
        "name": "Test Shoot", "client": "Client", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    # List
    r = await client.get("/api/v1/shoots", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_generate_access_codes(client: AsyncClient, admin_token: str):
    # Create shoot
    r = await client.post("/api/v1/shoots", json={
        "name": "Code Test", "client": "Client", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]
    # Generate codes
    r = await client.post(f"/api/v1/shoots/{shoot_id}/access-codes", json={
        "count": 5,
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    codes = r.json()
    assert len(codes) == 5
    assert all(c["code"] for c in codes)


@pytest.mark.asyncio
async def test_unauthenticated_access_rejected(client: AsyncClient):
    r = await client.get("/api/v1/shoots")
    assert r.status_code in (401, 403)
