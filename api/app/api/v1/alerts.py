import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertListResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=AlertListResponse)
async def list_alerts(current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)], shoot_id: uuid.UUID | None = None, severity: str | None = None):
    query = select(Alert)
    if shoot_id: query = query.where(Alert.shoot_id == shoot_id)
    if severity: query = query.where(Alert.severity == severity)
    result = await db.execute(query.order_by(Alert.created_at.desc()).limit(50))
    alerts = result.scalars().all()
    return AlertListResponse(alerts=alerts, total=len(alerts))

@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: uuid.UUID, admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_by = admin.id
    await db.commit()
    await db.refresh(alert)
    return alert
