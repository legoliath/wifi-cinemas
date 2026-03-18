import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.models.shoot import Shoot
from app.models.billing import BillingEntry
from app.schemas.billing import BillingEntryCreate, BillingEntryResponse, BillingReportResponse

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.post("", response_model=BillingEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_billing_entry(data: BillingEntryCreate, admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    entry = BillingEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

@router.get("/report/{shoot_id}", response_model=BillingReportResponse)
async def get_billing_report(shoot_id: uuid.UUID, admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    shoot_result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = shoot_result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")
    result = await db.execute(select(BillingEntry).where(BillingEntry.shoot_id == shoot_id))
    entries = result.scalars().all()
    return BillingReportResponse(shoot_id=shoot_id, shoot_name=shoot.name, client=shoot.client, total_hours=sum(e.hours for e in entries), total_data_gb=sum(e.data_gb for e in entries), total_amount=sum(e.amount for e in entries), entries=entries)
