"""Seed the database with test data: admin, tech, user, kit, shoot, access codes."""
import asyncio
import uuid
from datetime import date, datetime, timezone
from app.database import engine, async_session, Base
from app.models import *  # noqa


async def seed():
    async with async_session() as db:
        # Admin
        admin = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            email="admin@wificinemas.com",
            name="Goliath (Admin)",
            role="admin",
        )
        # Tech
        tech = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            email="tech@wificinemas.com",
            name="Marco (Tech)",
            role="tech",
        )
        # Regular user
        crew = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
            email="crew@wificinemas.com",
            name="Sophie (Crew)",
            role="user",
        )
        db.add_all([admin, tech, crew])
        await db.flush()

        # Kit
        kit = Kit(
            id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
            name="Kit Alpha",
            starlink_serial="SL-001",
            peplink_serial="PL-001",
            admin_ssid="WFC-Admin-Alpha",
            status="deployed",
        )
        db.add(kit)
        await db.flush()

        # Shoot
        shoot = Shoot(
            id=uuid.UUID("00000000-0000-0000-0000-000000000100"),
            name="Tournage Plateau Mont-Royal",
            ssid="WFC-PlateauMtl",
            client="Productions Éléphant",
            location="Montréal, Plateau Mont-Royal",
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 25),
            kit_id=kit.id,
            status="active",
            created_by=admin.id,
        )
        db.add(shoot)
        await db.flush()

        # Access codes
        for i, code in enumerate(["CREW-001", "CREW-002", "CREW-003"]):
            access = ShootAccess(
                shoot_id=shoot.id,
                access_code=code,
                qr_data=f"wfc://{shoot.id}/{code}",
                user_id=crew.id if i == 0 else None,
            )
            db.add(access)

        await db.commit()
        print("✅ Seeded: 3 users, 1 kit, 1 shoot, 3 access codes")


if __name__ == "__main__":
    asyncio.run(seed())
