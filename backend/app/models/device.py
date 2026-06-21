from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func

from ..database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tank_id = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    air_pump_running = Column(Boolean, default=False, nullable=False)
    heater_running = Column(Boolean, default=False, nullable=False)
    cooler_running = Column(Boolean, default=False, nullable=False)
    current_temp = Column(Float, nullable=True)
    current_ph = Column(Float, nullable=True)
    current_do = Column(Float, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
