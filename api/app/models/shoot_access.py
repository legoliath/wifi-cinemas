import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ShootAccess(Base):
    __tablename__ = "shoot_accesses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    shoot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shoots.id"))
    access_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    qr_data: Mapped[str | None] = mapped_column(String(500), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates="shoot_accesses")
    shoot = relationship("Shoot", back_populates="accesses")
