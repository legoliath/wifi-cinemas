import uuid
from datetime import date, datetime
from pydantic import BaseModel

class ShootCreate(BaseModel):
    name: str
    client: str
    location: str | None = None
    start_date: date
    end_date: date | None = None
    kit_id: uuid.UUID | None = None

class ShootUpdate(BaseModel):
    name: str | None = None
    client: str | None = None
    location: str | None = None
    status: str | None = None
    kit_id: uuid.UUID | None = None

class ShootResponse(BaseModel):
    id: uuid.UUID
    name: str
    ssid: str
    client: str
    location: str | None
    start_date: date
    end_date: date | None
    status: str
    created_by: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}

class ShootListResponse(BaseModel):
    shoots: list[ShootResponse]
    total: int

class AccessCodeResponse(BaseModel):
    code: str
    qr_data: str
    shoot_id: uuid.UUID

class GenerateCodesRequest(BaseModel):
    count: int = 10
