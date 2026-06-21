from datetime import datetime, time, date
from typing import Optional, List
from pydantic import BaseModel


class TankStatus(BaseModel):
    tank_id: str
    name: str
    current_temp: Optional[float] = None
    current_ph: Optional[float] = None
    current_do: Optional[float] = None
    air_pump_running: bool = False
    heater_running: bool = False
    cooler_running: bool = False
    last_heartbeat: Optional[datetime] = None
    temp_status: str = "normal"
    ph_status: str = "normal"
    do_status: str = "normal"


class FeedingStatus(BaseModel):
    has_schedule: bool = False
    feeding_time: Optional[time] = None
    is_enabled: bool = False
    detection_window_minutes: int = 15
    today_is_fed: bool = False
    fed_time: Optional[datetime] = None
    detection_method: Optional[str] = None
    is_feeding_window_open: bool = False
    should_remind: bool = False
    minutes_until_feeding: Optional[int] = None
    minutes_since_feeding: Optional[int] = None


class PendingCommand(BaseModel):
    id: int
    device_type: str
    action: str
    duration_minutes: Optional[int] = None
    reason: Optional[str] = None
    created_at: datetime


class DashboardSummary(BaseModel):
    tank_status: TankStatus
    pending_commands: List[PendingCommand]
    recent_sensor_count: int
    today_command_count: int
    feeding_status: FeedingStatus
