from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func

from ..database import Base


class ControlCommand(Base):
    __tablename__ = "control_commands"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tank_id = Column(String(64), nullable=False, index=True)
    device_type = Column(String(32), nullable=False, comment="设备类型: air_pump, heater, cooler 等")
    action = Column(String(32), nullable=False, comment="动作: turn_on, turn_off 等")
    duration_minutes = Column(Integer, nullable=True, comment="持续时间(分钟)")
    reason = Column(Text, nullable=True, comment="触发原因")
    triggered_by = Column(String(32), nullable=False, default="auto", comment="触发方式: auto/manual")
    is_executed = Column(Boolean, default=False, nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_tank_device_created", "tank_id", "device_type", "created_at"),
    )
