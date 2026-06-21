from datetime import time, date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class FeedingScheduleCreate(BaseModel):
    tank_id: str = Field(..., description="鱼缸ID")
    feeding_time: time = Field(..., description="喂食时间 (HH:MM)")
    detection_window_minutes: int = Field(default=15, ge=5, le=60, description="检测窗口时长(分钟)")


class FeedingScheduleUpdate(BaseModel):
    feeding_time: Optional[time] = None
    is_enabled: Optional[bool] = None
    detection_window_minutes: Optional[int] = Field(default=None, ge=5, le=60)


class FeedingScheduleResponse(BaseModel):
    id: int
    tank_id: str
    feeding_time: time
    is_enabled: bool
    detection_window_minutes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedingRecordResponse(BaseModel):
    id: int
    tank_id: str
    feeding_date: date
    scheduled_time: time
    detected_at: Optional[datetime] = None
    manually_marked_at: Optional[datetime] = None
    is_fed: bool
    detection_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedingMarkRequest(BaseModel):
    tank_id: str = Field(..., description="鱼缸ID")
    feeding_date: Optional[date] = None
    scheduled_time: time = Field(..., description="喂食时间")
    notes: Optional[str] = None


class FeedingStatusResponse(BaseModel):
    schedule: Optional[FeedingScheduleResponse] = None
    today_record: Optional[FeedingRecordResponse] = None
    is_feeding_time_passed: bool = False
    is_feeding_window_open: bool = False
    should_remind: bool = False
    minutes_until_feeding: Optional[int] = None
    minutes_since_feeding: Optional[int] = None
