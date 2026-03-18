import uuid
from datetime import datetime
from pydantic import BaseModel

class AlertResponse(BaseModel):
    id: uuid.UUID
    shoot_id: uuid.UUID
    type: str
    severity: str
    message: str
    acknowledged: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
