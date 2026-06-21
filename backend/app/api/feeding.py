from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.feeding import (
    FeedingScheduleCreate,
    FeedingScheduleUpdate,
    FeedingScheduleResponse,
    FeedingRecordResponse,
    FeedingMarkRequest,
    FeedingStatusResponse,
)
from ..services.feeding import FeedingService

router = APIRouter()


@router.post("/schedule", response_model=FeedingScheduleResponse, summary="设置喂食时间")
def set_feeding_schedule(
    data: FeedingScheduleCreate,
    db: Session = Depends(get_db),
):
    """设置每日喂食时间计划"""
    schedule = FeedingService.set_schedule(
        db=db,
        tank_id=data.tank_id,
        feeding_time=data.feeding_time,
        detection_window_minutes=data.detection_window_minutes,
    )
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/schedule/{tank_id}", response_model=FeedingScheduleResponse, summary="获取喂食计划")
def get_feeding_schedule(
    tank_id: str,
    db: Session = Depends(get_db),
):
    """获取指定鱼缸的喂食计划"""
    schedule = FeedingService.get_schedule(db, tank_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="未找到喂食计划")
    return schedule


@router.patch("/schedule/{tank_id}", response_model=FeedingScheduleResponse, summary="更新喂食计划")
def update_feeding_schedule(
    tank_id: str,
    data: FeedingScheduleUpdate,
    db: Session = Depends(get_db),
):
    """更新喂食计划"""
    schedule = FeedingService.get_schedule(db, tank_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="未找到喂食计划")

    if data.feeding_time is not None:
        schedule.feeding_time = data.feeding_time
    if data.is_enabled is not None:
        schedule.is_enabled = data.is_enabled
    if data.detection_window_minutes is not None:
        schedule.detection_window_minutes = data.detection_window_minutes

    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/status/{tank_id}", response_model=dict, summary="获取喂食状态")
def get_feeding_status(
    tank_id: str,
    db: Session = Depends(get_db),
):
    """获取当前喂食状态（用于前端显示）"""
    status = FeedingService.calculate_feeding_status(db, tank_id)
    return status


@router.post("/mark", response_model=FeedingRecordResponse, summary="手动标记已喂食")
def mark_as_fed(
    data: FeedingMarkRequest,
    db: Session = Depends(get_db),
):
    """手动标记为已喂食"""
    record = FeedingService.mark_as_fed(
        db=db,
        tank_id=data.tank_id,
        scheduled_time=data.scheduled_time,
        feeding_date=data.feeding_date,
        notes=data.notes,
    )
    db.commit()
    db.refresh(record)
    return record


@router.get("/records/{tank_id}", response_model=List[FeedingRecordResponse], summary="获取喂食记录")
def get_feeding_records(
    tank_id: str,
    limit: int = 7,
    db: Session = Depends(get_db),
):
    """获取最近的喂食记录"""
    if limit > 30:
        limit = 30
    records = FeedingService.get_recent_records(db, tank_id, limit)
    return records
