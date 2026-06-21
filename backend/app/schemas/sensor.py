from datetime import datetime
from pydantic import BaseModel, Field


class SensorDataCreate(BaseModel):
    tank_id: str = Field(..., description="鱼缸ID")
    temperature: float = Field(..., gt=0, lt=50, description="水温 (摄氏度)")
    ph: float = Field(..., gt=0, lt=14, description="pH值")
    dissolved_oxygen: float = Field(..., ge=0, le=20, description="溶氧量 (mg/L)")


class SensorDataResponse(BaseModel):
    id: int
    tank_id: str
    temperature: float
    ph: float
    dissolved_oxygen: float
    recorded_at: datetime

    class Config:
        from_attributes = True
