import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_shoot_as_admin(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Tournage Plateau", "client": "Productions ABC",
        "location": "Montréal", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    assert r.json()["ssid"].startswith("WFC-")


@pytest.mark.asyncio
async def test_create_shoot_as_owner(client: AsyncClient, owner_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Owner Shoot", "client": "Direct", "start_date": "2026-05-01",
    }, headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_user_cannot_create_shoot(client: AsyncClient, user_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Nope", "client": "X", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_owner_lists_all_shoots(client: AsyncClient, owner_token: str, admin_token: str):
    await client.post("/api/v1/shoots", json={
        "name": "S1", "client": "C1", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    r = await client.get("/api/v1/shoots", headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_generate_access_codes(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Code Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]
    r = await client.post(f"/api/v1/shoots/{shoot_id}/access-codes",
                          json={"count": 5},
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 5


@pytest.mark.asyncio
async def test_unauthenticated_rejected(client: AsyncClient):
    r = await client.get("/api/v1/shoots")
    assert r.status_code in (401, 403)
