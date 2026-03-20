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


@pytest_asyncio.fixture
async def shoot_with_admin(db: AsyncSession, admin_user):
    s = Shoot(
        id=uuid.uuid4(), name="Test Shoot", ssid="WFC-Test", client="Client",
        start_date=date(2026, 4, 1), status="active", created_by=admin_user.id,
    )
    db.add(s)
    await db.flush()
    # Admin gets access
    db.add(ShootAccess(shoot_id=s.id, user_id=admin_user.id, access_code="ADM-001"))
    await db.commit()
    await db.refresh(s)
    return s


@pytest.mark.asyncio
async def test_roof_status_as_admin(client: AsyncClient, admin_token: str, shoot_with_admin):
    r = await client.get(
        f"/api/v1/roof/status/{shoot_with_admin.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["is_live"] is False


@pytest.mark.asyncio
async def test_roof_status_forbidden_for_user(client: AsyncClient, user_token: str, shoot_with_admin):
    r = await client.get(
        f"/api/v1/roof/status/{shoot_with_admin.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_post_telemetry_as_admin(client: AsyncClient, admin_token: str, shoot_with_admin):
    r = await client.post(
        f"/api/v1/roof/telemetry/{shoot_with_admin.id}",
        json={
            "signal_strength": 85.0, "obstruction_pct": 0.02,
            "tilt_x": 1.5, "tilt_y": -0.8, "compass_heading": 180.0,
            "download_mbps": 150.0, "upload_mbps": 25.0, "latency_ms": 22.0,
            "phone_battery_pct": 78.0, "is_charging": True,
            "source_device": "iPhone 15 Pro",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    assert r.json()["signal_strength"] == 85.0


@pytest.mark.asyncio
async def test_roof_history(client: AsyncClient, admin_token: str, shoot_with_admin):
    for i in range(3):
        await client.post(
            f"/api/v1/roof/telemetry/{shoot_with_admin.id}",
            json={"signal_strength": 80 + i, "obstruction_pct": 0.01 * i},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    r = await client.get(
        f"/api/v1/roof/history/{shoot_with_admin.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 3
