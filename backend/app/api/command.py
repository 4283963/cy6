from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.command import ControlCommandResponse, CommandExecuteRequest
from ..models import ControlCommand

router = APIRouter()


@router.get("/pending/{tank_id}", response_model=List[ControlCommandResponse], summary="获取待执行指令")
def get_pending_commands(
    tank_id: str,
    db: Session = Depends(get_db),
):
    """获取指定鱼缸待执行的控制指令"""
    commands = (
        db.query(ControlCommand)
        .filter(
            ControlCommand.tank_id == tank_id,
            ControlCommand.is_executed == False,
        )
        .order_by(ControlCommand.created_at.asc())
        .all()
    )
    return commands


@router.post("/execute", response_model=ControlCommandResponse, summary="标记指令已执行")
def mark_command_executed(
    req: CommandExecuteRequest,
    db: Session = Depends(get_db),
):
    """设备端执行指令后调用此接口标记已执行"""
    cmd = db.query(ControlCommand).filter(ControlCommand.id == req.command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="指令不存在")

    cmd.is_executed = True
    cmd.executed_at = datetime.utcnow()
    db.commit()
    db.refresh(cmd)
    return cmd


@router.get("/history/{tank_id}", response_model=List[ControlCommandResponse], summary="获取历史指令")
def get_command_history(
    tank_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取指定鱼缸的历史控制指令"""
    if limit > 200:
        limit = 200

    commands = (
        db.query(ControlCommand)
        .filter(ControlCommand.tank_id == tank_id)
        .order_by(ControlCommand.created_at.desc())
        .limit(limit)
        .all()
    )
    return commands


@router.post("/manual", response_model=ControlCommandResponse, summary="手动下发指令")
def create_manual_command(
    tank_id: str,
    device_type: str,
    action: str,
    duration_minutes: int = 10,
    reason: str = "手动操作",
    db: Session = Depends(get_db),
):
    """手动下发控制指令"""
    valid_devices = ["air_pump", "heater", "cooler", "light"]
    valid_actions = ["turn_on", "turn_off"]

    if device_type not in valid_devices:
        raise HTTPException(status_code=400, detail=f"无效的设备类型，支持: {valid_devices}")
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"无效的动作，支持: {valid_actions}")

    cmd = ControlCommand(
        tank_id=tank_id,
        device_type=device_type,
        action=action,
        duration_minutes=duration_minutes if action == "turn_on" else None,
        reason=reason,
        triggered_by="manual",
        is_executed=False,
    )
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd
