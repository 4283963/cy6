import math
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..config import get_settings
from ..models import SensorData, ControlCommand, Device
from ..database import SessionLocal

settings = get_settings()


class CompensationService:

    @staticmethod
    def calculate_do_saturation(temp_c: float) -> float:
        """
        计算当前水温下的饱和溶氧量 (mg/L)
        使用经验公式: DO_sat = 14.652 - 0.41022*T + 0.007991*T^2 - 0.000077774*T^3
        """
        t = temp_c
        do_sat = (
            14.652
            - 0.41022 * t
            + 0.007991 * (t ** 2)
            - 0.000077774 * (t ** 3)
        )
        return max(0.0, do_sat)

    @staticmethod
    def calculate_do_deficit(
        current_do: float, current_temp: float
    ) -> Tuple[float, float]:
        """
        计算溶氧亏缺
        返回: (亏缺量 mg/L, 饱和度百分比)
        """
        do_sat = CompensationService.calculate_do_saturation(current_temp)
        if do_sat <= 0:
            return 0.0, 0.0
        deficit = do_sat - current_do
        saturation_pct = (current_do / do_sat) * 100.0
        return deficit, saturation_pct

    @staticmethod
    def calculate_air_pump_duration(
        current_do: float,
        current_temp: float,
        previous_do: Optional[float] = None,
        previous_temp: Optional[float] = None,
    ) -> Tuple[int, str]:
        """
        计算气泵需要运行的额外时间（分钟）
        考虑因素：
        1. 当前溶氧量与下限的差距
        2. 温度升高导致的溶氧自然下降
        3. 溶氧下降趋势

        返回: (持续时间分钟, 原因描述)
        """
        base_duration = settings.air_pump_base_duration
        max_duration = settings.air_pump_max_duration
        do_lower_limit = settings.do_lower_limit
        optimal_do = settings.optimal_do

        reasons = []

        do_deficit, saturation_pct = CompensationService.calculate_do_deficit(
            current_do, current_temp
        )

        duration = base_duration

        if current_do < do_lower_limit:
            gap = do_lower_limit - current_do
            extra = int(math.ceil(gap * 8))
            duration += extra
            reasons.append(
                f"溶氧 {current_do:.2f}mg/L 低于下限 {do_lower_limit}mg/L，差距 {gap:.2f}mg/L"
            )

        if current_do < optimal_do:
            gap = optimal_do - current_do
            extra = int(math.ceil(gap * 3))
            duration += extra
            reasons.append(
                f"溶氧 {current_do:.2f}mg/L 低于最优值 {optimal_do}mg/L"
            )

        if saturation_pct < 80:
            extra = int(math.ceil((80 - saturation_pct) * 0.3))
            duration += extra
            reasons.append(f"溶氧饱和度 {saturation_pct:.1f}% 低于80%")

        if previous_do is not None and previous_temp is not None:
            do_drop = previous_do - current_do
            temp_rise = current_temp - previous_temp

            if do_drop > 0:
                extra = int(math.ceil(do_drop * 5))
                duration += extra
                reasons.append(f"溶氧呈下降趋势，下降了 {do_drop:.2f}mg/L")

            if temp_rise > 0.5:
                expected_do_drop = (
                    CompensationService.calculate_do_saturation(previous_temp)
                    - CompensationService.calculate_do_saturation(current_temp)
                )
                if expected_do_drop > 0.1:
                    extra = int(math.ceil(expected_do_drop * 4))
                    duration += extra
                    reasons.append(
                        f"水温上升 {temp_rise:.1f}°C，预计溶氧自然下降 {expected_do_drop:.2f}mg/L"
                    )

        duration = min(duration, max_duration)
        duration = max(duration, 0)

        reason_text = (
            "；".join(reasons) if reasons else "常规维护性增氧"
        )

        return duration, reason_text

    @staticmethod
    def evaluate_tank_status(
        temperature: float, ph: float, dissolved_oxygen: float
    ) -> dict:
        """
        评估鱼缸整体状态
        返回各参数的状态: normal / warning / danger
        """
        temp_status = "normal"
        if (
            temperature >= settings.temp_upper_limit
            or temperature <= settings.temp_lower_limit
        ):
            temp_status = "danger"
        elif temperature >= settings.temp_upper_limit - 2:
            temp_status = "warning"
        elif temperature <= settings.temp_lower_limit + 2:
            temp_status = "warning"

        ph_status = "normal"
        if ph >= settings.ph_upper_limit or ph <= settings.ph_lower_limit:
            ph_status = "danger"
        elif ph >= settings.ph_upper_limit - 0.5:
            ph_status = "warning"
        elif ph <= settings.ph_lower_limit + 0.5:
            ph_status = "warning"

        do_status = "normal"
        do_sat = CompensationService.calculate_do_saturation(temperature)
        do_saturation_pct = (dissolved_oxygen / do_sat * 100) if do_sat > 0 else 0

        if dissolved_oxygen < settings.do_lower_limit or do_saturation_pct < 60:
            do_status = "danger"
        elif dissolved_oxygen < settings.optimal_do or do_saturation_pct < 80:
            do_status = "warning"

        return {
            "temp_status": temp_status,
            "ph_status": ph_status,
            "do_status": do_status,
            "do_saturation_pct": round(do_saturation_pct, 1),
        }

    @staticmethod
    def process_sensor_data(
        db: Session,
        tank_id: str,
        temperature: float,
        ph: float,
        dissolved_oxygen: float,
    ) -> List[ControlCommand]:
        """
        处理传感器数据，触发联合补偿逻辑
        返回生成的控制指令列表
        """
        new_commands = []

        previous_data = (
            db.query(SensorData)
            .filter(SensorData.tank_id == tank_id)
            .order_by(SensorData.recorded_at.desc())
            .offset(1)
            .limit(1)
            .first()
        )

        previous_do = previous_data.dissolved_oxygen if previous_data else None
        previous_temp = previous_data.temperature if previous_data else None

        duration, reason = CompensationService.calculate_air_pump_duration(
            current_do=dissolved_oxygen,
            current_temp=temperature,
            previous_do=previous_do,
            previous_temp=previous_temp,
        )

        status = CompensationService.evaluate_tank_status(temperature, ph, dissolved_oxygen)

        should_trigger = False
        if status["do_status"] in ("warning", "danger"):
            should_trigger = True
        elif dissolved_oxygen < settings.optimal_do:
            pending_count = (
                db.query(ControlCommand)
                .filter(
                    ControlCommand.tank_id == tank_id,
                    ControlCommand.device_type == "air_pump",
                    ControlCommand.is_executed == False,
                    ControlCommand.created_at > datetime.utcnow() - timedelta(minutes=30),
                )
                .count()
            )
            if pending_count == 0:
                last_executed = (
                    db.query(ControlCommand)
                    .filter(
                        ControlCommand.tank_id == tank_id,
                        ControlCommand.device_type == "air_pump",
                        ControlCommand.is_executed == True,
                    )
                    .order_by(ControlCommand.executed_at.desc())
                    .first()
                )
                if not last_executed or (
                    last_executed.executed_at
                    and last_executed.executed_at < datetime.utcnow() - timedelta(hours=2)
                ):
                    should_trigger = True

        if should_trigger and duration > 0:
            pending_air_pump = (
                db.query(ControlCommand)
                .filter(
                    ControlCommand.tank_id == tank_id,
                    ControlCommand.device_type == "air_pump",
                    ControlCommand.is_executed == False,
                )
                .first()
            )

            if not pending_air_pump:
                cmd = ControlCommand(
                    tank_id=tank_id,
                    device_type="air_pump",
                    action="turn_on",
                    duration_minutes=duration,
                    reason=reason,
                    triggered_by="auto",
                    is_executed=False,
                )
                db.add(cmd)
                new_commands.append(cmd)

        if status["temp_status"] == "danger":
            if temperature > settings.temp_upper_limit:
                pending_cooler = (
                    db.query(ControlCommand)
                    .filter(
                        ControlCommand.tank_id == tank_id,
                        ControlCommand.device_type == "cooler",
                        ControlCommand.is_executed == False,
                    )
                    .first()
                )
                if not pending_cooler:
                    cmd = ControlCommand(
                        tank_id=tank_id,
                        device_type="cooler",
                        action="turn_on",
                        duration_minutes=30,
                        reason=f"水温 {temperature:.1f}°C 超过上限 {settings.temp_upper_limit}°C",
                        triggered_by="auto",
                        is_executed=False,
                    )
                    db.add(cmd)
                    new_commands.append(cmd)
            elif temperature < settings.temp_lower_limit:
                pending_heater = (
                    db.query(ControlCommand)
                    .filter(
                        ControlCommand.tank_id == tank_id,
                        ControlCommand.device_type == "heater",
                        ControlCommand.is_executed == False,
                    )
                    .first()
                )
                if not pending_heater:
                    cmd = ControlCommand(
                        tank_id=tank_id,
                        device_type="heater",
                        action="turn_on",
                        duration_minutes=30,
                        reason=f"水温 {temperature:.1f}°C 低于下限 {settings.temp_lower_limit}°C",
                        triggered_by="auto",
                        is_executed=False,
                    )
                    db.add(cmd)
                    new_commands.append(cmd)

        db.flush()

        return new_commands
