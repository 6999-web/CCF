<template>
  <div class="page-shell">
    <div class="page-inner">
      <header class="landing-head glass-strong">
        <div class="brand">
          <div class="brand-mark">悦</div>
          <div>
            <h1 style="margin: 0; font-family: var(--font-display); font-size: 28px">悦读相伴 V3</h1>
            <p class="muted" style="margin: 4px 0 0">阳光清新 · 3D 立体 · 儿童学习优先</p>
          </div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap">
          <button class="button button-ghost" @click="router.push('/screen')">查看全局大屏</button>
        </div>
      </header>

      <section class="landing-scene glass">
        <h2 class="scene-title">让每一次答题都更有鼓励感</h2>

        <button class="scene-card scene-child glass" @click="openByCode('child')">
          <strong>儿童端</strong>
          <span>答题训练 · 鼓励反馈</span>
        </button>

        <button class="scene-card scene-parent glass" @click="openByCode('parent')">
          <strong>家长端</strong>
          <span>进度洞察 · AI 周报</span>
        </button>

        <button class="scene-card scene-counselor glass" @click="openByCode('counselor')">
          <strong>咨询师端</strong>
          <span>咨询订单 · 干预计划</span>
        </button>

        <button class="scene-card scene-management glass" @click="openByCode('management')">
          <strong>管理端</strong>
          <span>内容审核 · 数据分析</span>
        </button>

        <div class="scene-mascot">
          <TigerCharacter style="transform: scale(1.6); transform-origin: bottom center;" />
        </div>

        <div class="scene-chat">
          <input
            v-model="chatInput"
            class="scene-chat-input"
            placeholder="想问小悦什么？"
            @keydown.enter.prevent="askXiaoyue"
          />
          <button class="button button-primary scene-chat-btn" :disabled="chatSending" @click="askXiaoyue">
            {{ chatSending ? '发送中...' : '发送' }}
          </button>
        </div>
        <div v-if="chatReply" class="scene-chat-reply">{{ chatReply }}</div>
      </section>
    </div>

    <LoginDialog
      :visible="loginVisible"
      :card="selectedCard"
      :roles="currentRoles"
      @close="loginVisible = false"
      @success="handleLoginSuccess"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import LoginDialog from '../components/LoginDialog.vue'
import TigerCharacter from '../components/TigerCharacter.vue'
import { api } from '../services/api'
import { state as authState } from '../store/auth'

const router = useRouter()
const cards = ref([])
const selectedCard = ref(null)
const loginVisible = ref(false)
const chatInput = ref('')
const chatReply = ref('')
const chatSending = ref(false)

const fallbackCards = [
  {
    code: 'child',
    title: '儿童端',
    subtitle: '安全答题训练',
    description: '聚焦儿童学习任务，保留清晰的答题闭环与积极反馈。',
    features: ['分级关卡', '鼓励反馈', '奖励成长'],
    entry_roles: ['child'],
    accent: 'blue',
  },
  {
    code: 'parent',
    title: '家长端',
    subtitle: '陪伴与进度洞察',
    description: '查看学习进度、筛查报告、AI 分析与行动建议。',
    features: ['进度中台', 'AI 周报', '咨询预约'],
    entry_roles: ['parent'],
    accent: 'orange',
  },
  {
    code: 'counselor',
    title: '咨询师端',
    subtitle: '专业协作工作台',
    description: '管理咨询订单、干预计划与知识支持，协同家校落地。',
    features: ['订单管理', '干预计划', '知识支持'],
    entry_roles: ['counselor'],
    accent: 'green',
  },
  {
    code: 'management',
    title: '管理端',
    subtitle: '运营治理中心',
    description: '统一管理用户、内容、审计和系统配置。',
    features: ['用户治理', '内容管理', '审计追踪'],
    entry_roles: ['management'],
    accent: 'indigo',
  },
]

const roleLabelMap = {
  child: '儿童端',
  parent: '家长端',
  counselor: '咨询师端',
  management: '管理端',
}

const currentRoles = computed(() => {
  if (!selectedCard.value) return []
  const source = selectedCard.value.code === 'management' ? ['management'] : (selectedCard.value.entry_roles || [])
  return source.map((value) => ({ value, label: roleLabelMap[value] || value }))
})

onMounted(async () => {
  try {
    const data = await api.get('/api/v1/public/entry-points')
    cards.value = data.cards?.length ? data.cards : fallbackCards
  } catch {
    cards.value = fallbackCards
  }
})

function openByCode(code) {
  const card = cards.value.find((item) => item.code === code)
  if (!card) return
  selectedCard.value = card
  loginVisible.value = true
}

function handleLoginSuccess(data) {
  loginVisible.value = false
  router.push(`/portal/${data.portal || data.user.role}`)
}

function localReply(question) {
  if (question.includes('不会') || question.includes('答错')) {
    return '没关系，我们先把题目里的关键词圈出来，再一步一步做。你已经很棒了。'
  }
  if (question.includes('怎么学') || question.includes('计划')) {
    return '建议今天先做 10 分钟认字，再做 10 分钟阅读理解，最后复盘 5 分钟。'
  }
  if (question.includes('你好')) {
    return '你好呀，我是小悦，我们一起轻松学习。'
  }
  return '这个问题很棒。我们先从题干关键信息开始，我会陪你一步步完成。'
}

async function askXiaoyue() {
  const question = String(chatInput.value || '').trim()
  if (!question || chatSending.value) return
  chatSending.value = true
  try {
    let answer = ''
    try {
      const data = await api.post('/api/v1/public/ai/chat', {
        question,
        role: authState.user ? 'parent' : 'child',
        style_profile: 'child_cute',
      })
      answer = data?.answer || ''
    } catch {
      try {
        const data = await api.post('/api/public/ai/chat', {
          question,
          role: authState.user ? 'parent' : 'child',
          style_profile: 'child_cute',
        })
        answer = data?.answer || ''
      } catch {
        answer = ''
      }
      if (!answer && authState.token && authState.user) {
        try {
          const data = await api.post('/api/v1/ai/chat', {
            question,
            role: 'parent',
            style_profile: 'child_cute',
          })
          answer = data?.answer || ''
        } catch {
          answer = ''
        }
      }
    }
    if (!answer) {
      answer = localReply(question)
    }
    chatReply.value = answer
    window.xiaoyueCompanion?.speak?.(answer, 'gentle')
  } finally {
    chatSending.value = false
  }
}
</script>
