import uuid
from datetime import datetime, date
from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class BillingEntry(Base):
    __tablename__ = "billing_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shoot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shoots.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    hours: Mapped[float] = mapped_column(Float, default=0.0)
    data_gb: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    shoot = relationship("Shoot", back_populates="billing_entries")
