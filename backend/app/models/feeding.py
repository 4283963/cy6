from sqlalchemy import Column, Integer, String, DateTime, Boolean, Time, Date, Index, text
from sqlalchemy.sql import func

from ..database import Base


class FeedingSchedule(Base):
    __tablename__ = "feeding_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tank_id = Column(String(64), nullable=False, index=True)
    feeding_time = Column(Time, nullable=False, comment="每天喂食时间 (HH:MM)")
    is_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    detection_window_minutes = Column(
        Integer,
        nullable=False,
        default=15,
        server_default=text("15"),
        comment="检测窗口时长（分钟）：过了这个时间没检测到就提醒",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_tank_feeding_time", "tank_id", "feeding_time", unique=True),
    )


class FeedingRecord(Base):
    __tablename__ = "feeding_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tank_id = Column(String(64), nullable=False, index=True)
    feeding_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(Time, nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=True, comment="自动检测到喂食的时间")
    manually_marked_at = Column(DateTime(timezone=True), nullable=True, comment="手动标记的时间")
    is_fed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE"),
        index=True,
    )
    detection_method = Column(String(32), nullable=True, comment="检测方式: auto/manual")
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_tank_date_time", "tank_id", "feeding_date", "scheduled_time", unique=True),
    )
