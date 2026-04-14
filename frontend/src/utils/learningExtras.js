const STORAGE_KEY = 'ydxb_learning_extras_v1'

function todayKey() {
  return new Date().toISOString().slice(0, 10)
}

function readStore() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function writeStore(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
}

function ensureChild(store, childId) {
  if (!store[childId]) {
    store[childId] = {
      points: 0,
      checkins: [],
      mistakes: [],
    }
  }
  return store[childId]
}

export function getLearningExtras(childId) {
  if (!childId) return { points: 0, streakDays: 0, checkins: [], mistakes: [] }
  const store = readStore()
  const data = ensureChild(store, childId)
  const streakDays = calcStreakDays(data.checkins || [])
  return {
    points: Number(data.points || 0),
    streakDays,
    checkins: data.checkins || [],
    mistakes: data.mistakes || [],
  }
}

export function addPoints(childId, delta) {
  if (!childId || !delta) return getLearningExtras(childId)
  const store = readStore()
  const data = ensureChild(store, childId)
  data.points = Math.max(0, Number(data.points || 0) + Number(delta || 0))
  writeStore(store)
  return getLearningExtras(childId)
}

export function checkinToday(childId) {
  if (!childId) return { checked: false, extras: getLearningExtras(childId) }
  const store = readStore()
  const data = ensureChild(store, childId)
  const key = todayKey()
  const exists = (data.checkins || []).includes(key)
  if (!exists) {
    data.checkins = [...(data.checkins || []), key]
    data.points = Math.max(0, Number(data.points || 0) + 5)
    writeStore(store)
  }
  return { checked: !exists, extras: getLearningExtras(childId) }
}

export function addMistake(childId, item) {
  if (!childId || !item) return getLearningExtras(childId)
  const store = readStore()
  const data = ensureChild(store, childId)
  const mistakes = data.mistakes || []
  mistakes.unshift({
    id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    created_at: new Date().toISOString(),
    ...item,
  })
  data.mistakes = mistakes.slice(0, 100)
  writeStore(store)
  return getLearningExtras(childId)
}

export function clearMistake(childId, mistakeId) {
  if (!childId || !mistakeId) return getLearningExtras(childId)
  const store = readStore()
  const data = ensureChild(store, childId)
  data.mistakes = (data.mistakes || []).filter((item) => item.id !== mistakeId)
  writeStore(store)
  return getLearningExtras(childId)
}

export function exportLearningReport(payload, filename = 'yuedu-learning-report.json') {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

function calcStreakDays(checkins) {
  const set = new Set(checkins || [])
  let cursor = new Date()
  let streak = 0
  while (true) {
    const key = cursor.toISOString().slice(0, 10)
    if (!set.has(key)) break
    streak += 1
    cursor.setDate(cursor.getDate() - 1)
  }
  return streak
}

