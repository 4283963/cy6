# 智能鱼缸控制系统

金鱼与白子孔雀鱼混养缸智能控制后端系统

## 项目结构

```
cy6/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── sensor_data.py      # 传感器数据
│   │   │   ├── control_command.py  # 控制指令
│   │   │   └── device.py           # 设备信息
│   │   ├── schemas/        # Pydantic 数据验证
│   │   │   ├── __init__.py
│   │   │   ├── sensor.py
│   │   │   ├── command.py
│   │   │   └── dashboard.py
│   │   ├── services/       # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   └── compensation.py     # 联合补偿逻辑
│   │   └── api/            # API 路由层
│   │       ├── __init__.py
│   │       ├── sensor.py           # 传感器数据接口
│   │       ├── command.py          # 控制指令接口
│   │       └── dashboard.py        # 仪表盘接口
│   ├── requirements.txt
│   ├── .env.example
│   ├── init_db.py          # 数据库初始化脚本
│   ├── run.py              # 启动脚本
│   └── simulate_sensor.py  # 传感器模拟器
│
└── frontend/               # React 前端仪表盘
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── index.css
    │   ├── components/
    │   │   ├── StatusCard.jsx
    │   │   ├── SensorChart.jsx
    │   │   ├── CommandPanel.jsx
    │   │   └── StatsPanel.jsx
    │   └── services/
    │       └── api.js
    ├── package.json
    ├── vite.config.js
    └── index.html
```

## 核心功能

### 1. 参数收集接口
- 接口: `POST /api/v1/sensor/collect`
- 每 30 秒接收一次传感器数据
- 数据包含: 水温、pH值、溶氧量
- 自动触发联合补偿逻辑

### 2. 联合补偿逻辑
- 基于亨利定律计算当前水温下的饱和溶氧量
- 水温升高时自动计算气泵需要额外运行的时间
- 综合考虑: 溶氧绝对量、饱和度、下降趋势、温度变化
- 智能去重: 避免短时间内重复下发相同指令

### 3. 控制指令管理
- 自动生成气泵/加热棒/冷水机控制指令
- 支持手动下发指令
- 指令执行状态追踪

### 4. 前端仪表盘
- 实时显示水温、pH、溶氧量
- 水质参数趋势图表
- 待执行指令列表
- 手动控制按钮

## 快速开始

### 环境要求
- Python 3.10+
- MySQL 8.0+
- Node.js 18+

### 后端启动

1. 进入后端目录
```bash
cd backend
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息
```

4. 初始化数据库
```bash
python init_db.py
```

5. 启动后端服务
```bash
python run.py
```

服务将在 `http://localhost:8000` 启动
API 文档: `http://localhost:8000/docs`

### 前端启动

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动

### 测试模拟

运行传感器模拟器生成测试数据:
```bash
cd backend
python simulate_sensor.py
```

## API 接口列表

### 传感器数据
- `POST /api/v1/sensor/collect` - 上传传感器数据
- `GET /api/v1/sensor/history/{tank_id}` - 获取历史数据

### 控制指令
- `GET /api/v1/commands/pending/{tank_id}` - 获取待执行指令
- `POST /api/v1/commands/execute` - 标记指令已执行
- `GET /api/v1/commands/history/{tank_id}` - 获取历史指令
- `POST /api/v1/commands/manual` - 手动下发指令

### 仪表盘
- `GET /api/v1/dashboard/summary/{tank_id}` - 获取仪表盘汇总数据
- `GET /api/v1/dashboard/tanks` - 获取鱼缸列表

## 水质参数参考

| 参数 | 适宜范围 | 警告值 | 危险值 |
|------|----------|--------|--------|
| 水温 | 22-26°C | 24-28°C | <22°C 或 >30°C |
| pH值 | 6.5-7.5 | 6.0-8.0 | <6.0 或 >8.0 |
| 溶氧 | ≥7mg/L | ≥5mg/L | <5mg/L |

## 联合补偿算法说明

### 气泵运行时长计算
基础时长 10 分钟，根据以下因素累加:

1. **溶氧低于下限**: 每低 1mg/L 增加 8 分钟
2. **溶氧低于最优值**: 每低 1mg/L 增加 3 分钟
3. **饱和度低于80%**: 每低1%增加 0.3 分钟
4. **溶氧下降趋势**: 每下降 1mg/L 增加 5 分钟
5. **水温上升**: 预计自然下降每 1mg/L 增加 4 分钟

最大时长不超过 60 分钟。

### 触发条件
- 溶氧状态为 warning 或 danger 时立即触发
- 溶氧低于最优值且 30 分钟内无待执行指令、距上次执行超过 2 小时
- 温度超限时触发加热/制冷设备
