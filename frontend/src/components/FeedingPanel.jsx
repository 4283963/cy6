import { useState } from 'react'
import { setFeedingSchedule, markAsFed } from '../services/api'

function FeedingPanel({ feedingStatus, tankId, onFeedingUpdated }) {
  const [showModal, setShowModal] = useState(false)
  const [feedingTime, setFeedingTime] = useState(
    feedingStatus?.feeding_time || '14:00'
  )
  const [saving, setSaving] = useState(false)

  const formatTime = (timeStr) => {
    if (!timeStr) return '--:--'
    const parts = timeStr.split(':')
    return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`
  }

  const handleSaveSchedule = async () => {
    if (!feedingTime) return
    setSaving(true)
    try {
      await setFeedingSchedule(tankId, feedingTime, 15)
      setShowModal(false)
      onFeedingUpdated?.()
    } catch (err) {
      alert('保存失败: ' + err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleMarkAsFed = async () => {
    if (!feedingStatus?.feeding_time) return
    try {
      await markAsFed(tankId, feedingStatus.feeding_time)
      onFeedingUpdated?.()
    } catch (err) {
      alert('标记失败: ' + err.message)
    }
  }

  const getStatusText = () => {
    if (!feedingStatus || !feedingStatus.has_schedule) {
      return '未设置喂食时间'
    }
    if (feedingStatus.today_is_fed) {
      const fedTime = feedingStatus.fed_time
        ? new Date(feedingStatus.fed_time).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })
        : ''
      const method = feedingStatus.detection_method === 'auto' ? '自动检测' : '手动标记'
      return `✓ 今日已喂食 (${method} ${fedTime})`
    }
    if (feedingStatus.should_remind) {
      return `⚠️ 该喂小鱼了！已过喂食时间 ${feedingStatus.minutes_since_feeding} 分钟`
    }
    if (feedingStatus.minutes_until_feeding !== null) {
      return `距下次喂食还有 ${feedingStatus.minutes_until_feeding} 分钟`
    }
    if (feedingStatus.is_feeding_window_open) {
      return '🔍 正在检测喂食活动...'
    }
    return `每日喂食时间: ${formatTime(feedingStatus.feeding_time)}`
  }

  const getStatusColor = () => {
    if (!feedingStatus || !feedingStatus.has_schedule) return '#64748b'
    if (feedingStatus.today_is_fed) return '#34d399'
    if (feedingStatus.should_remind) return '#f97316'
    if (feedingStatus.is_feeding_window_open) return '#38bdf8'
    return '#94a3b8'
  }

  return (
    <div
      className="command-panel"
      style={{
        border: feedingStatus?.should_remind
          ? '2px solid #f97316'
          : undefined,
        background: feedingStatus?.should_remind
          ? 'rgba(249, 115, 22, 0.1)'
          : undefined,
      }}
    >
      <h2 className="section-title">🍽️ 喂食提醒</h2>

      <div
        style={{
          textAlign: 'center',
          padding: '24px 0',
        }}
      >
        <div
          style={{
            fontSize: '48px',
            marginBottom: '8px',
          }}
        >
          {feedingStatus?.today_is_fed ? '✅' : feedingStatus?.should_remind ? '⏰' : '🐟'}
        </div>
        <div
          style={{
            fontSize: '16px',
            fontWeight: 600,
            color: getStatusColor(),
            marginBottom: '8px',
          }}
        >
          {getStatusText()}
        </div>
        {feedingStatus?.has_schedule && (
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            今日 {formatTime(feedingStatus.feeding_time)} · 检测窗口 {feedingStatus.detection_window_minutes} 分钟
          </div>
        )}
      </div>

      <div className="manual-controls">
        <button className="control-btn" onClick={() => setShowModal(true)}>
          {feedingStatus?.has_schedule ? '修改喂食时间' : '设置喂食时间'}
        </button>
        {!feedingStatus?.today_is_fed && feedingStatus?.has_schedule && (
          <button
            className="control-btn"
            onClick={handleMarkAsFed}
            style={{
              background: 'linear-gradient(135deg, #f97316, #ea580c)',
            }}
          >
            手动标记已喂
          </button>
        )}
      </div>

      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowModal(false)}
        >
          <div
            style={{
              background: '#1e293b',
              borderRadius: '16px',
              padding: '24px',
              width: '90%',
              maxWidth: '400px',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                fontSize: '18px',
                fontWeight: 600,
                marginBottom: '16px',
                color: '#e2e8f0',
              }}
            >
              设置每日喂食时间
            </h3>
            <div style={{ marginBottom: '16px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '14px',
                  color: '#94a3b8',
                  marginBottom: '8px',
                }}
              >
                喂食时间
              </label>
              <input
                type="time"
                value={feedingTime}
                onChange={(e) => setFeedingTime(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255,255,255,0.2)',
                  background: 'rgba(255,255,255,0.1)',
                  color: '#e2e8f0',
                  fontSize: '16px',
                  outline: 'none',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255,255,255,0.2)',
                  background: 'transparent',
                  color: '#94a3b8',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                取消
              </button>
              <button
                onClick={handleSaveSchedule}
                disabled={saving}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #38bdf8, #6366f1)',
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FeedingPanel
