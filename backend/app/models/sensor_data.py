from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.sql import func

from ..database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tank_id = Column(String(64), nullable=False, index=True)
    temperature = Column(Float, nullable=False, comment="水温 (摄氏度)")
    ph = Column(Float, nullable=False, comment="pH值")
    dissolved_oxygen = Column(Float, nullable=False, comment="溶氧量 (mg/L)")
    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_tank_recorded_at", "tank_id", "recorded_at"),
    )
