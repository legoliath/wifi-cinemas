import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("", response_model=UserListResponse)
async def list_users(admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)], skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    count = await db.execute(select(func.count()).select_from(User))
    return UserListResponse(users=users, total=count.scalar() or 0)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: uuid.UUID, admin: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await db.commit()
