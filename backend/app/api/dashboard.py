from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..schemas.dashboard import DashboardSummary, TankStatus, PendingCommand, FeedingStatus
from ..models import Device, ControlCommand, SensorData
from ..services.compensation import CompensationService
from ..services.feeding import FeedingService

router = APIRouter()


@router.get("/summary/{tank_id}", response_model=DashboardSummary, summary="仪表盘汇总数据")
def get_dashboard_summary(
    tank_id: str,
    db: Session = Depends(get_db),
):
    """获取仪表盘所需的汇总数据"""
    device = db.query(Device).filter(Device.tank_id == tank_id).first()

    if not device:
        device = Device(
            tank_id=tank_id,
            name=f"鱼缸-{tank_id}",
            air_pump_running=False,
            heater_running=False,
            cooler_running=False,
        )

    status = CompensationService.evaluate_tank_status(
        device.current_temp or 25.0,
        device.current_ph or 7.0,
        device.current_do or 7.0,
    )

    tank_status = TankStatus(
        tank_id=device.tank_id,
        name=device.name,
        current_temp=device.current_temp,
        current_ph=device.current_ph,
        current_do=device.current_do,
        air_pump_running=device.air_pump_running,
        heater_running=device.heater_running,
        cooler_running=device.cooler_running,
        last_heartbeat=device.last_heartbeat,
        temp_status=status["temp_status"],
        ph_status=status["ph_status"],
        do_status=status["do_status"],
    )

    pending_cmds = (
        db.query(ControlCommand)
        .filter(
            ControlCommand.tank_id == tank_id,
            ControlCommand.is_executed == False,
        )
        .order_by(ControlCommand.created_at.asc())
        .all()
    )

    pending_commands = [
        PendingCommand(
            id=cmd.id,
            device_type=cmd.device_type,
            action=cmd.action,
            duration_minutes=cmd.duration_minutes,
            reason=cmd.reason,
            created_at=cmd.created_at,
        )
        for cmd in pending_cmds
    ]

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_command_count = (
        db.query(ControlCommand)
        .filter(
            ControlCommand.tank_id == tank_id,
            ControlCommand.created_at >= today_start,
        )
        .count()
    )

    recent_sensor_count = (
        db.query(SensorData)
        .filter(
            SensorData.tank_id == tank_id,
            SensorData.recorded_at >= datetime.utcnow() - timedelta(hours=1),
        )
        .count()
    )

    feeding_status_dict = FeedingService.calculate_feeding_status(db, tank_id)
    feeding_status = FeedingStatus(**feeding_status_dict)

    return DashboardSummary(
        tank_status=tank_status,
        pending_commands=pending_commands,
        recent_sensor_count=recent_sensor_count,
        today_command_count=today_command_count,
        feeding_status=feeding_status,
    )


@router.get("/tanks", response_model=list, summary="获取所有鱼缸列表")
def get_all_tanks(db: Session = Depends(get_db)):
    """获取所有已注册的鱼缸设备列表"""
    devices = db.query(Device).all()
    return [
        {
            "tank_id": d.tank_id,
            "name": d.name,
            "online": d.last_heartbeat and d.last_heartbeat > datetime.utcnow() - timedelta(minutes=5),
        }
        for d in devices
    ]
