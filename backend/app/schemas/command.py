from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ControlCommandResponse(BaseModel):
    id: int
    tank_id: str
    device_type: str
    action: str
    duration_minutes: Optional[int] = None
    reason: Optional[str] = None
    triggered_by: str
    is_executed: bool
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommandExecuteRequest(BaseModel):
    command_id: int = Field(..., description="指令ID")
