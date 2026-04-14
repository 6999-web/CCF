<template>
  <aside class="xiaoyue-wrap" :class="[`is-${mode}`, `state-${state.toLowerCase()}`, { 'has-dialog': showDialog }]" :style="wrapStyle">
    
    <div class="tiger-container drag-handle" @pointerdown="startDrag" @pointermove="onDrag" @pointerup="endDrag" @pointercancel="endDrag" @click="toggleDialog">
      <TigerCharacter
        :mode="mode"
        :state="state"
        :gesture="gesture"
        :expression="expression"
        :viseme="viseme"
        :show-stars="showStars"
        :blinked="blinked"
      />
    </div>

    <div v-show="showDialog" class="xiaoyue-card" @pointerdown.stop>
      <div class="xiaoyue-head">
        <div class="head-main">
          <span class="tag">白老虎数字人</span>
          <strong>小悦</strong>
        </div>
        <div class="head-actions">
          <button class="tiny-btn" @click.stop="toggleDialog">关闭</button>
        </div>
      </div>

      <p class="subtitle">{{ subtitle }}</p>
      <p class="hint" v-if="focusedWord">正在引导认字：{{ focusedWord }}</p>

      <div class="chat-log" v-if="chatHistory.length">
        <div v-for="item in visibleChatHistory" :key="item.id" class="chat-item" :class="`role-${item.role}`">
          <span class="chat-role">{{ item.role === 'user' ? '我' : '小悦' }}</span>
          <span class="chat-text">{{ item.text }}</span>
        </div>
      </div>

      <div class="chat-row">
        <input
          v-model="chatInput"
          class="chat-input"
          type="text"
          placeholder="和小悦聊一聊..."
          @keydown.enter.prevent="askQuestion"
        />
        <button class="chat-send" :disabled="chatSending" @click="askQuestion">{{ chatSending ? '发送中' : '发送' }}</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import TigerCharacter from './TigerCharacter.vue'
import { api } from '../services/api'
import { state as authState } from '../store/auth'
import { XiaoyueTigerCompanion, XiaoyueTigerStates } from '../utils/xiaoyueTigerCompanion'

const state = ref(XiaoyueTigerStates.IDLE)
const subtitle = ref('你好呀，我是小悦，我们一起轻松学习。')
const mode = ref('day')
const gesture = ref('idle')
const showStars = ref(false)
const focusedWord = ref('')
const blinked = ref(false)
const showDialog = ref(false)

const chatInput = ref('')
const chatSending = ref(false)
const chatHistory = ref([])

const viseme = reactive({
  openness: 0,
  shape: 'rest',
})

const expression = reactive({
  eye: 'neutral',
  brow: 'neutral',
  emotion: 'gentle',
})

let controller
let blinkTimer
let gestureTimer
let dragMoved = false

const dragState = reactive({
  active: false,
  offsetX: 0,
  offsetY: 0,
  x: null,
  y: null,
  startX: 0,
  startY: 0,
})

const wrapStyle = computed(() => {
  if (dragState.x === null || dragState.y === null) return {}
  return {
    left: `${dragState.x}px`,
    top: `${dragState.y}px`,
    right: 'auto',
    bottom: 'auto',
  }
})

const visibleChatHistory = computed(() => chatHistory.value.slice(-6))

function persistDragPosition() {
  if (dragState.x === null || dragState.y === null) return
  localStorage.setItem('xiaoyue_drag_pos_v2', JSON.stringify({ x: dragState.x, y: dragState.y }))
}

function restoreDragPosition() {
  try {
    const raw = localStorage.getItem('xiaoyue_drag_pos_v2')
    if (!raw) return
    const data = JSON.parse(raw)
    if (typeof data.x === 'number' && typeof data.y === 'number') {
      dragState.x = data.x
      dragState.y = data.y
    }
  } catch {
    // ignore
  }
}

function persistUiState() {
  localStorage.setItem('xiaoyue_ui_state_v2', JSON.stringify({ showDialog: showDialog.value }))
}

function restoreUiState() {
  try {
    const raw = localStorage.getItem('xiaoyue_ui_state_v2')
    if (!raw) return
    const data = JSON.parse(raw)
    showDialog.value = Boolean(data?.showDialog)
  } catch {
    // ignore
  }
}

function toggleDialog() {
  if (dragMoved) return // don't toggle if we were dragging
  showDialog.value = !showDialog.value
  persistUiState()
}

function startDrag(event) {
  const card = event.currentTarget?.closest('.xiaoyue-wrap')
  if (!card) return
  const rect = card.getBoundingClientRect()
  dragState.active = true
  dragMoved = false
  dragState.offsetX = event.clientX - rect.left
  dragState.offsetY = event.clientY - rect.top
  dragState.x = rect.left
  dragState.y = rect.top
  dragState.startX = event.clientX
  dragState.startY = event.clientY
  event.currentTarget.setPointerCapture(event.pointerId)
}

function onDrag(event) {
  if (!dragState.active) return
  const dist = Math.hypot(event.clientX - dragState.startX, event.clientY - dragState.startY)
  if (dist > 4) dragMoved = true
  
  const width = showDialog.value ? 336 : 180
  const maxX = Math.max(0, window.innerWidth - width)
  const maxY = Math.max(0, window.innerHeight - 150)
  dragState.x = Math.min(maxX, Math.max(0, event.clientX - dragState.offsetX))
  dragState.y = Math.min(maxY, Math.max(0, event.clientY - dragState.offsetY))
}

function endDrag(event) {
  if (!dragState.active) return
  dragState.active = false
  persistDragPosition()
  event.currentTarget?.releasePointerCapture?.(event.pointerId)
}

function withAutoHideStars() {
  showStars.value = true
  setTimeout(() => {
    showStars.value = false
  }, 1800)
}

async function profileFetcher() {
  const profile = authState.profile || null
  const user = authState.user || null
  return {
    nickname: profile?.nickname || user?.display_name,
    display_name: user?.display_name,
    last_story: profile?.extra?.last_story,
  }
}

function onFocusWord(event) {
  controller?.focus_on_word(event.detail?.word)
}

function onFeedback(event) {
  controller?.give_feedback(Boolean(event.detail?.correct), String(event.detail?.word || ''))
}

function onAccompany(event) {
  controller?.accompany_reading(String(event.detail?.content || ''))
}

function localReply(question) {
  if (question.includes('不会') || question.includes('答错')) return '没关系，我们一起再看一遍关键词，你已经在进步了。'
  if (question.includes('怎么学') || question.includes('计划')) return '可以先做 10 分钟认字，再做 10 分钟阅读，最后复盘 5 分钟。'
  if (question.includes('你好')) return '你好呀，我在这里陪你学习。'
  return '这个问题很棒，我们先从题目里的关键信息开始。'
}

async function requestCompanionAnswer(question) {
  try {
    const data = await api.post('/api/v1/public/ai/chat', { question, role: authState.user ? 'parent' : 'child', style_profile: 'child_cute' })
    if (data?.answer) return data.answer
  } catch {}

  try {
    const data = await api.post('/api/public/ai/chat', { question, role: authState.user ? 'parent' : 'child', style_profile: 'child_cute' })
    if (data?.answer) return data.answer
  } catch {}

  if (authState.token && authState.user) {
    try {
      const data = await api.post('/api/v1/ai/chat', { question, role: 'parent', style_profile: 'child_cute' })
      if (data?.answer) return data.answer
    } catch {}
  }

  return localReply(question)
}

async function askQuestion(text = '') {
  const question = String(text || chatInput.value || '').trim()
  if (!question || chatSending.value) return

  if (!showDialog.value) {
    showDialog.value = true
    persistUiState()
  }

  chatHistory.value.push({ id: `${Date.now()}-u`, role: 'user', text: question })
  chatInput.value = ''
  chatSending.value = true

  try {
    controller?.setState?.(XiaoyueTigerStates.INTERACTING)
    const answer = await requestCompanionAnswer(question)
    chatHistory.value.push({ id: `${Date.now()}-a`, role: 'assistant', text: answer })
    subtitle.value = answer
    await controller?.speak?.(answer, 'gentle')
  } finally {
    chatSending.value = false
    controller?.setState?.(XiaoyueTigerStates.IDLE)
  }
}

onMounted(async () => {
  restoreDragPosition()
  restoreUiState()

  controller = new XiaoyueTigerCompanion({
    onStateChange: (next) => { state.value = next },
    onSubtitle: (text) => { subtitle.value = text },
    onViseme: (payload) => {
      viseme.openness = payload?.openness || 0
      viseme.shape = payload?.shape || 'rest'
    },
    onExpression: (payload) => {
      expression.eye = payload?.eye || 'neutral'
      expression.brow = payload?.brow || 'neutral'
      expression.emotion = payload?.emotion || 'gentle'
    },
    onModeChange: (nextMode) => { mode.value = nextMode },
    onBlink: () => {
      blinked.value = true
      clearTimeout(blinkTimer)
      blinkTimer = setTimeout(() => { blinked.value = false }, 150)
    },
    onWordFocus: (word) => { focusedWord.value = word },
    onEffect: (effect) => {
      if (effect === 'stars') withAutoHideStars()
    },
    onGesture: (next) => {
      gesture.value = next
      clearTimeout(gestureTimer)
      gestureTimer = setTimeout(() => { gesture.value = 'idle' }, 1400)
    },
    onStrokeDemo: (word) => {
      subtitle.value = `${word} 的笔顺演示：从上到下、从左到右慢慢写。`
    },
  })

  controller.start()
  const pathname = window.location.pathname || ''
  if (authState.user && pathname.startsWith('/portal/')) {
    await controller.progress_recall(profileFetcher)
  }

  window.addEventListener('xiaoyue:focus-word', onFocusWord)
  window.addEventListener('xiaoyue:feedback', onFeedback)
  window.addEventListener('xiaoyue:accompany-reading', onAccompany)

  window.xiaoyueCompanion = {
    focus_on_word: (word) => controller?.focus_on_word(word),
    give_feedback: (correct, word) => controller?.give_feedback(correct, word),
    accompany_reading: (content) => controller?.accompany_reading(content),
    speak: (content, emotion) => controller?.speak(content, emotion),
    ask: (content) => askQuestion(content),
  }
})

onBeforeUnmount(() => {
  clearTimeout(blinkTimer)
  clearTimeout(gestureTimer)
  window.removeEventListener('xiaoyue:focus-word', onFocusWord)
  window.removeEventListener('xiaoyue:feedback', onFeedback)
  window.removeEventListener('xiaoyue:accompany-reading', onAccompany)
  if (window.xiaoyueCompanion) delete window.xiaoyueCompanion
  controller?.destroy()
})
</script>

<style scoped>
.xiaoyue-wrap {
  position: fixed;
  right: 16px;
  bottom: 14px;
  z-index: 90;
  width: min(336px, calc(100vw - 24px));
  display: flex;
  flex-direction: column-reverse;
  align-items: flex-end;
  gap: 12px;
}

.tiger-container {
  width: 160px;
  height: 160px;
  cursor: pointer;
  border-radius: 20px;
  background: radial-gradient(circle at 12% 12%, rgba(255, 239, 188, 0.72), transparent 44%),
    linear-gradient(140deg, rgba(183, 231, 255, 0.7), rgba(222, 248, 232, 0.7));
  box-shadow: 0 10px 24px rgba(36, 111, 154, 0.18);
  backdrop-filter: blur(8px);
  touch-action: none; /* for pointer events */
}

.xiaoyue-wrap.is-night .tiger-container {
  background: radial-gradient(circle at 12% 12%, rgba(199, 217, 255, 0.68), transparent 44%),
    linear-gradient(140deg, rgba(221, 234, 255, 0.64), rgba(235, 245, 255, 0.66));
}

.tiger-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 34px rgba(36, 111, 154, 0.25);
  transition: all 0.2s ease;
}

.drag-handle {
  user-select: none;
}

.xiaoyue-card {
  width: 100%;
  border-radius: 22px;
  border: 1px solid rgba(112, 177, 214, 0.34);
  box-shadow: 0 14px 34px rgba(36, 111, 154, 0.18);
  backdrop-filter: blur(10px);
  padding: 16px;
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.95), rgba(240, 250, 255, 0.92));
}

.xiaoyue-wrap.is-night .xiaoyue-card {
  background: linear-gradient(170deg, rgba(247, 252, 255, 0.94), rgba(231, 241, 253, 0.9));
}

.xiaoyue-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.head-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.head-actions {
  display: flex;
  gap: 6px;
}

.tiny-btn {
  border: 1px solid rgba(89, 156, 194, 0.3);
  background: rgba(255, 255, 255, 0.88);
  color: #2f607c;
  font-size: 11px;
  border-radius: 999px;
  padding: 2px 8px;
  cursor: pointer;
}

.tag {
  font-size: 11px;
  font-weight: 700;
  color: #3b7292;
  border-radius: 999px;
  border: 1px solid rgba(89, 156, 194, 0.26);
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.8);
}

.subtitle {
  margin: 10px 0 0;
  color: #2f607c;
  font-size: 13px;
  line-height: 1.5;
  min-height: 40px;
}

.hint {
  margin: 5px 0 0;
  font-size: 12px;
  color: #4a7894;
}

.chat-log {
  margin-top: 8px;
  max-height: 160px;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid rgba(99, 157, 191, 0.22);
  background: rgba(255, 255, 255, 0.72);
  padding: 8px;
}

.chat-item {
  display: flex;
  gap: 6px;
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 6px;
}

.chat-item:last-child {
  margin-bottom: 0;
}

.chat-role {
  flex-shrink: 0;
  color: #2f607c;
  font-weight: 700;
}

.chat-text {
  color: #355e79;
}

.chat-item.role-assistant .chat-text {
  color: #2e6e58;
}

.chat-row {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.chat-input {
  border: 1px solid rgba(99, 157, 191, 0.28);
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 12px;
  outline: none;
  background: rgba(255, 255, 255, 0.88);
}

.chat-send {
  border: 1px solid rgba(67, 129, 165, 0.4);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 12px;
  color: #fff;
  background: linear-gradient(140deg, #49a7df, #2a83c5);
  cursor: pointer;
}

.chat-send:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
