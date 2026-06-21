from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.sensor import SensorDataCreate, SensorDataResponse
from ..models import SensorData, Device
from ..services.compensation import CompensationService

router = APIRouter()


@router.post("/collect", response_model=dict, summary="接收传感器数据")
def collect_sensor_data(
    data: SensorDataCreate,
    db: Session = Depends(get_db),
):
    """
    接收鱼缸上传的传感器数据（每30秒一次）
    - 水温、pH值、溶氧量
    - 自动触发联合补偿逻辑
    """
    sensor_record = SensorData(
        tank_id=data.tank_id,
        temperature=data.temperature,
        ph=data.ph,
        dissolved_oxygen=data.dissolved_oxygen,
    )
    db.add(sensor_record)

    device = db.query(Device).filter(Device.tank_id == data.tank_id).first()
    if device:
        device.current_temp = data.temperature
        device.current_ph = data.ph
        device.current_do = data.dissolved_oxygen
        device.last_heartbeat = datetime.utcnow()
    else:
        device = Device(
            tank_id=data.tank_id,
            name=f"鱼缸-{data.tank_id}",
            current_temp=data.temperature,
            current_ph=data.ph,
            current_do=data.dissolved_oxygen,
            last_heartbeat=datetime.utcnow(),
            air_pump_running=False,
            heater_running=False,
            cooler_running=False,
        )
        db.add(device)

    db.flush()

    new_commands = CompensationService.process_sensor_data(
        db=db,
        tank_id=data.tank_id,
        temperature=data.temperature,
        ph=data.ph,
        dissolved_oxygen=data.dissolved_oxygen,
    )

    db.commit()
    db.refresh(sensor_record)

    status = CompensationService.evaluate_tank_status(
        data.temperature, data.ph, data.dissolved_oxygen
    )

    return {
        "success": True,
        "sensor_id": sensor_record.id,
        "status": status,
        "new_commands": [
            {
                "id": cmd.id,
                "device_type": cmd.device_type,
                "action": cmd.action,
                "duration_minutes": cmd.duration_minutes,
                "reason": cmd.reason,
            }
            for cmd in new_commands
        ],
    }


@router.get("/history/{tank_id}", response_model=List[SensorDataResponse], summary="获取历史传感器数据")
def get_sensor_history(
    tank_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """获取指定鱼缸的历史传感器数据"""
    if limit > 1000:
        limit = 1000

    records = (
        db.query(SensorData)
        .filter(SensorData.tank_id == tank_id)
        .order_by(SensorData.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(records))
