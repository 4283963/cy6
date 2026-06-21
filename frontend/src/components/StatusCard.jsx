function StatusCard({ icon, iconClass, title, value, unit, status, subtitle, isTextValue }) {
  const statusLabel = {
    normal: '正常',
    warning: '警告',
    danger: '危险',
  }

  const displayValue = value !== null && value !== undefined ? value : '--'

  return (
    <div className="status-card">
      <div className="status-card-header">
        <div className={`status-icon ${iconClass}`}>{icon}</div>
        <div>
          <div className="status-card-title">{title}</div>
          <span className={`status-badge ${status}`}>
            {statusLabel[status] || status}
          </span>
        </div>
      </div>
      <div className="status-value">
        {displayValue}
        {!isTextValue && unit && <span className="status-unit"> {unit}</span>}
      </div>
      {subtitle && <div style={{ fontSize: '13px', color: '#94a3b8' }}>{subtitle}</div>}
    </div>
  )
}

export default StatusCard
