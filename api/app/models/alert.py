import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shoot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shoots.id"), index=True)
    type: Mapped[str] = mapped_column(SAEnum("starlink_down","failover_active","ap_offline","data_cap_warning","high_latency","packet_loss","custom", name="alert_type"))
    severity: Mapped[str] = mapped_column(SAEnum("info","warning","critical", name="alert_severity"), default="warning")
    message: Mapped[str] = mapped_column(Text)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    shoot = relationship("Shoot", back_populates="alerts")
