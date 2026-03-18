import uuid
from datetime import date, datetime
from pydantic import BaseModel

class BillingEntryCreate(BaseModel):
    shoot_id: uuid.UUID
    date: date
    hours: float
    data_gb: float = 0.0
    amount: float = 0.0
    notes: str | None = None

class BillingEntryResponse(BaseModel):
    id: uuid.UUID
    shoot_id: uuid.UUID
    date: date
    hours: float
    data_gb: float
    amount: float
    notes: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class BillingReportResponse(BaseModel):
    shoot_id: uuid.UUID
    shoot_name: str
    client: str
    total_hours: float
    total_data_gb: float
    total_amount: float
    entries: list[BillingEntryResponse]
