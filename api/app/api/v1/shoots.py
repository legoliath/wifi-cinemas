import uuid, secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.shoot import Shoot
from app.models.shoot_access import ShootAccess
from app.schemas.shoot import ShootCreate, ShootUpdate, ShootResponse, ShootListResponse, AccessCodeResponse, GenerateCodesRequest

router = APIRouter(prefix="/shoots", tags=["Shoots"])

@router.post("", response_model=ShootResponse, status_code=status.HTTP_201_CREATED)
async def create_shoot(data: ShootCreate, admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    ssid = f"WFC-{data.name.replace(' ','')[:20]}"
    shoot = Shoot(name=data.name, ssid=ssid, client=data.client, location=data.location, start_date=data.start_date, end_date=data.end_date, kit_id=data.kit_id, status="scheduled", created_by=admin.id)
    db.add(shoot)
    await db.commit()
    await db.refresh(shoot)
    return shoot

@router.get("", response_model=ShootListResponse)
async def list_shoots(current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)], status_filter: str | None = Query(None, alias="status")):
    query = select(Shoot)
    if current_user.role != "admin":
        query = query.join(ShootAccess).where(ShootAccess.user_id == current_user.id)
    if status_filter:
        query = query.where(Shoot.status == status_filter)
    result = await db.execute(query.limit(50))
    shoots = result.scalars().all()
    return ShootListResponse(shoots=shoots, total=len(shoots))

@router.get("/{shoot_id}", response_model=ShootResponse)
async def get_shoot(shoot_id: uuid.UUID, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")
    return shoot

@router.post("/{shoot_id}/access-codes", response_model=list[AccessCodeResponse])
async def generate_access_codes(shoot_id: uuid.UUID, data: GenerateCodesRequest, admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    codes = []
    for _ in range(data.count):
        code = secrets.token_urlsafe(6).upper()[:8]
        qr_data = f"wfc://{shoot_id}/{code}"
        db.add(ShootAccess(shoot_id=shoot_id, access_code=code, qr_data=qr_data))
        codes.append(AccessCodeResponse(code=code, qr_data=qr_data, shoot_id=shoot_id))
    await db.commit()
    return codes
