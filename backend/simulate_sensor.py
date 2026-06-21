#!/usr/bin/env python3
"""
模拟传感器数据发送脚本
用于测试智能鱼缸控制系统
每 30 秒发送一次数据，模拟真实传感器

按 'f' 键 + 回车可以模拟喂食扰动（触发喂食检测）
"""
import time
import random
import math
import requests
import threading
import sys
from datetime import datetime

API_URL = "http://localhost:8000/api/v1/sensor/collect"
TANK_ID = "main_tank_01"
INTERVAL = 30


class SensorSimulator:
    def __init__(self):
        self.base_temp = 25.0
        self.base_ph = 7.0
        self.base_do = 7.5
        self.tick = 0
        self.feeding_mode = False
        self.feeding_ticks = 0

    def calculate_do_saturation(self, temp_c):
        t = temp_c
        do_sat = (
            14.652
            - 0.41022 * t
            + 0.007991 * (t ** 2)
            - 0.000077774 * (t ** 3)
        )
        return max(0.0, do_sat)

    def trigger_feeding(self):
        """触发喂食扰动模拟"""
        self.feeding_mode = True
        self.feeding_ticks = 5
        print("\n🍽️  已触发喂食扰动模拟！\n")

    def generate_data(self):
        self.tick += 1

        temp_variation = 2.0 * math.sin(self.tick * 0.05)
        temp_noise = random.uniform(-0.2, 0.2)
        temperature = self.base_temp + temp_variation + temp_noise

        ph_variation = 0.3 * math.sin(self.tick * 0.03 + 1)
        ph_noise = random.uniform(-0.05, 0.05)
        ph = self.base_ph + ph_variation + ph_noise

        do_sat = self.calculate_do_saturation(temperature)
        do_ratio = 0.6 + 0.35 * math.sin(self.tick * 0.04 + 2)
        do_noise = random.uniform(-0.1, 0.1)
        dissolved_oxygen = do_sat * do_ratio + do_noise

        if self.feeding_mode and self.feeding_ticks > 0:
            self.feeding_ticks -= 1
            feeding_phase = 5 - self.feeding_ticks
            if feeding_phase <= 2:
                do_drop = 0.8 * (feeding_phase / 2)
                dissolved_oxygen -= do_drop
                temp_noise_extra = random.uniform(0, 0.3)
                temperature += temp_noise_extra
                ph_noise_extra = random.uniform(-0.08, 0.02)
                ph += ph_noise_extra
            else:
                do_rise = 0.6 * ((feeding_phase - 2) / 3)
                dissolved_oxygen += do_rise

            if self.feeding_ticks == 0:
                self.feeding_mode = False

        temperature = max(22.0, min(32.0, temperature))
        ph = max(6.0, min(8.5, ph))
        dissolved_oxygen = max(3.0, min(12.0, dissolved_oxygen))

        return {
            "tank_id": TANK_ID,
            "temperature": round(temperature, 2),
            "ph": round(ph, 2),
            "dissolved_oxygen": round(dissolved_oxygen, 2),
            "simulated_feeding": self.feeding_mode,
        }

    def send_data(self, data):
        try:
            response = requests.post(API_URL, json=data, timeout=5)
            response.raise_for_status()
            result = response.json()
            status = result.get("status", {})
            new_cmds = result.get("new_commands", [])
            feeding_info = result.get("feeding", {})
            feeding_alert = result.get("feeding_alert", "")

            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"水温: {data['temperature']:.2f}°C | "
                  f"pH: {data['ph']:.2f} | "
                  f"溶氧: {data['dissolved_oxygen']:.2f}mg/L | "
                  f"状态: 温度={status.get('temp_status')} "
                  f"pH={status.get('ph_status')} "
                  f"溶氧={status.get('do_status')}")

            if feeding_info and feeding_info.get("in_window"):
                status_text = "检测中"
                if feeding_info.get("already_fed"):
                    status_text = "✓ 今日已喂"
                elif feeding_info.get("detected"):
                    status_text = "✓ 检测到喂食"
                print(f"  🍽️  喂食窗口: {status_text}, 评分: {feeding_info.get('score', 0)}")

            if feeding_alert:
                print(f"  {feeding_alert}")

            if new_cmds:
                print(f"  → 生成 {len(new_cmds)} 条新指令:")
                for cmd in new_cmds:
                    print(f"    - {cmd['device_type']} {cmd['action']} "
                          f"{cmd.get('duration_minutes', '')}分钟")
                    print(f"      原因: {cmd.get('reason', '')}")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送失败: {e}")
            return False


def input_listener(simulator):
    """监听键盘输入，按 f 触发喂食模拟"""
    while True:
        try:
            line = sys.stdin.readline().strip().lower()
            if line == 'f':
                simulator.trigger_feeding()
            elif line == 'q':
                print("\n正在退出...")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            break


def main():
    print("=" * 60)
    print("🐠 智能鱼缸传感器模拟器")
    print("=" * 60)
    print(f"目标地址: {API_URL}")
    print(f"鱼缸ID: {TANK_ID}")
    print(f"发送间隔: {INTERVAL}秒")
    print("-" * 60)
    print("操作: 按 'f' + 回车 = 模拟喂食扰动")
    print("      按 'q' + 回车 = 退出程序")
    print("=" * 60)
    print()

    simulator = SensorSimulator()
    count = 0

    input_thread = threading.Thread(target=input_listener, args=(simulator,), daemon=True)
    input_thread.start()

    try:
        while True:
            data = simulator.generate_data()
            if simulator.send_data(data):
                count += 1
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print(f"\n\n共发送 {count} 条数据")
        print("程序已停止")


if __name__ == "__main__":
    main()
