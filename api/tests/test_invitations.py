import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_invite_user_to_shoot(client: AsyncClient, admin_token: str):
    # Create shoot
    r = await client.post("/api/v1/shoots", json={
        "name": "Invite Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    # Invite
    r = await client.post(f"/api/v1/invitations/shoot/{shoot_id}", json={
        "email": "sophie@prod.com", "name": "Sophie", "user_class": "chef_dep",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "sophie@prod.com"
    assert data["user_class"] == "chef_dep"
    assert data["invite_token"]
    return data["invite_token"], shoot_id


@pytest.mark.asyncio
async def test_accept_invite(client: AsyncClient, admin_token: str):
    # Create + invite
    r = await client.post("/api/v1/shoots", json={
        "name": "Accept Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    r = await client.post(f"/api/v1/invitations/shoot/{shoot_id}", json={
        "email": "new@crew.com", "name": "New Crew",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    token = r.json()["invite_token"]

    # Accept
    r = await client.get(f"/api/v1/invitations/accept/{token}")
    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Bienvenue! Accès accordé."
    assert data["shoot_name"] == "Accept Test"


@pytest.mark.asyncio
async def test_cannot_accept_twice(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Double Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    r = await client.post(f"/api/v1/invitations/shoot/{shoot_id}", json={
        "email": "once@crew.com",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    token = r.json()["invite_token"]

    await client.get(f"/api/v1/invitations/accept/{token}")
    r = await client.get(f"/api/v1/invitations/accept/{token}")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_duplicate_invite_rejected(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Dup Invite", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    payload = {"email": "dup@crew.com", "name": "Dup"}
    r1 = await client.post(f"/api/v1/invitations/shoot/{shoot_id}", json=payload,
                           headers={"Authorization": f"Bearer {admin_token}"})
    assert r1.status_code == 201

    r2 = await client.post(f"/api/v1/invitations/shoot/{shoot_id}", json=payload,
                           headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_pending_invites(client: AsyncClient, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Pending Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    # Invite 2 people
    for email in ["a@crew.com", "b@crew.com"]:
        await client.post(f"/api/v1/invitations/shoot/{shoot_id}",
                          json={"email": email},
                          headers={"Authorization": f"Bearer {admin_token}"})

    r = await client.get(f"/api/v1/invitations/shoot/{shoot_id}/pending",
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["total"] == 2


@pytest.mark.asyncio
async def test_user_cannot_invite(client: AsyncClient, user_token: str, admin_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Perm Test", "client": "C", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    r = await client.post(f"/api/v1/invitations/shoot/{shoot_id}",
                          json={"email": "x@x.com"},
                          headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403
