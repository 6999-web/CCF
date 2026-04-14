const STATES = {
  IDLE: 'IDLE',
  READING: 'READING',
  INTERACTING: 'INTERACTING',
  ENCOURAGING: 'ENCOURAGING',
  THINKING: 'THINKING',
}

const EMOTION_PRESET = {
  happy: { rate: 1.05, pitch: 1.14 },
  gentle: { rate: 0.92, pitch: 1.06 },
  calm: { rate: 0.96, pitch: 1.0 },
}

function mapEmotion(emotion) {
  const value = String(emotion || '').toLowerCase().trim()
  if (['happy', '开心', '高兴', '鼓励'].includes(value)) return 'happy'
  if (['calm', '平和', '平静', 'neutral'].includes(value)) return 'calm'
  return 'gentle'
}

function calcVisemeByChar(char) {
  const strong = 'aoueivAOUOEI啊哦额阿欧爱安昂'
  const middle = 'mnwbpf吾嗯文吧发'

  if (!char || /\s/.test(char)) {
    return { openness: 0, shape: 'rest', phoneme: 'sil' }
  }
  if (strong.includes(char)) {
    return { openness: 0.84, shape: 'round', phoneme: 'vowel' }
  }
  if (middle.includes(char)) {
    return { openness: 0.56, shape: 'narrow', phoneme: 'mid' }
  }
  return { openness: 0.36, shape: 'smile', phoneme: 'cons' }
}

function createBrowserTtsAdapter() {
  return {
    canSpeak() {
      return typeof window !== 'undefined' && 'speechSynthesis' in window
    },
    speak({ text, emotion, onStart, onEnd, onError }) {
      if (!this.canSpeak()) {
        onError?.(new Error('speechSynthesis unavailable'))
        return
      }

      const cfg = EMOTION_PRESET[emotion] || EMOTION_PRESET.gentle
      const utter = new SpeechSynthesisUtterance(text)
      utter.lang = 'zh-CN'
      utter.rate = cfg.rate
      utter.pitch = cfg.pitch
      utter.onstart = () => onStart?.()
      utter.onend = () => onEnd?.()
      utter.onerror = (e) => onError?.(e)

      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(utter)
    },
    stop() {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    },
  }
}

export class XiaoyueTigerCompanion {
  constructor(options = {}) {
    this.options = options
    this.state = STATES.IDLE
    this.lastPrompt = ''
    this.studyStartAt = Date.now()
    this.eyeCareDurationMs = 20 * 60 * 1000
    this.mode = this._resolveDayNightMode()

    this._timers = {
      speak: null,
      eyeCare: null,
      blink: null,
      idle: null,
      mode: null,
      fallbackSpeak: null,
    }

    this.ttsAdapter = createBrowserTtsAdapter()
  }

  setTtsAdapter(adapter) {
    if (adapter && typeof adapter.speak === 'function') {
      this.ttsAdapter = adapter
    }
  }

  getStates() {
    return { ...STATES }
  }

  start() {
    this._emitMode()
    this._startIdleLoop()
    this._startBlinkLoop()
    this._startEyeCareLoop()
    this._startModeLoop()
    this.setState(STATES.IDLE)
  }

  destroy() {
    Object.values(this._timers).forEach((id) => clearInterval(id) || clearTimeout(id))
    this.ttsAdapter?.stop?.()
  }

  setState(next) {
    if (!next || this.state === next) return
    this.state = next
    this.options.onStateChange?.(this.state)
  }

  async speak(content, emotion = 'gentle') {
    const text = String(content || '').trim()
    if (!text) return

    const normalizedEmotion = mapEmotion(emotion)
    this.options.onSubtitle?.(text)
    this._applyExpressionByText(text, normalizedEmotion)

    const startViseme = () => this._streamViseme(text)
    const endViseme = () => this._finishViseme()

    if (this.ttsAdapter?.canSpeak?.()) {
      await new Promise((resolve) => {
        this.ttsAdapter.speak({
          text,
          emotion: normalizedEmotion,
          onStart: startViseme,
          onEnd: () => {
            endViseme()
            resolve()
          },
          onError: () => {
            endViseme()
            resolve()
          },
        })
      })
      return
    }

    startViseme()
    const pseudoDuration = Math.max(900, text.length * 160)
    await new Promise((resolve) => {
      this._timers.fallbackSpeak = setTimeout(() => {
        endViseme()
        resolve()
      }, pseudoDuration)
    })
  }

  async focus_on_word(word) {
    const label = String(word || '').trim()
    if (!label) return

    this.lastPrompt = label
    this.setState(STATES.READING)
    this.options.onGesture?.('point-word')
    this.options.onWordFocus?.(label)

    await this.speak(`看这里，这个字是“${label}”。我们一起读：${label}。`, 'gentle')
    this.options.onStrokeDemo?.(label)
    this.setState(STATES.IDLE)
  }

  async give_feedback(correct, word = '') {
    if (correct) {
      this.setState(STATES.ENCOURAGING)
      this.options.onGesture?.('clap-spin')
      this.options.onEffect?.('stars')
      await this.speak('哇！你太厉害了，这个字你都认识！', 'happy')
      this.setState(STATES.IDLE)
      return
    }

    this.setState(STATES.THINKING)
    this.options.onGesture?.('thinking')
    const hintWord = String(word || this.lastPrompt || '这个字')
    await this.speak(`没关系，我们再看看${hintWord}，它长得像不像一个小窗口？`, 'gentle')
    this.setState(STATES.IDLE)
  }

  async accompany_reading(content) {
    const text = String(content || '').trim()
    if (!text) return

    this.setState(STATES.READING)
    await this.speak(`我先读一遍：${text}`, 'calm')
    this.setState(STATES.INTERACTING)
    await this.speak('轮到你啦，我会认真听你读。', 'gentle')
    this.setState(STATES.IDLE)
  }

  async progress_recall(fetcher) {
    try {
      const profile = await fetcher?.()
      const name = profile?.nickname || profile?.display_name || '小朋友'
      const story = profile?.last_story || '《森林历险记》'
      this.setState(STATES.INTERACTING)
      await this.speak(`${name}宝贝，欢迎回来！我们上次读到了${story}，今天要继续吗？`, 'gentle')
      this.setState(STATES.IDLE)
    } catch {
      // ignore network failures
    }
  }

  resetStudyClock() {
    this.studyStartAt = Date.now()
  }

  _streamViseme(text) {
    clearInterval(this._timers.speak)

    const chars = Array.from(text)
    let index = 0
    this._timers.speak = setInterval(() => {
      if (index >= chars.length) {
        this._finishViseme()
        return
      }
      const viseme = calcVisemeByChar(chars[index])
      this.options.onViseme?.(viseme)
      index += 1
    }, 85)
  }

  _finishViseme() {
    clearInterval(this._timers.speak)
    clearTimeout(this._timers.fallbackSpeak)
    this.options.onViseme?.({ openness: 0, shape: 'rest', phoneme: 'sil' })
  }

  _applyExpressionByText(text, emotion) {
    const payload = { emotion, eye: 'neutral', brow: 'neutral' }
    if (text.includes('太厉害') || text.includes('真棒') || text.includes('太棒')) {
      payload.eye = 'smile'
      payload.brow = 'up'
    } else if (text.includes('再试') || text.includes('没关系') || text.includes('看看')) {
      payload.eye = 'soft'
      payload.brow = 'soft'
    }
    this.options.onExpression?.(payload)
  }

  _resolveDayNightMode() {
    const hour = new Date().getHours()
    return hour >= 7 && hour < 19 ? 'day' : 'night'
  }

  _emitMode() {
    this.options.onModeChange?.(this.mode)
  }

  _startModeLoop() {
    clearInterval(this._timers.mode)
    this._timers.mode = setInterval(() => {
      const next = this._resolveDayNightMode()
      if (next === this.mode) return
      this.mode = next
      this._emitMode()
    }, 60 * 1000)
  }

  _startEyeCareLoop() {
    clearInterval(this._timers.eyeCare)
    this._timers.eyeCare = setInterval(async () => {
      if (Date.now() - this.studyStartAt < this.eyeCareDurationMs) return
      this.resetStudyClock()
      this.options.onGesture?.('stretch')
      this.setState(STATES.INTERACTING)
      await this.speak('我们已经学习 20 分钟啦，和小悦一起看看远方，让眼睛休息一下吧。', 'gentle')
      this.setState(STATES.IDLE)
    }, 30 * 1000)
  }

  _startBlinkLoop() {
    clearInterval(this._timers.blink)
    this._timers.blink = setInterval(() => this.options.onBlink?.(), 4200)
  }

  _startIdleLoop() {
    clearInterval(this._timers.idle)
    this._timers.idle = setInterval(() => {
      if (this.state !== STATES.IDLE) return
      this.options.onGesture?.(Math.random() > 0.5 ? 'wave' : 'idle')
    }, 5500)
  }
}

export const XiaoyueTigerStates = STATES
