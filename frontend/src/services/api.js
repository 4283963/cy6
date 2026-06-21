const API_BASE = '/api/v1'

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  return response.json()
}

export async function fetchDashboard(tankId) {
  return request(`/dashboard/summary/${tankId}`)
}

export async function fetchSensorHistory(tankId, limit = 100) {
  return request(`/sensor/history/${tankId}?limit=${limit}`)
}

export async function fetchPendingCommands(tankId) {
  return request(`/commands/pending/${tankId}`)
}

export async function fetchCommandHistory(tankId, limit = 50) {
  return request(`/commands/history/${tankId}?limit=${limit}`)
}

export async function submitSensorData(data) {
  return request('/sensor/collect', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function executeCommand(commandId) {
  return request('/commands/execute', {
    method: 'POST',
    body: JSON.stringify({ command_id: commandId }),
  })
}

export async function createManualCommand(tankId, deviceType, action, duration = 10) {
  const params = new URLSearchParams({
    tank_id: tankId,
    device_type: deviceType,
    action: action,
    duration_minutes: duration,
  })
  return request(`/commands/manual?${params.toString()}`, {
    method: 'POST',
  })
}

export async function fetchFeedingStatus(tankId) {
  return request(`/feeding/status/${tankId}`)
}

export async function fetchFeedingSchedule(tankId) {
  return request(`/feeding/schedule/${tankId}`)
}

export async function setFeedingSchedule(tankId, feedingTime, detectionWindowMinutes = 15) {
  return request('/feeding/schedule', {
    method: 'POST',
    body: JSON.stringify({
      tank_id: tankId,
      feeding_time: feedingTime,
      detection_window_minutes: detectionWindowMinutes,
    }),
  })
}

export async function markAsFed(tankId, scheduledTime) {
  return request('/feeding/mark', {
    method: 'POST',
    body: JSON.stringify({
      tank_id: tankId,
      scheduled_time: scheduledTime,
    }),
  })
}

export async function fetchFeedingRecords(tankId, limit = 7) {
  return request(`/feeding/records/${tankId}?limit=${limit}`)
}
