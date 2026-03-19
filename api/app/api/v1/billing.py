"""Billing — owner sees all, admin sees their own shoots only."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, require_admin, require_owner
from app.models.user import User
from app.models.shoot import Shoot
from app.models.billing import BillingEntry
from app.schemas.billing import BillingEntryCreate, BillingEntryResponse, BillingReportResponse

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("", response_model=BillingEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_billing_entry(
    data: BillingEntryCreate,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Owner creates billing entries."""
    entry = BillingEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/report/{shoot_id}", response_model=BillingReportResponse)
async def get_billing_report(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Owner sees any shoot. Admin sees only their own."""
    shoot_result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = shoot_result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")

    if current_user.role != "owner" and shoot.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    result = await db.execute(select(BillingEntry).where(BillingEntry.shoot_id == shoot_id))
    entries = result.scalars().all()
    return BillingReportResponse(
        shoot_id=shoot_id,
        shoot_name=shoot.name,
        client=shoot.client,
        total_hours=sum(e.hours for e in entries),
        total_data_gb=sum(e.data_gb for e in entries),
        total_amount=sum(e.amount for e in entries),
        entries=entries,
    )


@router.get("/global", response_model=list[BillingReportResponse])
async def get_global_billing(
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
):
    """Owner: billing across all shoots."""
    query = select(Shoot)
    if status_filter:
        query = query.where(Shoot.status == status_filter)

    shoots_result = await db.execute(query.order_by(Shoot.created_at.desc()))
    shoots = shoots_result.scalars().all()

    reports = []
    for shoot in shoots:
        entries_result = await db.execute(
            select(BillingEntry).where(BillingEntry.shoot_id == shoot.id)
        )
        entries = entries_result.scalars().all()
        reports.append(BillingReportResponse(
            shoot_id=shoot.id,
            shoot_name=shoot.name,
            client=shoot.client,
            total_hours=sum(e.hours for e in entries),
            total_data_gb=sum(e.data_gb for e in entries),
            total_amount=sum(e.amount for e in entries),
            entries=entries,
        ))
    return reports
