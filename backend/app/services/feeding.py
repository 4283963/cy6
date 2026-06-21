from datetime import datetime, timedelta, time, date
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
import statistics

from ..config import get_settings
from ..models import SensorData, FeedingSchedule, FeedingRecord

settings = get_settings()


class FeedingService:

    @staticmethod
    def detect_feeding_activity(
        db: Session,
        tank_id: str,
        current_do: float,
        current_temp: float,
        current_ph: float,
    ) -> Tuple[bool, float]:
        """
        通过传感器数据波动检测是否有喂食活动
        原理：喂食时鱼会剧烈活动，导致溶氧量出现明显波动（先降后升）
        同时水面扰动也会影响温度和pH的微变化

        返回: (是否检测到喂食, 波动评分)
        """
        recent_data = (
            db.query(SensorData)
            .filter(SensorData.tank_id == tank_id)
            .order_by(SensorData.recorded_at.desc())
            .limit(10)
            .all()
        )

        if len(recent_data) < 5:
            return False, 0.0

        do_values = [d.dissolved_oxygen for d in recent_data]
        temp_values = [d.temperature for d in recent_data]
        ph_values = [d.ph for d in recent_data]

        do_std = statistics.stdev(do_values) if len(do_values) > 1 else 0
        temp_std = statistics.stdev(temp_values) if len(temp_values) > 1 else 0
        ph_std = statistics.stdev(ph_values) if len(ph_values) > 1 else 0

        do_range = max(do_values) - min(do_values)
        temp_range = max(temp_values) - min(temp_values)
        ph_range = max(ph_values) - min(ph_values)

        do_change = abs(current_do - statistics.mean(do_values[1:5])) if len(do_values) > 3 else 0

        score = 0.0
        score += min(do_std * 50, 40)
        score += min(do_range * 30, 30)
        score += min(do_change * 40, 20)
        score += min(temp_std * 100, 5)
        score += min(temp_range * 50, 3)
        score += min(ph_std * 200, 2)

        is_feeding = score >= 25.0

        return is_feeding, round(score, 2)

    @staticmethod
    def is_in_feeding_window(
        schedule: FeedingSchedule,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, int, int]:
        """
        判断当前是否在喂食检测窗口内
        返回: (是否在窗口内, 距喂食还有多少分钟, 超过喂食多少分钟)
        """
        now = now or datetime.utcnow()
        now_time = now.time()
        feed_time = schedule.feeding_time

        now_total = now_time.hour * 60 + now_time.minute + now_time.second / 60
        feed_total = feed_time.hour * 60 + feed_time.minute

        window_minutes = schedule.detection_window_minutes

        minutes_until = feed_total - now_total
        minutes_since = now_total - feed_total

        if -window_minutes <= minutes_until <= window_minutes:
            return True, int(max(0, minutes_until)), int(max(0, minutes_since))

        return False, int(max(0, minutes_until)), int(max(0, minutes_since))

    @staticmethod
    def get_or_create_today_record(
        db: Session,
        schedule: FeedingSchedule,
        today: Optional[date] = None,
    ) -> FeedingRecord:
        """获取或创建今日的喂食记录"""
        today = today or datetime.utcnow().date()

        record = (
            db.query(FeedingRecord)
            .filter(
                FeedingRecord.tank_id == schedule.tank_id,
                FeedingRecord.feeding_date == today,
                FeedingRecord.scheduled_time == schedule.feeding_time,
            )
            .first()
        )

        if not record:
            record = FeedingRecord(
                tank_id=schedule.tank_id,
                feeding_date=today,
                scheduled_time=schedule.feeding_time,
                is_fed=False,
            )
            db.add(record)
            db.flush()

        return record

    @staticmethod
    def process_feeding_detection(
        db: Session,
        tank_id: str,
        current_do: float,
        current_temp: float,
        current_ph: float,
    ) -> Optional[dict]:
        """
        处理喂食检测，每次传感器数据上传时调用
        返回检测结果信息（如果在检测窗口内）
        """
        schedule = (
            db.query(FeedingSchedule)
            .filter(
                FeedingSchedule.tank_id == tank_id,
                FeedingSchedule.is_enabled == True,
            )
            .first()
        )

        if not schedule:
            return None

        now = datetime.utcnow()
        in_window, minutes_until, minutes_since = FeedingService.is_in_feeding_window(
            schedule, now
        )

        record = FeedingService.get_or_create_today_record(db, schedule, now.date())

        result = {
            "in_window": in_window,
            "minutes_until": minutes_until,
            "minutes_since": minutes_since,
            "window_minutes": schedule.detection_window_minutes,
            "already_fed": record.is_fed,
            "detected": False,
            "score": 0.0,
        }

        if record.is_fed:
            return result

        if in_window:
            is_feeding, score = FeedingService.detect_feeding_activity(
                db, tank_id, current_do, current_temp, current_ph
            )
            result["detected"] = is_feeding
            result["score"] = score

            if is_feeding:
                record.is_fed = True
                record.detected_at = now
                record.detection_method = "auto"
                record.notes = f"自动检测到喂食，波动评分 {score}"
                db.flush()

        return result

    @staticmethod
    def calculate_feeding_status(
        db: Session,
        tank_id: str,
    ) -> dict:
        """
        计算当前喂食状态，供仪表盘使用
        """
        now = datetime.utcnow()

        schedule = (
            db.query(FeedingSchedule)
            .filter(
                FeedingSchedule.tank_id == tank_id,
                FeedingSchedule.is_enabled == True,
            )
            .first()
        )

        if not schedule:
            return {
                "has_schedule": False,
                "feeding_time": None,
                "is_enabled": False,
                "detection_window_minutes": 15,
                "today_is_fed": False,
                "fed_time": None,
                "detection_method": None,
                "is_feeding_window_open": False,
                "should_remind": False,
                "minutes_until_feeding": None,
                "minutes_since_feeding": None,
            }

        today_record = (
            db.query(FeedingRecord)
            .filter(
                FeedingRecord.tank_id == tank_id,
                FeedingRecord.feeding_date == now.date(),
                FeedingRecord.scheduled_time == schedule.feeding_time,
            )
            .first()
        )

        in_window, minutes_until, minutes_since = FeedingService.is_in_feeding_window(
            schedule, now
        )

        should_remind = False
        if not today_record or not today_record.is_fed:
            if minutes_since > 0 and minutes_since <= 120:
                should_remind = True

        fed_time = None
        detection_method = None
        if today_record and today_record.is_fed:
            fed_time = today_record.detected_at or today_record.manually_marked_at
            detection_method = today_record.detection_method

        return {
            "has_schedule": True,
            "feeding_time": schedule.feeding_time,
            "is_enabled": schedule.is_enabled,
            "detection_window_minutes": schedule.detection_window_minutes,
            "today_is_fed": today_record.is_fed if today_record else False,
            "fed_time": fed_time,
            "detection_method": detection_method,
            "is_feeding_window_open": in_window,
            "should_remind": should_remind,
            "minutes_until_feeding": minutes_until if minutes_until > 0 else None,
            "minutes_since_feeding": minutes_since if minutes_since > 0 else None,
        }

    @staticmethod
    def set_schedule(
        db: Session,
        tank_id: str,
        feeding_time: time,
        detection_window_minutes: int = 15,
    ) -> FeedingSchedule:
        """设置喂食计划（不存在则创建，存在则更新）"""
        schedule = (
            db.query(FeedingSchedule)
            .filter(FeedingSchedule.tank_id == tank_id)
            .first()
        )

        if schedule:
            schedule.feeding_time = feeding_time
            schedule.detection_window_minutes = detection_window_minutes
            schedule.is_enabled = True
        else:
            schedule = FeedingSchedule(
                tank_id=tank_id,
                feeding_time=feeding_time,
                detection_window_minutes=detection_window_minutes,
                is_enabled=True,
            )
            db.add(schedule)

        db.flush()
        return schedule

    @staticmethod
    def mark_as_fed(
        db: Session,
        tank_id: str,
        scheduled_time: time,
        feeding_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> FeedingRecord:
        """手动标记为已喂食"""
        feeding_date = feeding_date or datetime.utcnow().date()

        schedule = (
            db.query(FeedingSchedule)
            .filter(FeedingSchedule.tank_id == tank_id)
            .first()
        )

        record = (
            db.query(FeedingRecord)
            .filter(
                FeedingRecord.tank_id == tank_id,
                FeedingRecord.feeding_date == feeding_date,
                FeedingRecord.scheduled_time == scheduled_time,
            )
            .first()
        )

        if not record:
            record = FeedingRecord(
                tank_id=tank_id,
                feeding_date=feeding_date,
                scheduled_time=scheduled_time,
            )
            db.add(record)

        record.is_fed = True
        record.manually_marked_at = datetime.utcnow()
        record.detection_method = "manual"
        if notes:
            record.notes = notes

        db.flush()
        return record

    @staticmethod
    def get_schedule(db: Session, tank_id: str) -> Optional[FeedingSchedule]:
        """获取喂食计划"""
        return (
            db.query(FeedingSchedule)
            .filter(FeedingSchedule.tank_id == tank_id)
            .first()
        )

    @staticmethod
    def get_recent_records(
        db: Session, tank_id: str, limit: int = 7
    ) -> List[FeedingRecord]:
        """获取最近的喂食记录"""
        return (
            db.query(FeedingRecord)
            .filter(FeedingRecord.tank_id == tank_id)
            .order_by(
                FeedingRecord.feeding_date.desc(),
                FeedingRecord.scheduled_time.desc(),
            )
            .limit(limit)
            .all()
        )
