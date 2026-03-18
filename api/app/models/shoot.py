import uuid
from datetime import datetime, date
from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Shoot(Base):
    __tablename__ = "shoots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    ssid: Mapped[str] = mapped_column(String(32))
    client: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    kit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("kits.id"), nullable=True)
    status: Mapped[str] = mapped_column(SAEnum("scheduled","active","completed","cancelled", name="shoot_status"), default="scheduled")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    kit = relationship("Kit", back_populates="shoots")
    creator = relationship("User", foreign_keys=[created_by])
    accesses = relationship("ShootAccess", back_populates="shoot")
    devices = relationship("Device", back_populates="shoot")
    metrics = relationship("NetworkMetric", back_populates="shoot")
    alerts = relationship("Alert", back_populates="shoot")
    billing_entries = relationship("BillingEntry", back_populates="shoot")
