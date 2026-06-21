import { useState } from 'react'
import { createManualCommand, executeCommand } from '../services/api'

const deviceNames = {
  air_pump: '气泵',
  heater: '加热棒',
  cooler: '冷水机',
  light: '灯光',
}

const actionNames = {
  turn_on: '开启',
  turn_off: '关闭',
}

function CommandPanel({ commands, tankId, onCommandExecuted }) {
  const [sending, setSending] = useState(false)

  const handleManualCommand = async (deviceType, action) => {
    if (sending) return
    setSending(true)
    try {
      await createManualCommand(tankId, deviceType, action, 15)
      onCommandExecuted?.()
    } catch (err) {
      alert('下发指令失败: ' + err.message)
    } finally {
      setSending(false)
    }
  }

  const handleExecute = async (commandId) => {
    try {
      await executeCommand(commandId)
      onCommandExecuted?.()
    } catch (err) {
      alert('执行失败: ' + err.message)
    }
  }

  return (
    <div className="command-panel">
      <h2 className="section-title">📋 待执行指令</h2>

      <div className="command-list">
        {commands.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '32px 0',
              color: '#64748b',
            }}
          >
            暂无待执行指令
          </div>
        ) : (
          commands.map((cmd) => (
            <div key={cmd.id} className="command-item">
              <div className="command-header">
                <span className="command-device">
                  {deviceNames[cmd.device_type] || cmd.device_type}
                </span>
                <span className={`command-action ${cmd.action}`}>
                  {actionNames[cmd.action] || cmd.action}
                  {cmd.duration_minutes && ` ${cmd.duration_minutes}分钟`}
                </span>
              </div>
              <div className="command-reason">{cmd.reason}</div>
              <div className="command-meta">
                <span>
                  触发方式: {cmd.triggered_by === 'auto' ? '自动' : '手动'}
                </span>
                <span>
                  创建时间: {new Date(cmd.created_at).toLocaleString('zh-CN')}
                </span>
              </div>
              <button
                onClick={() => handleExecute(cmd.id)}
                style={{
                  marginTop: '12px',
                  width: '100%',
                  padding: '8px',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #38bdf8, #6366f1)',
                  color: 'white',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                标记为已执行
              </button>
            </div>
          ))
        )}
      </div>

      <h3
        style={{
          fontSize: '15px',
          fontWeight: 600,
          marginTop: '24px',
          marginBottom: '12px',
          paddingTop: '16px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        手动控制
      </h3>
      <div className="manual-controls">
        <button
          className="control-btn"
          onClick={() => handleManualCommand('air_pump', 'turn_on')}
          disabled={sending}
        >
          开气泵 15分钟
        </button>
        <button
          className="control-btn"
          onClick={() => handleManualCommand('air_pump', 'turn_off')}
          disabled={sending}
        >
          关气泵
        </button>
        <button
          className="control-btn"
          onClick={() => handleManualCommand('heater', 'turn_on')}
          disabled={sending}
        >
          开加热棒
        </button>
        <button
          className="control-btn"
          onClick={() => handleManualCommand('cooler', 'turn_on')}
          disabled={sending}
        >
          开冷水机
        </button>
      </div>
    </div>
  )
}

export default CommandPanel
