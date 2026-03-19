import pytest
import pytest_asyncio
import uuid
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import make_token
from app.models.user import User
from app.models.shoot import Shoot


@pytest_asyncio.fixture
async def tech_user(db: AsyncSession):
    user = User(id=uuid.uuid4(), email="tech@wificinemas.com", name="Tech Guy", role="tech")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def tech_token(tech_user):
    return make_token(str(tech_user.id), "tech")


@pytest_asyncio.fixture
async def shoot(db: AsyncSession, admin_user):
    s = Shoot(
        id=uuid.uuid4(), name="Test Shoot", ssid="WFC-Test", client="Client",
        start_date=date(2026, 4, 1), status="active", created_by=admin_user.id,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@pytest.mark.asyncio
async def test_roof_status_as_tech(client: AsyncClient, tech_token: str, shoot):
    r = await client.get(
        f"/api/v1/roof/status/{shoot.id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_live"] is False
    assert data["subscribers"] == 0


@pytest.mark.asyncio
async def test_roof_status_as_admin(client: AsyncClient, admin_token: str, shoot):
    r = await client.get(
        f"/api/v1/roof/status/{shoot.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_roof_status_forbidden_for_user(client: AsyncClient, user_token: str, shoot):
    r = await client.get(
        f"/api/v1/roof/status/{shoot.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_post_telemetry(client: AsyncClient, tech_token: str, shoot):
    r = await client.post(
        f"/api/v1/roof/telemetry/{shoot.id}",
        json={
            "signal_strength": 85.0,
            "obstruction_pct": 0.02,
            "tilt_x": 1.5,
            "tilt_y": -0.8,
            "compass_heading": 180.0,
            "download_mbps": 150.0,
            "upload_mbps": 25.0,
            "latency_ms": 22.0,
            "phone_battery_pct": 78.0,
            "is_charging": True,
            "source_device": "iPhone 15 Pro",
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["signal_strength"] == 85.0
    assert data["source_device"] == "iPhone 15 Pro"


@pytest.mark.asyncio
async def test_roof_history(client: AsyncClient, tech_token: str, shoot):
    # Post some data first
    for i in range(3):
        await client.post(
            f"/api/v1/roof/telemetry/{shoot.id}",
            json={"signal_strength": 80 + i, "obstruction_pct": 0.01 * i},
            headers={"Authorization": f"Bearer {tech_token}"},
        )
    # Fetch history
    r = await client.get(
        f"/api/v1/roof/history/{shoot.id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 3
