<template>
  <div class="page-shell v3-landing-shell">
    <div class="page-inner">
      <header class="v3-topbar glass-strong">
        <div class="v3-brand">
          <div class="v3-brand-mark">悦</div>
          <div>
            <h1 class="v3-brand-title">悦读相伴 V3</h1>
            <p class="v3-brand-sub">阳光清新 · 3D 立体 · 儿童学习优先</p>
          </div>
        </div>
        <button class="button v3-screen-btn" @click="router.push('/screen')">查看全局大屏</button>
      </header>

      <section class="v3-stage v3-stage-compact glass">
        <div class="v3-stage-main">
          <span class="v3-kicker">儿童友好学习系统</span>
          <h2 class="v3-hero-title">
            让每一次答题都更有
            <span>鼓励感</span>
          </h2>
          <p class="v3-hero-desc">
            统一覆盖儿童端、家长端、咨询师端与管理端。儿童答对赞美，答错先鼓励再提示，家长可实时查看进度与 AI 分析。
          </p>
        </div>

        <div class="v3-loop-panel">
          <article class="v3-loop-item">
            <h3>学习闭环</h3>
            <p>选关卡 → 开会话 → 答题反馈 → 提交结果</p>
          </article>
          <article class="v3-loop-item">
            <h3>家长洞察</h3>
            <p>完成率、正确率、连续学习天数、薄弱项分析</p>
          </article>
          <article class="v3-loop-item">
            <h3>系统协同</h3>
            <p>儿童端、家长端、咨询师端、管理端统一协作</p>
          </article>
        </div>
      </section>

      <section class="v3-role-grid">
        <button
          v-for="card in roleCards"
          :key="card.code"
          class="v3-role-card glass"
          :class="`v3-role-${card.code}`"
          @click="openByCode(card.code)"
        >
          <span class="v3-role-tag">{{ roleTagMap[card.code] || '统一入口' }}</span>
          <h3>{{ card.title }}</h3>
          <p>{{ card.description }}</p>
        </button>
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
import { api } from '../services/api'

const router = useRouter()
const cards = ref([])
const selectedCard = ref(null)
const loginVisible = ref(false)

const fallbackCards = [
  {
    code: 'child',
    title: '儿童端',
    subtitle: '安全答题训练',
    description: '围绕读写障碍儿童的关卡练习、奖励成长、设备采集与游戏数据回传。',
    features: ['分级关卡', '鼓励反馈', '奖励成长'],
    entry_roles: ['child'],
  },
  {
    code: 'parent',
    title: '家长端',
    subtitle: '陪伴与进度洞察',
    description: '查看筛查报告、填写问卷、与 AI 智能体问答，并发起人工咨询预约。',
    features: ['进度中台', 'AI 周报', '咨询预约'],
    entry_roles: ['parent'],
  },
  {
    code: 'counselor',
    title: '咨询师端',
    subtitle: '专业协作工作台',
    description: '承接咨询订单、编写干预方案、查看儿童画像与知识库素材。',
    features: ['订单管理', '干预计划', '知识支持'],
    entry_roles: ['counselor'],
  },
  {
    code: 'management',
    title: '管理端',
    subtitle: '运营治理中心',
    description: '统一管理用户、内容、审计和系统配置。',
    features: ['用户治理', '内容管理', '审计追踪'],
    entry_roles: ['review_group', 'review_office', 'academic_affairs'],
  },
]

const roleLabelMap = {
  child: '儿童端',
  parent: '家长端',
  counselor: '咨询师端',
  management: '管理端',
  review_group: '评教小组',
  review_office: '评教办',
  academic_affairs: '教务处',
}

const roleTagMap = {
  child: 'CH 趣味训练，轻量上手',
  parent: 'PA 报告、问答、预约',
  counselor: 'CO 接单、排班、干预',
  management: 'MG 审核、配置、治理',
}

const currentRoles = computed(() => {
  if (!selectedCard.value) return []
  if (selectedCard.value.code === 'management') {
    return [{ value: 'management', label: roleLabelMap.management }]
  }
  return (selectedCard.value.entry_roles || []).map((value) => ({ value, label: roleLabelMap[value] || value }))
})

const roleCards = computed(() => {
  const byCode = new Map(cards.value.map((item) => [item.code, item]))
  return ['child', 'parent', 'counselor', 'management'].map((code) => byCode.get(code)).filter(Boolean)
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
</script>
