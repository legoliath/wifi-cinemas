import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Kit(Base):
    __tablename__ = "kits"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    starlink_serial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    peplink_serial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unifi_site_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    admin_ssid: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(SAEnum("available","deployed","maintenance", name="kit_status"), default="available")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    shoots = relationship("Shoot", back_populates="kit")
