import assert from 'node:assert/strict'
import {
  addMistake,
  addPoints,
  checkinToday,
  clearMistake,
  getLearningExtras,
} from '../src/utils/learningExtras.js'

const memory = new Map()
global.localStorage = {
  getItem(key) {
    return memory.has(key) ? memory.get(key) : null
  },
  setItem(key, value) {
    memory.set(key, String(value))
  },
  removeItem(key) {
    memory.delete(key)
  },
}

function run() {
  const childId = 'child-test-1'

  let extras = getLearningExtras(childId)
  assert.equal(extras.points, 0)
  assert.equal(extras.streakDays, 0)
  assert.equal(extras.mistakes.length, 0)

  extras = addPoints(childId, 8)
  assert.equal(extras.points, 8)

  const firstCheckin = checkinToday(childId)
  assert.equal(firstCheckin.checked, true)
  assert.equal(firstCheckin.extras.points, 13)

  const secondCheckin = checkinToday(childId)
  assert.equal(secondCheckin.checked, false)
  assert.equal(secondCheckin.extras.points, 13)

  extras = addMistake(childId, {
    prompt: '2 + 3 = ?',
    selected: '4',
    answer: '5',
    skill: '基础计算',
  })
  assert.equal(extras.mistakes.length, 1)

  const targetId = extras.mistakes[0].id
  extras = clearMistake(childId, targetId)
  assert.equal(extras.mistakes.length, 0)
}

run()
console.log('learningExtras tests passed')

