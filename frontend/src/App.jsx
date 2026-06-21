import { useState, useEffect } from 'react'
import StatusCard from './components/StatusCard'
import SensorChart from './components/SensorChart'
import CommandPanel from './components/CommandPanel'
import StatsPanel from './components/StatsPanel'
import { fetchDashboard, fetchSensorHistory, fetchPendingCommands } from './services/api'

const DEFAULT_TANK_ID = 'main_tank_01'

function App() {
  const [tankId, setTankId] = useState(DEFAULT_TANK_ID)
  const [dashboardData, setDashboardData] = useState(null)
  const [sensorHistory, setSensorHistory] = useState([])
  const [pendingCommands, setPendingCommands] = useState([])
  const [lastUpdate, setLastUpdate] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      const [dashboard, history, commands] = await Promise.all([
        fetchDashboard(tankId),
        fetchSensorHistory(tankId, 60),
        fetchPendingCommands(tankId),
      ])
      setDashboardData(dashboard)
      setSensorHistory(history)
      setPendingCommands(commands)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('加载数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [tankId])

  const tankStatus = dashboardData?.tank_status || {
    tank_id: tankId,
    name: '主鱼缸',
    current_temp: null,
    current_ph: null,
    current_do: null,
    temp_status: 'normal',
    ph_status: 'normal',
    do_status: 'normal',
    air_pump_running: false,
    heater_running: false,
    cooler_running: false,
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">🐠 智能鱼缸监控系统</h1>
        <div className="tank-selector">
          <label>鱼缸选择:</label>
          <select value={tankId} onChange={(e) => setTankId(e.target.value)}>
            <option value="main_tank_01">主鱼缸 - 金鱼&孔雀鱼</option>
          </select>
        </div>
      </header>

      <div className="status-grid">
        <StatusCard
          icon="🌡️"
          iconClass="temp"
          title="水温"
          value={tankStatus.current_temp}
          unit="°C"
          status={tankStatus.temp_status}
          subtitle={`金鱼适宜: 22-26°C`}
        />
        <StatusCard
          icon="🧪"
          iconClass="ph"
          title="pH 值"
          value={tankStatus.current_ph}
          unit=""
          status={tankStatus.ph_status}
          subtitle={`适宜范围: 6.5-7.5`}
        />
        <StatusCard
          icon="💧"
          iconClass="oxygen"
          title="溶氧量"
          value={tankStatus.current_do}
          unit="mg/L"
          status={tankStatus.do_status}
          subtitle={`建议 ≥ 5mg/L`}
        />
        <StatusCard
          icon="🫧"
          iconClass="pump"
          title="气泵状态"
          value={tankStatus.air_pump_running ? '运行中' : '待机'}
          unit=""
          status={tankStatus.air_pump_running ? 'normal' : 'warning'}
          subtitle={
            <div className="device-status-row">
              <span className={`device-indicator ${tankStatus.air_pump_running ? 'active' : ''}`}></span>
              <span className="device-label">气泵</span>
              <span className={`device-indicator ${tankStatus.heater_running ? 'active' : ''}`}></span>
              <span className="device-label">加热棒</span>
              <span className={`device-indicator ${tankStatus.cooler_running ? 'active' : ''}`}></span>
              <span className="device-label">冷水机</span>
            </div>
          }
          isTextValue={true}
        />
      </div>

      <div className="chart-section">
        <h2 className="section-title">📊 水质参数趋势（最近30分钟）</h2>
        <SensorChart data={sensorHistory} />
      </div>

      <div className="bottom-section">
        <CommandPanel
          commands={pendingCommands}
          tankId={tankId}
          onCommandExecuted={loadData}
        />
        <StatsPanel dashboardData={dashboardData} lastUpdate={lastUpdate} />
      </div>
    </div>
  )
}

export default App
