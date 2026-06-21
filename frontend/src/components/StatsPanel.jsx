function StatsPanel({ dashboardData, lastUpdate }) {
  const formatTime = (date) => {
    if (!date) return '--'
    return date.toLocaleString('zh-CN')
  }

  const formatHeartbeat = (isoString) => {
    if (!isoString) return '从未连接'
    const diff = Date.now() - new Date(isoString).getTime()
    const minutes = Math.floor(diff / 60000)
    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes} 分钟前`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} 小时前`
    return new Date(isoString).toLocaleDateString('zh-CN')
  }

  return (
    <div className="command-panel">
      <h2 className="section-title">📈 系统概览</h2>

      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-value">{dashboardData?.recent_sensor_count || 0}</div>
          <div className="stat-label">近1小时数据点</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{dashboardData?.today_command_count || 0}</div>
          <div className="stat-label">今日指令数</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{dashboardData?.pending_commands?.length || 0}</div>
          <div className="stat-label">待执行指令</div>
        </div>
        <div className="stat-item">
          <div className="stat-value" style={{ fontSize: '16px' }}>
            {formatHeartbeat(dashboardData?.tank_status?.last_heartbeat)}
          </div>
          <div className="stat-label">最后心跳</div>
        </div>
      </div>

      <div className="last-update">
        最后更新: {formatTime(lastUpdate)}
        <br />
        <span style={{ fontSize: '12px', color: '#64748b' }}>
          每 10 秒自动刷新
        </span>
      </div>

      <div
        style={{
          marginTop: '20px',
          padding: '16px',
          background: 'rgba(56, 189, 248, 0.1)',
          borderRadius: '12px',
          border: '1px solid rgba(56, 189, 248, 0.2)',
        }}
      >
        <h4 style={{ fontSize: '14px', color: '#38bdf8', marginBottom: '8px' }}>
          💡 系统说明
        </h4>
        <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.6 }}>
          系统每 30 秒接收一次传感器数据，自动分析水温、pH、溶氧量。
          当水温升高导致溶氧下降时，会自动计算气泵增氧时长并下发指令。
          金鱼和白子孔雀鱼适宜水温 22-26°C，pH 6.5-7.5，溶氧 ≥ 5mg/L。
        </p>
      </div>
    </div>
  )
}

export default StatsPanel
