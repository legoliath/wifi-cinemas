import pytest
import pytest_asyncio
import uuid
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import make_token
from app.models.user import User
from app.models.shoot import Shoot
from app.models.shoot_access import ShootAccess


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
async def test_create_shoot_auto_grants_admin_access(client: AsyncClient, admin_token: str, db: AsyncSession, admin_user):
    """Creator automatically gets shoot_role=admin access."""
    r = await client.post("/api/v1/shoots", json={
        "name": "Auto Access", "client": "Client", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = uuid.UUID(r.json()["id"])

    result = await db.execute(
        ShootAccess.__table__.select().where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == admin_user.id,
        )
    )
    access = result.first()
    assert access is not None
    assert access.shoot_role == "admin"


@pytest.mark.asyncio
async def test_create_shoot_as_owner(client: AsyncClient, owner_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Owner Shoot", "client": "Direct", "start_date": "2026-05-01",
    }, headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_shoot_as_user_forbidden(client: AsyncClient, user_token: str):
    r = await client.post("/api/v1/shoots", json={
        "name": "Nope", "client": "Nobody", "start_date": "2026-04-01",
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
async def test_admin_sees_only_own_shoots(client: AsyncClient, admin_token: str, db: AsyncSession):
    """Admin A can't see Admin B's shoots."""
    # Create another admin
    admin_b = User(id=uuid.uuid4(), email="adminb@other.com", name="Admin B", role="admin")
    db.add(admin_b)
    await db.commit()
    await db.refresh(admin_b)
    token_b = make_token(str(admin_b.id), "admin")

    # Admin B creates a shoot
    await client.post("/api/v1/shoots", json={
        "name": "B's Secret Shoot", "client": "B Corp", "start_date": "2026-06-01",
    }, headers={"Authorization": f"Bearer {token_b}"})

    # Admin A creates their own
    await client.post("/api/v1/shoots", json={
        "name": "A's Shoot", "client": "A Corp", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})

    # Admin A only sees their own
    r = await client.get("/api/v1/shoots", headers={"Authorization": f"Bearer {admin_token}"})
    shoots = r.json()["shoots"]
    assert all(s["name"] != "B's Secret Shoot" for s in shoots)


@pytest.mark.asyncio
async def test_multi_admin_shoot(client: AsyncClient, admin_token: str, db: AsyncSession, admin_user):
    """Multiple admins can manage the same shoot."""
    # Admin A creates shoot
    r = await client.post("/api/v1/shoots", json={
        "name": "Multi Admin Shoot", "client": "Big Prod", "start_date": "2026-04-01",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    shoot_id = r.json()["id"]

    # Admin A adds Admin B to the shoot as admin
    r = await client.post(f"/api/v1/users/shoot/{shoot_id}/members", json={
        "email": "adminb@bigprod.com", "name": "Admin B", "role": "admin",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    admin_b_id = r.json()["id"]

    # Admin B can now list members
    token_b = make_token(admin_b_id, "admin")
    r = await client.get(f"/api/v1/shoots/{shoot_id}/members",
                         headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    assert r.json()["total"] >= 2  # Admin A + Admin B


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
