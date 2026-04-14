<template>
  <div class="page-shell" :class="{ 'child-theme-shell': normalizedRole === 'child' }">
    <div class="page-inner portal-layout">
      <aside class="portal-sidebar glass">
        <div class="brand" style="align-items: flex-start">
          <div class="brand-mark">读</div>
          <div>
            <h1 style="margin: 0; font-size: 18px">悦读相伴</h1>
            <p class="muted" style="margin: 4px 0 0">{{ roleLabel }}工作台</p>
          </div>
        </div>

        <div class="portal-nav">
          <button
            v-for="item in menu"
            :key="item.key"
            :class="{ active: activeTab === item.key }"
            @click="activeTab = item.key"
          >
            {{ item.label }}
          </button>
        </div>

        <div class="glass" style="border-radius: 14px; padding: 12px">
          <div class="muted" style="font-size: 12px">当前账号</div>
          <strong style="display: block; margin-top: 6px">{{ state.user?.display_name || '未登录' }}</strong>
          <div class="muted" style="margin-top: 4px; font-size: 13px">{{ state.user?.organization || roleLabel }}</div>
        </div>

        <button class="button button-ghost" @click="logoutAndBack">退出登录</button>
      </aside>

      <main class="portal-main" :class="{ 'portal-main-child': normalizedRole === 'child' }">
        <header class="portal-header glass-strong">
          <div>
            <span class="badge">Unified Portal</span>
            <h2>{{ portalTitle }}</h2>
            <p class="muted" style="margin: 4px 0 0">{{ portalSubtitle }}</p>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap">
            <button class="button button-ghost" @click="router.push('/screen')">数据大屏</button>
            <button class="button button-ghost" @click="refreshAll">刷新</button>
            <button v-if="normalizedRole === 'child'" class="button button-primary" @click="checkinNow">今日打卡 +5</button>
            <button v-if="normalizedRole === 'parent'" class="button button-ghost" @click="exportParentLearningReport">导出学习报告</button>
            <button v-if="normalizedRole === 'parent'" class="button button-primary" @click="openRemoteTutor">远程辅导入口</button>
          </div>
        </header>

        <section class="portal-metrics">
          <article v-for="item in metrics" :key="item.label" class="stat-card glass">
            <div class="label">{{ item.label }}</div>
            <div class="value">{{ item.value }}</div>
            <div class="muted" style="font-size: 12px; margin-top: 6px">{{ item.note }}</div>
          </article>
        </section>

        <section v-if="normalizedRole === 'child'" class="quiz-layout">
          <article class="quiz-card glass-strong">
            <h3>儿童答题任务</h3>
            <p class="muted" style="margin: 6px 0 0">聚焦学习闭环，隐藏无关入口，确保每一步可解释、可控。</p>

            <div class="level-list">
              <button
                v-for="level in levels"
                :key="level.code"
                class="level-btn"
                :class="{ active: selectedLevel?.code === level.code }"
                @click="chooseLevel(level)"
              >
                <strong>{{ level.name }}</strong>
                <div class="muted" style="font-size: 12px">{{ level.category }} · {{ level.difficulty }}</div>
              </button>
            </div>

            <div class="guard-note">
              功能屏蔽规则：
              <br />1. 未选关卡无法开始。
              <br />2. 未开会话无法提交答案。
              <br />3. 会话未结束无法领奖。
              <br />4. 角色越权请求由后端直接拒绝。
            </div>

            <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap">
              <button class="button button-primary" :disabled="!canStart" @click="startQuiz">开始答题</button>
              <button class="button button-ghost" :disabled="!sessionId" @click="endQuiz">结束并提交</button>
              <button class="button button-ghost" :disabled="!canUnlockReward" @click="unlockReward">解锁奖励</button>
            </div>
          </article>

          <article class="quiz-question glass-strong">
            <div style="display: flex; justify-content: space-between; gap: 10px; align-items: center">
              <h3>当前题目</h3>
              <span class="badge">{{ questionIndex + 1 }} / {{ questions.length || 1 }}</span>
            </div>

            <template v-if="sessionId && currentQuestion">
              <p style="line-height: 1.8; margin-top: 10px">{{ currentQuestion.prompt }}</p>
              <div style="margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap">
                <button
                  v-for="word in questionWordCandidates"
                  :key="word"
                  class="button button-ghost"
                  style="min-height: 30px; padding: 0 10px; font-size: 12px"
                  @click="focusWord(word)"
                >
                  认字：{{ word }}
                </button>
              </div>
              <p class="muted" style="margin: 6px 0 0; font-size: 12px">
                能力点：{{ currentQuestion.skill || '综合能力' }} · 难度：{{ currentQuestion.difficulty || 'easy' }}
              </p>

              <div class="answer-list">
                <button
                  v-for="option in currentQuestion.options"
                  :key="option"
                  class="answer-btn"
                  :class="answerClass(option)"
                  :disabled="lockedCurrent"
                  @click="submitAnswer(option)"
                >
                  {{ option }}
                </button>
              </div>

              <p class="muted" style="margin: 10px 0 0">{{ answerFeedback }}</p>
              <p v-if="motivationTip" class="motivation-tip">{{ motivationTip }}</p>
              <p class="muted" style="margin: 6px 0 0; font-size: 12px" v-if="currentQuestion.source_basis">
                设计依据：{{ Object.values(currentQuestion.source_basis).join(' / ') }}
              </p>
              <p class="muted" style="margin: 3px 0 0; font-size: 12px" v-if="currentQuestion.hint">
                提示：{{ currentQuestion.hint }}
              </p>
              <div class="quiz-progress"><span :style="progressStyle"></span></div>
            </template>

            <template v-else>
              <p class="muted" style="line-height: 1.8; margin-top: 10px">请选择关卡后点击“开始答题”。</p>
            </template>
          </article>
        </section>

        <section v-if="normalizedRole === 'child'" class="panel glass-strong">
          <h3>错题本</h3>
          <div class="panel-list">
            <div v-if="!learningExtras.mistakes.length" class="panel-item">
              <div class="muted">目前还没有错题，继续保持！</div>
            </div>
            <div v-for="item in learningExtras.mistakes" :key="item.id" class="panel-item">
              <strong>{{ item.prompt }}</strong>
              <div class="muted" style="margin-top: 6px; font-size: 13px">你的答案：{{ item.selected }} · 正确答案：{{ item.answer }}</div>
              <div class="muted" style="margin-top: 4px; font-size: 12px">{{ item.skill || '综合能力' }} · {{ item.created_at?.slice(0, 19)?.replace('T', ' ') }}</div>
              <div style="margin-top: 8px">
                <button class="button button-ghost" @click="removeMistake(item.id)">移除</button>
              </div>
            </div>
          </div>
        </section>

        <section v-else class="portal-content-grid">
          <article class="panel glass-strong">
            <h3>{{ activeTabLabel }}</h3>
            <div class="panel-list">
              <div v-for="item in primaryList" :key="item.id || item.title || item.name" class="panel-item">
                <strong>{{ item.title || item.name || item.action || item.key || '记录' }}</strong>
                <div class="muted" style="margin-top: 4px; font-size: 13px">{{ item.summary || item.status || item.detail || item.category || item.value || '-' }}</div>
              </div>
            </div>
          </article>

          <article class="panel glass">
            <h3>最近动态</h3>
            <div class="panel-list">
              <div v-for="item in recentList" :key="item.title + item.time" class="panel-item">
                <strong>{{ item.title }}</strong>
                <div class="muted" style="margin-top: 4px; font-size: 13px">{{ item.content }}</div>
                <div class="muted" style="margin-top: 4px; font-size: 12px">{{ item.time || '-' }}</div>
              </div>
            </div>
          </article>
        </section>

        <section v-if="normalizedRole === 'parent'" class="panel glass-strong">
          <h3>儿童答题进度与 AI 分析</h3>
          <div class="panel-list">
            <div v-for="item in parentProgress" :key="item.child?.id" class="panel-item">
              <div style="display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap">
                <strong>{{ item.child?.name || '未命名儿童' }}</strong>
                <span class="badge">
                  完成率 {{ item.progress?.completion_rate || 0 }}% · 正确率 {{ item.progress?.accuracy || 0 }}%
                </span>
              </div>
              <div class="muted" style="margin-top: 6px; font-size: 13px">
                会话 {{ item.progress?.completed_sessions || 0 }}/{{ item.progress?.total_sessions || 0 }}
                · 平均分 {{ item.progress?.average_score || 0 }}
                · 连续学习 {{ item.progress?.streak_days || 0 }} 天
                · 最近关卡 {{ item.progress?.latest_level || '暂无' }}
              </div>
              <div class="muted" style="margin-top: 6px; font-size: 13px" v-if="item.progress?.weak_skills?.length">
                薄弱能力：{{ item.progress.weak_skills.map((w) => w.name).join('、') }}
              </div>
              <div class="muted" style="margin-top: 8px; line-height: 1.7">AI 分析：{{ item.ai_analysis || '暂无分析' }}</div>
              <div class="muted" style="margin-top: 6px; line-height: 1.7">AI 周报：{{ item.ai_weekly_summary || '暂无周报' }}</div>
            </div>
          </div>
        </section>

        <section v-if="normalizedRole === 'parent'" class="panel glass">
          <h3>家长可执行建议</h3>
          <div class="panel-list">
            <div v-for="tip in parentActionTips" :key="tip.title" class="panel-item">
              <strong>{{ tip.title }}</strong>
              <div class="muted" style="margin-top: 4px; font-size: 13px">{{ tip.content }}</div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import gsap from 'gsap'

import { api, buildApiUrl } from '../services/api'
import { logout, state } from '../store/auth'
import {
  addMistake,
  addPoints,
  checkinToday,
  clearMistake,
  exportLearningReport,
  getLearningExtras,
} from '../utils/learningExtras'

const route = useRoute()
const router = useRouter()

const roleAlias = {
  review_group: 'management',
  review_office: 'management',
  academic_affairs: 'management',
}

const roleNameMap = {
  child: '儿童端',
  parent: '家长端',
  counselor: '咨询师端',
  management: '管理端',
}

const normalizedRole = computed(() => roleAlias[route.params.role] || route.params.role || 'child')
const roleLabel = computed(() => roleNameMap[normalizedRole.value] || '管理端')

const menuByRole = {
  child: [
    { key: 'quiz', label: '答题任务' },
    { key: 'reports', label: '成长报告' },
    { key: 'rewards', label: '奖励进度' },
  ],
  parent: [
    { key: 'overview', label: '总览' },
    { key: 'children', label: '儿童档案' },
    { key: 'reports', label: '筛查报告' },
    { key: 'appointments', label: '咨询预约' },
  ],
  counselor: [
    { key: 'overview', label: '总览' },
    { key: 'orders', label: '咨询订单' },
    { key: 'plans', label: '干预计划' },
    { key: 'knowledge', label: '知识支持' },
  ],
  management: [
    { key: 'overview', label: '总览' },
    { key: 'users', label: '用户管理' },
    { key: 'content', label: '内容管理' },
    { key: 'logs', label: '审计日志' },
  ],
}

const activeTab = ref('overview')
const overview = ref({})

const levels = ref([])
const childProfile = ref(null)
const childReports = ref([])
const rewardStatus = ref({})
const parentProgress = ref([])

const selectedLevel = ref(null)
const questions = ref([])
const questionApiAvailable = ref(true)
const questionApiMode = ref('child')
const questionApiProbeDone = ref(false)
const questionIndex = ref(0)
const selectedAnswer = ref('')
const answerFeedback = ref('')
const score = ref(0)
const totalAnswered = ref(0)
const lockedCurrent = ref(false)
const sessionId = ref('')
const sessionStartedAt = ref(0)
const motivationTip = ref('')
const quizCompleted = ref(false)
const comboStreak = ref(0)

const learningExtras = reactive({
  points: 0,
  streakDays: 0,
  checkins: [],
  mistakes: [],
})

const praisePool = [
  '太棒啦！你真聪明～继续保持。',
  '回答正确，今天状态超棒！',
  '你做得很好，继续向前冲。',
]

const encouragePool = [
  '没关系，再试一次，你一定可以的！',
  '你已经很努力了，我们再来一题。',
  '先别着急，跟着提示一步一步来。',
]

const portalTitle = computed(() => {
  if (normalizedRole.value === 'child') return '儿童安全答题中心'
  if (normalizedRole.value === 'parent') return '家校协同中心'
  if (normalizedRole.value === 'counselor') return '咨询协作中心'
  return '运营管理中心'
})

const portalSubtitle = computed(() => {
  if (normalizedRole.value === 'child') return '严谨受控答题流程，清晰反馈，零违规入口'
  if (normalizedRole.value === 'parent') return '进度、报告、问卷、预约与 AI 建议统一视图'
  if (normalizedRole.value === 'counselor') return '订单、干预与知识支持一体化协作'
  return '指标治理、内容管理与审计追踪统一管理'
})

const menu = computed(() => menuByRole[normalizedRole.value] || menuByRole.management)
const activeTabLabel = computed(() => menu.value.find((item) => item.key === activeTab.value)?.label || '总览')

const metrics = computed(() => {
  if (normalizedRole.value === 'child') {
    return [
      { label: '已答题数', value: totalAnswered.value, note: '当前会话累计' },
      { label: '实时得分', value: score.value, note: '答对 +10 / 答错 0' },
      { label: '学习积分', value: learningExtras.points, note: '答题、打卡与完成任务累计' },
      { label: '连续打卡', value: `${learningExtras.streakDays} 天`, note: '保持节奏更容易进步' },
    ]
  }
  if (normalizedRole.value === 'parent') {
    const completionRateAvg = parentProgress.value.length
      ? Number((parentProgress.value.reduce((acc, item) => acc + Number(item.progress?.completion_rate || 0), 0) / parentProgress.value.length).toFixed(1))
      : 0
    return [
      { label: '关联儿童', value: (overview.value.children?.children || []).length, note: '家庭档案' },
      { label: '报告数量', value: (overview.value.reports?.reports || []).length, note: '筛查结果' },
      { label: '预约订单', value: (overview.value.appointments?.orders || []).length, note: '咨询进度' },
      { label: '平均完成率', value: `${completionRateAvg}%`, note: '儿童答题进度' },
    ]
  }
  if (normalizedRole.value === 'counselor') {
    return [
      { label: '咨询订单', value: (overview.value.orders?.orders || []).length, note: '待处理 + 已处理' },
      { label: '干预方案', value: (overview.value.plans?.plans || []).length, note: '草稿 + 执行' },
      { label: '知识条目', value: (overview.value.knowledge?.articles || []).length, note: '可复用模板' },
      { label: '协同提醒', value: (overview.value.summary?.recent_alerts || []).length, note: '最近告警' },
    ]
  }
  return [
    { label: '用户总数', value: overview.value.dashboard?.summary?.users || 0, note: '平台账户' },
    { label: '内容总数', value: (overview.value.articles?.articles || []).length, note: '知识内容' },
    { label: '审计日志', value: (overview.value.logs?.logs || []).length, note: '系统行为记录' },
    { label: '异常告警', value: (overview.value.dashboard?.alerts || []).length, note: '待关注事项' },
  ]
})

const primaryList = computed(() => {
  const tab = activeTab.value
  if (normalizedRole.value === 'parent') {
    if (tab === 'children') {
      if (parentProgress.value.length) {
        return parentProgress.value.map((item) => ({
          ...item,
          title: item.child?.name || '未命名儿童',
          summary: `完成率 ${item.progress?.completion_rate || 0}% · 正确率 ${item.progress?.accuracy || 0}% · 连续 ${item.progress?.streak_days || 0} 天`,
        }))
      }
      return (overview.value.children?.children || []).map((item) => ({ ...item, title: item.name, summary: `${item.school || '-'} · ${item.risk_level || '-'}` }))
    }
    if (tab === 'reports') return (overview.value.reports?.reports || []).map((item) => ({ ...item, title: item.conclusion || item.risk_text, summary: `得分 ${item.score || 0}` }))
    if (tab === 'appointments') return (overview.value.appointments?.orders || []).map((item) => ({ ...item, title: item.title, summary: item.status }))
    return overview.value.knowledge?.articles || []
  }

  if (normalizedRole.value === 'counselor') {
    if (tab === 'orders') return (overview.value.orders?.orders || []).map((item) => ({ ...item, title: item.title, summary: item.status }))
    if (tab === 'plans') return (overview.value.plans?.plans || []).map((item) => ({ ...item, title: item.title, summary: item.status }))
    if (tab === 'knowledge') return (overview.value.knowledge?.articles || []).map((item) => ({ ...item, title: item.title, summary: item.category }))
    return overview.value.summary?.recent_alerts || []
  }

  if (normalizedRole.value === 'management') {
    if (tab === 'users') return (overview.value.users?.users || []).map((item) => ({ ...item, title: item.display_name, summary: `${item.role} · ${item.status}` }))
    if (tab === 'content') return (overview.value.articles?.articles || []).map((item) => ({ ...item, title: item.title, summary: item.category }))
    if (tab === 'logs') return (overview.value.logs?.logs || []).map((item) => ({ ...item, title: item.action, summary: item.detail }))
    return overview.value.dashboard?.alerts || []
  }

  return childReports.value.map((item) => ({ ...item, title: item.conclusion || item.risk_text, summary: `得分 ${item.score || 0}` }))
})

const recentList = computed(() => {
  if (normalizedRole.value === 'child') {
    return [
      { title: '当前关卡', content: selectedLevel.value?.name || '未选择', time: sessionId.value ? '进行中' : '待开始' },
      { title: '答题反馈', content: answerFeedback.value || '暂无', time: `题号 ${questionIndex.value + 1}` },
      { title: '积分状态', content: `${learningExtras.points} 分`, time: `连签 ${learningExtras.streakDays} 天` },
    ]
  }

  if (normalizedRole.value === 'parent') {
    return (overview.value.reports?.reports || []).slice(0, 5).map((item) => ({
      title: item.risk_text || '报告',
      content: item.conclusion || '-',
      time: item.created_at,
    }))
  }

  if (normalizedRole.value === 'counselor') {
    return (overview.value.orders?.orders || []).slice(0, 5).map((item) => ({
      title: item.title,
      content: item.summary || item.status,
      time: item.created_at,
    }))
  }

  return (overview.value.logs?.logs || []).slice(0, 5).map((item) => ({
    title: item.action,
    content: item.detail || '-',
    time: item.created_at,
  }))
})

const currentQuestion = computed(() => questions.value[questionIndex.value] || null)
const canStart = computed(() => normalizedRole.value === 'child' && !sessionId.value)
const canUnlockReward = computed(() => normalizedRole.value === 'child' && !sessionId.value && quizCompleted.value && totalAnswered.value > 0)
const progressStyle = computed(() => ({ width: `${questions.value.length ? ((questionIndex.value + 1) / questions.value.length) * 100 : 0}%` }))
const questionWordCandidates = computed(() => {
  const prompt = String(currentQuestion.value?.prompt || '')
  return Array.from(new Set((prompt.match(/[\u4e00-\u9fa5]{1,2}/g) || []).slice(0, 4)))
})

const parentActionTips = computed(() => {
  if (!parentProgress.value.length) {
    return [
      { title: '建立固定学习节奏', content: '建议每天固定 20 分钟，采用“听音-识字-复盘”三步练习。' },
      { title: '保持正向反馈', content: '答对及时赞美，答错先鼓励再提示，避免批评式交流。' },
    ]
  }

  const child = parentProgress.value[0]
  const accuracy = Number(child.progress?.accuracy || 0)
  const completion = Number(child.progress?.completion_rate || 0)
  const streakDays = Number(child.progress?.streak_days || 0)

  const tips = [
    { title: '每周固定复盘', content: '和孩子一起回顾本周高频错题，按 2 类问题重点练习。' },
    { title: '奖励可视化', content: '用徽章或贴纸记录连续学习天数，增强持续动力。' },
  ]
  if (accuracy < 65) tips.unshift({ title: '先降难再提速', content: '近期正确率偏低，建议先做基础题巩固，再逐步提升难度。' })
  if (completion < 55) tips.unshift({ title: '缩短单次时长', content: '把一次学习拆成 10-15 分钟，减少疲劳提升完成率。' })
  if (streakDays < 3) tips.unshift({ title: '建立连续打卡', content: '先从连续 3 天小目标开始，形成稳定学习习惯。' })
  return tips
})

watch(
  normalizedRole,
  async () => {
    activeTab.value = normalizedRole.value === 'child' ? 'quiz' : 'overview'
    await refreshAll()
  },
  { immediate: true },
)

function syncLearningExtras() {
  Object.assign(learningExtras, getLearningExtras(childProfile.value?.id))
}

async function chooseLevel(level) {
  if (sessionId.value) return
  selectedLevel.value = level
  if (!questionApiAvailable.value || questionApiMode.value === 'local') {
    questions.value = ensureQuestions(level, buildLocalFallbackQuestions(level.code, level.name))
  } else {
    const attempts =
      questionApiMode.value === 'games'
        ? [
            { mode: 'games', base: '/api/v1/games/questions' },
            { mode: 'games', base: '/api/games/questions' },
          ]
        : [
            { mode: 'child', base: '/api/v1/child/questions' },
            { mode: 'games', base: '/api/v1/games/questions' },
            { mode: 'child', base: '/api/child/questions' },
            { mode: 'games', base: '/api/games/questions' },
          ]

    let loaded = false
    for (const attempt of attempts) {
      try {
        const data = await api.get(`${attempt.base}/${level.code}?count=8`)
        questions.value = ensureQuestions(level, data.questions || [])
        questionApiMode.value = attempt.mode
        loaded = true
        break
      } catch (error) {
        if (error?.status && error.status !== 404) {
          break
        }
      }
    }

    if (!loaded) {
      questionApiAvailable.value = false
      questionApiMode.value = 'local'
      questions.value = ensureQuestions(level, buildLocalFallbackQuestions(level.code, level.name))
    }
  }
  if (!questions.value.length) {
    questions.value = ensureQuestions(level, [])
  }
  questionIndex.value = 0
  score.value = 0
  totalAnswered.value = 0
  comboStreak.value = 0
  selectedAnswer.value = ''
  answerFeedback.value = '已选择关卡，请点击开始答题。'
  motivationTip.value = ''
  quizCompleted.value = false
  dispatchCompanionRead(questions.value[0]?.prompt || '')
}

async function probeQuestionApiSupport() {
  if (questionApiProbeDone.value) return
  questionApiProbeDone.value = true
  try {
    const response = await fetch(buildApiUrl('/openapi.json'))
    if (!response.ok) return
    const schema = await response.json()
    const paths = schema?.paths ? Object.keys(schema.paths) : []
    const supportsAny =
      paths.includes('/api/v1/child/questions/{level_code}') ||
      paths.includes('/api/v1/games/questions/{level_code}') ||
      paths.includes('/api/child/questions/{level_code}') ||
      paths.includes('/api/games/questions/{level_code}')
    if (!supportsAny) {
      questionApiAvailable.value = false
      questionApiMode.value = 'local'
    }
  } catch {
    // keep current mode and fallback dynamically
  }
}

function answerClass(option) {
  if (!lockedCurrent.value) return { selected: selectedAnswer.value === option }
  if (!currentQuestion.value) return {}
  return {
    correct: option === currentQuestion.value.answer,
    wrong: option === selectedAnswer.value && option !== currentQuestion.value.answer,
  }
}

async function startQuiz() {
  if (!canStart.value) return
  if (!selectedLevel.value) {
    if (!levels.value.length) {
      levels.value = buildLocalFallbackLevels()
    }
    if (levels.value.length) {
      await chooseLevel(levels.value[0])
    }
  }
  if (!selectedLevel.value) {
    answerFeedback.value = '当前无法加载关卡，已切换到本地练习，请稍后重试。'
    return
  }
  if (!questions.value.length && selectedLevel.value) {
    await chooseLevel(selectedLevel.value)
  }
  if (!questions.value.length && selectedLevel.value) {
    questions.value = ensureQuestions(selectedLevel.value, [])
  }
  try {
    const data = await api.post('/api/v1/child/session/start', {
      child_id: childProfile.value?.id || null,
      level_code: selectedLevel.value.code,
      device: 'web',
    })
    sessionId.value = data.session?.id || ''
    sessionStartedAt.value = Date.now()
    answerFeedback.value = '会话已启动，开始答题。'
    lockedCurrent.value = false
    quizCompleted.value = false
    if (!currentQuestion.value && selectedLevel.value) {
      questions.value = ensureQuestions(selectedLevel.value, [])
      questionIndex.value = 0
    }
  } catch (error) {
    answerFeedback.value = error.message || '无法开始答题会话'
  }
}

async function submitAnswer(option) {
  if (!sessionId.value || !currentQuestion.value || lockedCurrent.value) return
  selectedAnswer.value = option
  lockedCurrent.value = true
  totalAnswered.value += 1

  const correct = option === currentQuestion.value.answer
  if (correct) {
    score.value += 10
    comboStreak.value += 1
    Object.assign(learningExtras, addPoints(childProfile.value?.id, 2))
    answerFeedback.value = '回答正确，继续下一题。'
    motivationTip.value = praisePool[Math.floor(Math.random() * praisePool.length)]
    dispatchCompanionFeedback(true, extractHintWord(currentQuestion.value?.prompt))
  } else {
    comboStreak.value = 0
    Object.assign(
      learningExtras,
      addMistake(childProfile.value?.id, {
        prompt: currentQuestion.value.prompt,
        selected: option,
        answer: currentQuestion.value.answer,
        skill: currentQuestion.value.skill,
      }),
    )
    const explain = currentQuestion.value.explanation ? ` ${currentQuestion.value.explanation}` : ''
    answerFeedback.value = `这次没有答对，正确答案是：${currentQuestion.value.answer}。${explain}`
    motivationTip.value = encouragePool[Math.floor(Math.random() * encouragePool.length)]
    dispatchCompanionFeedback(false, extractHintWord(currentQuestion.value?.prompt))
  }

  try {
    await api.post('/api/v1/child/telemetry', {
      session_id: sessionId.value,
      child_id: childProfile.value?.id || '',
      event_type: 'quiz_answer',
      payload: {
        question_id: currentQuestion.value.id,
        selected: option,
        correct,
        weak_skills: correct ? [] : [currentQuestion.value.skill || selectedLevel.value.code],
      },
      score_delta: correct ? 10 : 0,
      duration_seconds: Math.max(1, Math.floor((Date.now() - sessionStartedAt.value) / 1000)),
    })
  } catch {
    // telemetry should not block flow
  }

  setTimeout(() => {
    if (questionIndex.value < questions.value.length - 1) {
      questionIndex.value += 1
      selectedAnswer.value = ''
      lockedCurrent.value = false
      answerFeedback.value = '请继续作答。'
      dispatchCompanionRead(questions.value[questionIndex.value]?.prompt || '')
    } else {
      answerFeedback.value = '本轮题目已完成，请点击“结束并提交”。'
      quizCompleted.value = true
    }
  }, 450)
}

async function endQuiz() {
  if (!sessionId.value) return
  const duration = Math.max(1, Math.floor((Date.now() - sessionStartedAt.value) / 1000))
  try {
    await api.put('/api/v1/child/session/end', {
      session_id: sessionId.value,
      score: score.value,
      duration_seconds: duration,
      status: 'completed',
      telemetry_summary: {
        answers: totalAnswered.value,
        accuracy: totalAnswered.value ? Number((score.value / (totalAnswered.value * 10)).toFixed(2)) : 0,
        weak_skills: [selectedLevel.value?.code].filter(Boolean),
      },
    })
    Object.assign(learningExtras, addPoints(childProfile.value?.id, 10))
    sessionId.value = ''
    lockedCurrent.value = false
    quizCompleted.value = true
    answerFeedback.value = `已提交，得分 ${score.value} 分。现在可以解锁奖励。`
    motivationTip.value = score.value >= 60 ? '你完成得很棒，继续保持。' : '你坚持完成了全部题目，这就是进步。'
    await fetchRewardStatus()
  } catch (error) {
    answerFeedback.value = error.message || '提交失败'
  }
}

async function unlockReward() {
  if (!canUnlockReward.value) return
  try {
    await api.post('/api/v1/child/rewards/unlock')
    Object.assign(learningExtras, addPoints(childProfile.value?.id, 6))
    answerFeedback.value = '奖励解锁成功。'
    await fetchRewardStatus()
  } catch (error) {
    answerFeedback.value = error.message || '奖励解锁失败'
  }
}

function checkinNow() {
  if (!childProfile.value?.id) return
  const { checked, extras } = checkinToday(childProfile.value.id)
  Object.assign(learningExtras, extras)
  answerFeedback.value = checked ? '今日打卡成功，积分 +5。' : '今天已经打卡过啦，明天再来。'
}

function removeMistake(id) {
  Object.assign(learningExtras, clearMistake(childProfile.value?.id, id))
}

function focusWord(word) {
  if (!word) return
  window.dispatchEvent(new CustomEvent('xiaoyue:focus-word', { detail: { word } }))
}

function dispatchCompanionFeedback(correct, word) {
  window.dispatchEvent(new CustomEvent('xiaoyue:feedback', { detail: { correct, word } }))
}

function dispatchCompanionRead(content) {
  if (!content) return
  window.dispatchEvent(new CustomEvent('xiaoyue:accompany-reading', { detail: { content } }))
}

function extractHintWord(prompt) {
  const matched = String(prompt || '').match(/[\u4e00-\u9fa5]{1,2}/g)
  return matched?.[0] || '这个字'
}

function buildLocalFallbackQuestions(levelCode, levelName) {
  const code = levelCode || 'fallback'
  const common = {
    source_basis: {
      curriculum: 'local_fallback',
      note: '题库接口不可用时的本地保护题',
    },
    difficulty: 'easy',
    hint: '先圈出关键信息，再排除明显不对的选项。',
  }
  return [
    {
      id: `${code}-local-1`,
      prompt: `${levelName || '阅读'}练习：小朋友在教室里认真地____。`,
      options: ['奔跑', '学习', '潜水', '飞翔'],
      answer: '学习',
      skill: '语境理解',
      explanation: '在教室里最常见的行为是学习。',
      ...common,
    },
    {
      id: `${code}-local-2`,
      prompt: '“门/们/问”中，和“门”读音最接近的是？',
      options: ['们', '问', '都不是', '都一样'],
      answer: '们',
      skill: '音韵辨识',
      explanation: '“门”和“们”发音接近。',
      ...common,
    },
    {
      id: `${code}-local-3`,
      prompt: '阅读句子：小红先洗手，再吃水果。小红先做什么？',
      options: ['吃水果', '洗手', '看书', '跳绳'],
      answer: '洗手',
      skill: '顺序理解',
      explanation: '句子明确写了“先洗手”。',
      ...common,
    },
    {
      id: `${code}-local-4`,
      prompt: '哪一个词语和“开心”意思最接近？',
      options: ['难过', '高兴', '困倦', '安静'],
      answer: '高兴',
      skill: '词义理解',
      explanation: '“开心”和“高兴”语义接近。',
      ...common,
    },
  ]
}

function buildLocalFallbackLevels() {
  return [
    {
      code: 'rhyme_match',
      name: '韵脚配对（本地）',
      category: '语音基础',
      difficulty: 'easy',
    },
    {
      code: 'sentence_complete',
      name: '句子补全（本地）',
      category: '阅读理解',
      difficulty: 'easy',
    },
  ]
}

function ensureQuestions(level, items) {
  if (Array.isArray(items) && items.length) return items
  return buildLocalFallbackQuestions(level?.code, level?.name)
}

function exportParentLearningReport() {
  const payload = {
    exported_at: new Date().toISOString(),
    role: 'parent',
    parent: state.user,
    children_progress: parentProgress.value,
    reports: overview.value.reports?.reports || [],
    appointments: overview.value.appointments?.orders || [],
  }
  exportLearningReport(payload, `yuedu-parent-report-${Date.now()}.json`)
}

async function openRemoteTutor() {
  try {
    const firstChildId = overview.value.children?.children?.[0]?.id || null
    await api.post('/api/v1/parent/appointments', {
      child_id: firstChildId,
      title: '家长远程辅导支持',
      summary: '希望安排线上远程辅导，针对近期薄弱能力进行一对一建议。',
      channel: 'online',
    })
    await refreshAll()
  } catch (error) {
    console.error(error)
  }
}

async function fetchRewardStatus() {
  try {
    rewardStatus.value = await api.get('/api/v1/child/rewards/status')
  } catch {
    rewardStatus.value = {}
  }
}

async function refreshAll() {
  if (normalizedRole.value === 'child') {
    parentProgress.value = []
    const [dashboardResult, levelResult, rewardResult, reportResult] = await Promise.allSettled([
      api.get('/api/v1/child/dashboard'),
      api.get('/api/v1/child/levels'),
      api.get('/api/v1/child/rewards/status'),
      api.get('/api/v1/child/reports'),
    ])
    overview.value = dashboardResult.status === 'fulfilled' ? dashboardResult.value || {} : {}
    const levelData = levelResult.status === 'fulfilled' ? levelResult.value || {} : {}
    const reportData = reportResult.status === 'fulfilled' ? reportResult.value || {} : {}
    levels.value = (levelData.levels || []).length ? levelData.levels : buildLocalFallbackLevels()
    childProfile.value = levelData.child || reportData.child || childProfile.value || null
    rewardStatus.value = rewardResult.status === 'fulfilled' ? rewardResult.value || {} : {}
    childReports.value = reportData.reports || []
    syncLearningExtras()
    await probeQuestionApiSupport()
    if (!selectedLevel.value && levels.value.length) await chooseLevel(levels.value[0])
    runEntryAnimations()
    return
  }

  if (normalizedRole.value === 'parent') {
    try {
      const [children, reports, appointments, knowledge, progress] = await Promise.all([
        api.get('/api/v1/parent/children'),
        api.get('/api/v1/parent/reports'),
        api.get('/api/v1/parent/appointments'),
        api.get('/api/v1/parent/knowledge'),
        api.get('/api/v1/parent/children/progress?include_ai=true'),
      ])
      overview.value = { children, reports, appointments, knowledge }
      parentProgress.value = progress.children_progress || []
    } catch {
      overview.value = { children: { children: [] }, reports: { reports: [] }, appointments: { orders: [] }, knowledge: { articles: [] } }
      parentProgress.value = []
    }
    runEntryAnimations()
    return
  }

  if (normalizedRole.value === 'counselor') {
    parentProgress.value = []
    try {
      const [orders, plans, summary, knowledge] = await Promise.all([
        api.get('/api/v1/counselor/orders'),
        api.get('/api/v1/counselor/interventions'),
        api.get('/api/v1/counselor/statistics/summary'),
        api.get('/api/v1/counselor/knowledge'),
      ])
      overview.value = { orders, plans, summary, knowledge }
    } catch {
      overview.value = { orders: { orders: [] }, plans: { plans: [] }, summary: { recent_alerts: [] }, knowledge: { articles: [] } }
    }
    runEntryAnimations()
    return
  }

  try {
    const [dashboard, users, articles, logs] = await Promise.all([
      api.get('/api/v1/admin/dashboard'),
      api.get('/api/v1/admin/users'),
      api.get('/api/v1/admin/articles'),
      api.get('/api/v1/admin/audit-logs'),
    ])
    overview.value = { dashboard, users, articles, logs }
  } catch {
    overview.value = { dashboard: { summary: {}, alerts: [] }, users: { users: [] }, articles: { articles: [] }, logs: { logs: [] } }
  }
  parentProgress.value = []
  runEntryAnimations()
}

function runEntryAnimations() {
  nextTick(() => {
    const statCards = gsap.utils.toArray('.stat-card')
    if (statCards.length) {
      gsap.fromTo(statCards, { y: 18, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, stagger: 0.06, ease: 'power3.out' })
    }

    const contentCards = gsap.utils.toArray('.panel, .quiz-card, .quiz-question')
    if (contentCards.length) {
      gsap.fromTo(contentCards, { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.55, stagger: 0.08, ease: 'power3.out' })
    }
  })
}

async function logoutAndBack() {
  await logout()
  router.push('/')
}
</script>
