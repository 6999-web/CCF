import { api } from './src/services/api.js'
import { clearSession, hydrateSession, login, logout, state } from './src/store/auth.js'
import { managementRoles, roleConfig } from './src/config/portal.js'
import { DEFAULT_THEME_KEY_BY_ROLE, getThemeByKey, getThemeOptions } from './src/config/themes.js'

const {
  createApp,
  ref,
  reactive,
  computed,
  watch,
  onMounted,
  onBeforeUnmount,
} = Vue

const { createRouter, createWebHistory, useRouter, useRoute } = VueRouter

const AVATAR_PRESETS = [
  { value: '🦾', label: '机甲' },
  { value: '🌸', label: '花朵' },
  { value: '🚀', label: '火箭' },
  { value: '🧠', label: '智慧' },
  { value: '🎯', label: '目标' },
  { value: '📘', label: '书本' },
  { value: '🦋', label: '蝴蝶' },
  { value: '⭐', label: '星星' },
  { value: '🌊', label: '海浪' },
  { value: '🛡️', label: '盾牌' },
]

function splitList(value) {
  return String(value || '')
    .split(/[\n,，、;；]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function joinList(items) {
  return (items || []).join('，')
}

function getStoredThemeKey(scope) {
  return localStorage.getItem(`xm_theme_${scope}`) || DEFAULT_THEME_KEY_BY_ROLE[scope] || getThemeOptions(scope)[0]?.key
}

function applyTheme(scope, key) {
  const theme = getThemeByKey(scope, key || getStoredThemeKey(scope))
  const root = document.documentElement
  root.dataset.theme = theme.key
  root.style.setProperty('--page-bg', theme.bodyBackground)
  Object.entries(theme.vars || {}).forEach(([name, value]) => {
    root.style.setProperty(name, value)
  })
  localStorage.setItem(`xm_theme_${scope}`, theme.key)
  return theme
}

function avatarDisplay(value, fallback = '星') {
  const raw = String(value || '').trim()
  if (!raw) return fallback
  return raw.slice(0, 2)
}

function formFromProfile(profile, role) {
  const theme = getThemeByKey(role, profile?.theme_key || getStoredThemeKey(role))
  return {
    nickname: profile?.nickname || '',
    avatar: profile?.avatar || '',
    signature: profile?.signature || '',
    bio: profile?.bio || '',
    hobbiesText: joinList(profile?.hobbies || []),
    interestsText: joinList(profile?.interests || []),
    favorite_color: profile?.favorite_color || '',
    favorite_subject: profile?.favorite_subject || '',
    assistant_name: profile?.assistant_name || '',
    theme_key: theme.key,
    extraText: JSON.stringify(profile?.extra || {}, null, 2),
  }
}

function payloadFromForm(form) {
  let extra = {}
  try {
    extra = form.extraText ? JSON.parse(form.extraText) : {}
  } catch {
    extra = {}
  }
  return {
    nickname: form.nickname.trim(),
    avatar: form.avatar.trim(),
    signature: form.signature.trim(),
    bio: form.bio.trim(),
    hobbies: splitList(form.hobbiesText),
    interests: splitList(form.interestsText),
    favorite_color: form.favorite_color.trim(),
    favorite_subject: form.favorite_subject.trim(),
    assistant_name: form.assistant_name.trim(),
    theme_key: form.theme_key,
    extra,
  }
}

function themePreviewStyle(theme) {
  return {
    background: theme.bodyBackground,
  }
}

const fallbackCards = [
  {
    code: 'child',
    title: '儿童端',
    subtitle: '趣味训练，轻量上手',
    description: '围绕读写障碍儿童的关卡练习、奖励成长、设备采集与游戏数据回传。',
    features: ['分级关卡', '游戏记录', '奖励成长'],
    entry_roles: ['child'],
    accent: 'blue',
    route: '/portal/child',
    login_required: true,
  },
  {
    code: 'parent',
    title: '家长端',
    subtitle: '报告、问答、预约',
    description: '查看筛查报告、填写问卷、与 AI 智能体问答，并发起人工咨询预约。',
    features: ['筛查报告', 'AI 问答', '咨询预约'],
    entry_roles: ['parent'],
    accent: 'pink',
    route: '/portal/parent',
    login_required: true,
  },
  {
    code: 'counselor',
    title: '咨询师端',
    subtitle: '接单、排班、干预',
    description: '承接咨询订单、编写干预方案、查看儿童画像与知识库素材。',
    features: ['订单管理', '排班管理', '干预方案'],
    entry_roles: ['counselor'],
    accent: 'green',
    route: '/portal/counselor',
    login_required: true,
  },
  {
    code: 'management',
    title: '管理端',
    subtitle: '审核、配置、统计',
    description: '统一管理用户、内容、规则、咨询师审核和数据看板。',
    features: ['用户管理', '内容审核', '系统配置'],
    entry_roles: ['review_group', 'review_office', 'academic_affairs'],
    accent: 'orange',
    route: '/portal/management',
    login_required: true,
  },
]

function createBaseCardTemplate(card) {
  return `
    <div class="role-card">
      <div class="role-icon" style="background:${{
        blue: 'linear-gradient(135deg, #2f4978 0%, #1e2947 100%)',
        pink: 'linear-gradient(135deg, #4a3457 0%, #2a2342 100%)',
        green: 'linear-gradient(135deg, #2f5b57 0%, #234043 100%)',
        orange: 'linear-gradient(135deg, #7a542b 0%, #4b3521 100%)',
        indigo: 'linear-gradient(135deg, #364171 0%, #242d54 100%)',
      }[card.accent] || 'linear-gradient(135deg, #2f4978 0%, #1e2947 100%)'}">
        ${card.title.slice(0, 1)}
      </div>
      <h3 class="role-name">${card.title}</h3>
      <p class="role-desc">${card.description}</p>
      <div class="role-footer">
        ${card.features.map((tag) => `<span class="mini-tag">${tag}</span>`).join('')}
      </div>
    </div>
  `
}

const RoleCard = {
  props: ['card'],
  emits: ['select'],
  template: `
    <div class="role-card" @click="$emit('select', card)">
      <div class="role-icon" :style="iconStyle">{{ shortLabel }}</div>
      <h3 class="role-name">{{ card.title }}</h3>
      <p class="role-desc">{{ card.description }}</p>
      <div class="role-footer">
        <span v-for="tag in card.features" :key="tag" class="mini-tag">{{ tag }}</span>
      </div>
    </div>
  `,
  setup(props) {
    const shortLabel = computed(() => props.card.title?.slice(0, 1) || '星')
    const iconStyle = computed(() => {
      const palette = {
        blue: 'linear-gradient(135deg, #2f4978 0%, #1e2947 100%)',
        pink: 'linear-gradient(135deg, #4a3457 0%, #2a2342 100%)',
        green: 'linear-gradient(135deg, #2f5b57 0%, #234043 100%)',
        orange: 'linear-gradient(135deg, #7a542b 0%, #4b3521 100%)',
        indigo: 'linear-gradient(135deg, #364171 0%, #242d54 100%)',
      }
      return { background: palette[props.card.accent] || palette.blue }
    })
    return { shortLabel, iconStyle }
  },
}

const StatCard = {
  props: ['label', 'value', 'note'],
  template: `
    <div class="stat-card">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ value }}</div>
      <div class="stat-note">{{ note }}</div>
    </div>
  `,
}

const PanelCard = {
  props: ['title', 'variant'],
  template: `
    <section :class="['panel', variant === 'light' ? 'light' : '']">
      <div v-if="title" class="panel-title">{{ title }}</div>
      <slot></slot>
    </section>
  `,
}

const ShellLayout = {
  props: ['title', 'subtitle', 'menu', 'activeKey', 'user'],
  emits: ['change-tab'],
  template: `
    <div class="layout">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">星</div>
          <div>
            <p class="brand-title">星萌乐学</p>
            <p class="brand-subtitle">统一门户 · 单端口 · 实时联动</p>
          </div>
        </div>
        <div class="badge" style="margin-top: 6px">
          <span>{{ title }}</span>
        </div>
        <div class="nav-group">
          <button
            v-for="item in menu"
            :key="item.key"
            class="nav-item"
            :class="{ active: item.key === activeKey }"
            @click="$emit('change-tab', item.key)"
          >{{ item.label }}</button>
        </div>
        <div class="surface-dark" style="padding: 18px; margin-top: 18px">
          <div class="muted" style="font-size: 13px">当前用户</div>
          <div style="font-size: 20px; font-weight: 900; margin-top: 8px">{{ user?.display_name || '未登录' }}</div>
          <div style="margin-top: 10px; color: var(--muted)">{{ user?.organization || subtitle }}</div>
        </div>
      </aside>
      <main class="workspace">
        <div class="workspace-header">
          <div>
            <h1 class="workspace-title">{{ title }}</h1>
            <p class="workspace-subtitle">{{ subtitle }}</p>
          </div>
          <div class="chip-row">
            <slot name="header-actions"></slot>
          </div>
        </div>
        <slot></slot>
      </main>
    </div>
  `,
}

const LoginDialog = {
  props: ['visible', 'card', 'roles'],
  emits: ['close', 'success'],
  template: `
    <div v-if="visible" class="dialog-mask">
      <div class="dialog-card">
        <div class="dialog-header">
          <h2 class="dialog-title">{{ card?.title || '统一登录' }}</h2>
          <button class="button button-ghost" @click="$emit('close')">关闭</button>
        </div>
        <div class="dialog-body">
          <div>
            <div class="badge" style="margin-bottom: 14px">统一入口 · 单点登录 · 角色切换</div>
            <div class="field">
              <label>用户名</label>
              <input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
            </div>
            <div class="field">
              <label>密码</label>
              <input v-model="form.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
            </div>
            <div class="field">
              <label>备用入口说明</label>
              <textarea rows="3" readonly :value="card?.subtitle || '登录后进入对应工作台'"></textarea>
            </div>
            <div style="display:flex;gap:12px;align-items:center">
              <button class="button button-primary" :disabled="loading" @click="submit">
                {{ loading ? '登录中...' : '进入系统' }}
              </button>
              <button class="button button-ghost" @click="reset">重置</button>
            </div>
            <p v-if="error" style="color:#c5485d;margin-top:14px">{{ error }}</p>
          </div>
          <div class="surface" style="padding:22px;align-self:start">
            <div class="panel-title" style="color:#22314b">入口信息</div>
            <div class="card-grid">
              <div>
                <div class="muted" style="font-size:14px">当前入口</div>
                <div style="font-size:22px;font-weight:900;margin-top:8px">{{ card?.title || '未选择' }}</div>
              </div>
              <div>
                <div class="muted" style="font-size:14px">功能摘要</div>
                <div style="margin-top:8px;line-height:1.7;color:#41516c">{{ card?.description || '请在左侧选择入口信息。' }}</div>
              </div>
              <div>
                <div class="muted" style="font-size:14px">推荐入口</div>
                <div class="chip-row" style="margin-top:10px">
                  <span v-for="tag in card?.features || []" :key="tag" class="chip">{{ tag }}</span>
                </div>
              </div>
              <div>
                <div class="muted" style="font-size:14px">登录建议</div>
                <div style="margin-top:8px;line-height:1.7;color:#41516c">
                  教研室、管理、家长、咨询师四个端口现在已经合并到同一个前端和同一个后端，登录后会按角色路由。
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup(props, { emit }) {
    const form = reactive({
      username: '',
      password: '',
      role: '',
      subRole: '',
    })
    const loading = ref(false)
    const error = ref('')
    const currentRole = computed(() => form.subRole || form.role)

    watch(
      () => props.card,
      (card) => {
        form.role = card?.code === 'management' ? 'management' : props.roles?.[0]?.value || card?.entry_roles?.[0] || ''
        form.subRole = card?.code === 'management' ? props.roles?.[0]?.value || '' : ''
        error.value = ''
      },
      { immediate: true },
    )

    function reset() {
      form.username = ''
      form.password = ''
      form.role = props.card?.code === 'management' ? 'management' : props.roles?.[0]?.value || props.card?.entry_roles?.[0] || ''
      form.subRole = props.card?.code === 'management' ? props.roles?.[0]?.value || '' : ''
      error.value = ''
    }

    async function submit() {
      try {
        loading.value = true
        error.value = ''
        const payload = {
          username: form.username.trim(),
          password: form.password,
          portal: props.card?.code || 'child',
          role: currentRole.value || props.card?.entry_roles?.[0] || '',
        }
        const data = await login(payload)
        emit('success', data)
      } catch (err) {
        error.value = err.message || '登录失败'
      } finally {
        loading.value = false
      }
    }

    return {
      form,
      loading,
      error,
      managementRoles,
      submit,
      reset,
      currentRole,
    }
  },
}

const AssistantDialog = {
  props: ['visible', 'role', 'title', 'profile', 'shortcuts', 'childId'],
  emits: ['close'],
  template: `
    <div v-if="visible" class="assistant-mask">
      <div class="assistant-card">
        <div class="assistant-header">
          <div>
            <h2 class="assistant-title">{{ title || 'AI 数字人助手' }}</h2>
            <p class="assistant-subtitle">NVIDIA 大模型驱动 · 文本问答 · 语音播报</p>
          </div>
          <div class="toolbar-actions">
            <span class="assistant-status"><span class="assistant-dot"></span>{{ loading ? '思考中' : '在线' }}</span>
            <button class="button button-ghost" @click="voiceEnabled = !voiceEnabled">
              {{ voiceEnabled ? '语音开' : '语音关' }}
            </button>
            <button class="button button-ghost" @click="$emit('close')">关闭</button>
          </div>
        </div>

        <div class="assistant-body">
          <aside class="assistant-side">
            <div class="assistant-avatar-card">
              <div class="assistant-avatar">
                <img v-if="avatarIsImage" :src="avatarText" alt="avatar" />
                <span v-else>{{ avatarText }}</span>
              </div>
              <div style="text-align:center">
                <div style="font-weight:900;font-size:18px">{{ assistantName }}</div>
                <div class="muted" style="font-size:13px">{{ roleLabel }}</div>
              </div>
            </div>
            <div>
              <div class="badge" style="margin-bottom:10px">当前状态</div>
              <div class="assistant-chip-row">
                <span v-for="tag in contextTags" :key="tag" class="assistant-chip">{{ tag }}</span>
              </div>
            </div>
            <div>
              <div class="badge" style="margin-bottom:10px">快捷提问</div>
              <div class="assistant-chip-row">
                <button v-for="chip in shortcuts" :key="chip" class="assistant-chip" @click="quickAsk(chip)">{{ chip }}</button>
              </div>
            </div>
          </aside>

          <section class="assistant-chat">
            <div class="assistant-messages">
              <div v-for="message in messages" :key="message.id" :class="['assistant-message', message.role]">
                <div>{{ message.content }}</div>
                <div v-if="message.provider || (message.citations && message.citations.length)" class="meta">
                  <span v-if="message.provider">来源：{{ message.provider }}</span>
                  <span v-if="message.citations && message.citations.length"> · 参考 {{ message.citations.length }} 条</span>
                </div>
              </div>
            </div>
            <div class="assistant-footer">
              <div class="assistant-input-row">
                <textarea
                  v-model="input"
                  rows="3"
                  placeholder="输入想咨询的问题，支持换行"
                  @keydown.enter.exact.prevent="submit"
                ></textarea>
                <div style="display:grid;gap:10px;align-content:stretch;width:140px">
                  <button class="button button-primary" :disabled="loading" @click="submit">
                    {{ loading ? '发送中...' : '发送' }}
                  </button>
                  <button class="button button-ghost" @click="clearConversation">清空</button>
                </div>
              </div>
              <div class="assistant-quick">
                <button v-for="chip in shortcuts" :key="chip" @click="quickAsk(chip)">{{ chip }}</button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  `,
  setup(props) {
    const messages = ref([])
    const input = ref('')
    const loading = ref(false)
    const voiceEnabled = ref(true)

    const assistantName = computed(() => props.profile?.assistant_name || '星萌小助手')
    const roleLabel = computed(() => {
      const labels = {
        child: '儿童端 · 训练与奖励',
        parent: '家长端 · 报告与问答',
        counselor: '咨询师端 · 接单与干预',
        management: '管理端 · 审核与看板',
        teacher_research: '教研室端 · 自评与整改',
        screen: '数据大屏 · 公开展示',
      }
      return labels[props.role] || '通用助手'
    })
    const avatarText = computed(() => {
      const value = props.profile?.avatar || ''
      if (/^https?:\/\//i.test(value)) return value
      return avatarDisplay(value || assistantName.value, '星')
    })
    const avatarIsImage = computed(() => /^https?:\/\//i.test(props.profile?.avatar || ''))
    const contextTags = computed(() => {
      const tags = [roleLabel.value]
      if (props.profile?.nickname) tags.push(props.profile.nickname)
      if (props.profile?.favorite_subject) tags.push(props.profile.favorite_subject)
      if (props.profile?.theme_key) tags.push(props.profile.theme_key)
      return tags
    })

    function pushMessage(role, content, extra = {}) {
      messages.value.push({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role,
        content,
        ...extra,
      })
    }

    function speak(text) {
      if (!voiceEnabled.value || !window.speechSynthesis || !text) return
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'zh-CN'
      utterance.rate = 1
      utterance.pitch = 1.04
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(utterance)
    }

    async function submit() {
      const question = input.value.trim()
      if (!question || loading.value) return
      input.value = ''
      pushMessage('user', question)
      loading.value = true
      try {
        const response = await api.post('/api/v1/ai/chat', {
          question,
          role: props.role || 'parent',
          child_id: props.childId || null,
        })
        pushMessage('assistant', response.answer || '暂时没有返回内容', {
          provider: response.provider || 'local',
          citations: response.citations || [],
        })
        speak(response.answer || '')
      } catch (error) {
        pushMessage('assistant', error.message || 'AI 服务暂时不可用，请稍后再试。')
      } finally {
        loading.value = false
      }
    }

    async function quickAsk(question) {
      input.value = question
      await submit()
    }

    function clearConversation() {
      messages.value = []
      pushMessage('assistant', `你好，我是${assistantName.value}。你可以直接问我筛查、训练、报告、预约或干预相关的问题。`, {
        provider: 'system',
      })
    }

    watch(
      () => props.visible,
      (visible) => {
        if (visible && messages.value.length === 0) {
          clearConversation()
        }
      },
      { immediate: true },
    )

    return {
      messages,
      input,
      loading,
      voiceEnabled,
      assistantName,
      roleLabel,
      avatarText,
      avatarIsImage,
      contextTags,
      submit,
      quickAsk,
      clearConversation,
    }
  },
}

const LandingView = {
  components: { RoleCard, LoginDialog },
  template: `
    <div class="page-shell">
      <div class="container" style="padding: 34px 0 42px">
        <div style="display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:28px">
          <div class="badge">星萌乐学 · 读写障碍统一平台</div>
          <button class="button button-ghost" @click="goScreen">进入数据大屏</button>
        </div>

        <div style="text-align:center;padding:14px 0 30px">
          <div style="width:118px;height:118px;border-radius:30px;margin:0 auto 24px;display:grid;place-items:center;background:rgba(255,255,255,0.18);box-shadow:inset 0 1px 0 rgba(255,255,255,0.3)">
            <div style="width:78px;height:78px;border-radius:22px;background:linear-gradient(135deg,#f5f8ff 0%,#cfe0ff 100%);display:grid;place-items:center;color:#203552;font-size:32px;font-weight:900">
              星
            </div>
          </div>
          <h1 class="hero-title">星萌乐学统一平台</h1>
          <p class="hero-subtitle">
          </p>
        </div>

        <div class="card-grid portal-grid" style="align-items:stretch">
          <RoleCard v-for="card in cards" :key="card.code" :card="card" @select="openLogin" />
        </div>

        <div style="display:flex;justify-content:center;margin-top:28px">
          <button class="button button-primary" @click="goScreen">公开展示 · 数据大屏</button>
        </div>

        <div style="text-align:center;margin-top:32px;color:rgba(234,241,255,0.72)">
          © 2026 星萌乐学统一平台
        </div>
      </div>

      <LoginDialog
        :visible="loginVisible"
        :card="selectedCard"
        :roles="currentRoles"
        @close="loginVisible = false"
        @success="handleLoginSuccess"
      />
    </div>
  `,
  setup() {
    const router = useRouter()
    const cards = ref([])
    const selectedCard = ref(null)
    const loginVisible = ref(false)
    const entryMap = ref({})

    const currentRoles = computed(() => {
      if (!selectedCard.value) return []
      if (selectedCard.value.code === 'management') {
        const roles = (entryMap.value.management || selectedCard.value.entry_roles || []).filter((role) => role !== 'management')
        return roles.map((role) => ({
          value: role,
          label:
            role === 'review_group'
              ? '评教小组'
              : role === 'review_office'
                ? '评教小组办公室'
                : '教务处',
        }))
      }
      return (selectedCard.value.entry_roles || []).map((role) => ({
        value: role,
        label:
          role === 'child'
            ? '儿童端'
            : role === 'parent'
              ? '家长端'
              : role === 'counselor'
                ? '咨询师端'
                : '管理端',
      }))
    })

    onMounted(async () => {
      try {
        const data = await api.get('/api/v1/public/entry-points')
        cards.value = data.cards || fallbackCards
        entryMap.value = data.login_roles || {}
      } catch {
        cards.value = fallbackCards
        entryMap.value = {
          management: ['review_group', 'review_office', 'academic_affairs'],
        }
      }
    })

    function openLogin(card) {
      selectedCard.value = card
      loginVisible.value = true
    }

    function handleLoginSuccess(data) {
      loginVisible.value = false
      router.push(`/portal/${data.portal || data.user.role}`)
    }

    function goScreen() {
      router.push('/screen')
    }

    return {
      cards,
      selectedCard,
      loginVisible,
      currentRoles,
      openLogin,
      handleLoginSuccess,
      goScreen,
    }
  },
}

const PortalView = {
  components: { ShellLayout, StatCard, PanelCard, AssistantDialog },
  template: `
    <ShellLayout
      :title="config.title"
      :subtitle="config.subtitle"
      :menu="config.menu"
      :activeKey="activeTab"
      :user="state.user"
      @change-tab="activeTab = $event"
    >
      <template #header-actions>
        <button class="button button-ghost" @click="router.push('/')">返回首页</button>
        <button class="button button-ghost" @click="router.push('/screen')">进入大屏</button>
        <select class="theme-select" v-model="themeKey" @change="selectTheme(themeKey)">
          <option v-for="theme in themeOptions" :key="theme.key" :value="theme.key">
            {{ theme.label }}
          </option>
        </select>
        <button class="button button-ghost" @click="assistantVisible = true">AI 数字人</button>
        <button class="button button-primary" @click="logoutAndBack">退出登录</button>
      </template>

      <div class="stat-grid" style="margin-bottom:18px">
        <StatCard v-for="item in stats" :key="item.label" :label="item.label" :value="item.value" :note="item.note" />
      </div>

      <div v-if="activeTab === 'overview'" class="split-grid">
        <PanelCard title="核心业务">
          <div class="table-like">
            <div v-for="item in primaryList" :key="item.title" class="row-card">
              <div>
                <div class="row-title">{{ item.title }}</div>
                <div class="row-subtitle">{{ item.subtitle }}</div>
              </div>
              <div class="soft-pill">{{ item.value }}</div>
            </div>
          </div>
        </PanelCard>

        <PanelCard title="最近动态" variant="light">
          <div class="table-like">
            <div v-for="item in recentList" :key="item.title" class="row-card light">
              <div>
                <div class="row-title">{{ item.title }}</div>
                <div class="row-subtitle">{{ item.content }}</div>
              </div>
              <div class="soft-pill">{{ item.time || '刚刚' }}</div>
            </div>
          </div>
        </PanelCard>
      </div>

      <div v-else-if="activeTab === 'profile'" class="panel-grid">
        <PanelCard title="个人资料中心" variant="light">
          <div class="profile-shell">
            <div class="profile-header">
              <div>
                <div class="badge">可自定义昵称、头像、爱好、兴趣、签名与主题</div>
              </div>
              <div class="toolbar-actions">
                <button class="button button-primary" @click="saveProfile">保存资料</button>
                <button class="button button-ghost" @click="resetProfileForm">恢复默认</button>
              </div>
            </div>

            <div class="profile-form">
              <div class="field">
                <label>昵称</label>
                <input v-model="profileDraft.nickname" placeholder="请输入昵称" />
              </div>
              <div class="field">
                <label>头像</label>
                <input v-model="profileDraft.avatar" placeholder="输入表情、代号或头像链接" />
              </div>
              <div class="field full">
                <label>头像预设</label>
                <div class="avatar-grid">
                  <button
                    v-for="preset in AVATAR_PRESETS"
                    :key="preset.value"
                    type="button"
                    :class="['avatar-option', { active: profileDraft.avatar === preset.value }]"
                    @click="setAvatarPreset(preset.value)"
                  >
                    <span>{{ preset.value }}</span>
                    <small>{{ preset.label }}</small>
                  </button>
                </div>
              </div>
              <div class="field">
                <label>个人签名</label>
                <input v-model="profileDraft.signature" placeholder="一句话介绍自己" />
              </div>
              <div class="field">
                <label>偏好学科</label>
                <input v-model="profileDraft.favorite_subject" placeholder="例如：语文 / 数学" />
              </div>
              <div class="field full">
                <label>个人简介</label>
                <textarea v-model="profileDraft.bio" rows="3" placeholder="介绍一下你的学习目标、风格或需求"></textarea>
              </div>
              <div class="field full">
                <label>爱好（逗号、顿号或换行分隔）</label>
                <textarea v-model="profileDraft.hobbiesText" rows="2" placeholder="例如：阅读, 拼图, 机器人"></textarea>
              </div>
              <div class="field full">
                <label>兴趣（逗号、顿号或换行分隔）</label>
                <textarea v-model="profileDraft.interestsText" rows="2" placeholder="例如：机甲, 画画, 英语"></textarea>
              </div>
              <div class="field">
                <label>偏好颜色</label>
                <input v-model="profileDraft.favorite_color" placeholder="例如：蓝色" />
              </div>
              <div class="field">
                <label>AI 助手称呼</label>
                <input v-model="profileDraft.assistant_name" placeholder="例如：星萌小助手" />
              </div>
              <div class="field full">
                <label>备用信息 JSON</label>
                <textarea v-model="profileDraft.extraText" rows="3" placeholder='{"goal":"提升阅读流畅性"}'></textarea>
              </div>
            </div>

            <div class="profile-preview">
              <div class="avatar-row">
                <div class="avatar-preview">
                  <img v-if="avatarPreviewIsImage" :src="profileDraft.avatar" alt="avatar" />
                  <span v-else>{{ avatarDisplay(profileDraft.avatar || profileDraft.nickname || state.user?.display_name || '星') }}</span>
                </div>
                <div>
                  <div style="font-size:24px;font-weight:900">{{ profileDraft.nickname || state.user?.display_name }}</div>
                  <div class="muted">{{ profileDraft.signature || '还没有填写签名' }}</div>
                  <div style="margin-top:10px" class="assistant-chip-row">
                    <span v-for="tag in profileTags" :key="tag" class="assistant-chip">{{ tag }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <div class="panel-title">主题切换</div>
              <div class="theme-gallery">
                <div
                  v-for="theme in themeOptions"
                  :key="theme.key"
                  :class="['theme-card', { active: profileDraft.theme_key === theme.key }]"
                  @click="selectTheme(theme.key)"
                >
                  <div class="theme-swatch" :style="themePreviewStyle(theme)"></div>
                  <div>
                    <h4 class="theme-label">{{ theme.label }}</h4>
                    <p class="theme-desc">{{ theme.description }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="badge" v-if="profileStatus" style="justify-self:start">{{ profileStatus }}</div>
          </div>
        </PanelCard>
      </div>

      <div v-else class="panel-grid">
        <PanelCard :title="tabTitle" variant="light">
          <div class="table-like">
            <div v-for="item in tabList" :key="item.id || item.key || item.title" class="row-card light">
              <div>
                <div class="row-title">{{ item.title || item.name || item.label }}</div>
                <div class="row-subtitle">{{ item.subtitle || item.summary || item.category || item.content || item.status }}</div>
              </div>
              <div class="soft-pill">{{ item.value || item.score || item.status || item.created_at || '' }}</div>
            </div>
          </div>
        </PanelCard>
      </div>

      <AssistantDialog
        :visible="assistantVisible"
        :role="role"
        :title="assistantTitle"
        :profile="state.profile || profileSnapshot"
        :shortcuts="assistantShortcuts"
        :child-id="assistantChildId"
        @close="assistantVisible = false"
      />
    </ShellLayout>
  `,
  setup() {
    const route = useRoute()
    const router = useRouter()
    const role = computed(() => route.params.role || 'child')
    const config = computed(() => roleConfig[role.value] || roleConfig.child)
    const activeTab = ref('overview')
    const overview = ref({})
    const profileSnapshot = ref(null)
    const profileStatus = ref('')
    const assistantVisible = ref(false)
    const themeOptions = computed(() => getThemeOptions(role.value))
    const themeKey = ref(getStoredThemeKey(role.value))
    const profileDraft = reactive(formFromProfile(null, role.value))

    const assistantShortcuts = computed(() => {
      const shortcuts = {
        child: ['我应该先训练哪一关？', '怎样更快分清 b 和 d？', '今天的奖励怎么拿？'],
        parent: ['如何解读筛查报告？', '家庭训练怎么安排？', '什么时候需要预约咨询？'],
        counselor: ['帮我生成干预计划模板', '今天有哪些待处理订单？', '如何跟进高风险儿童？'],
        management: ['今日看板异常有哪些？', '如何查看审计记录？', '帮我做系统配置建议'],
        teacher_research: ['教研材料如何归档？', '自评要关注哪些指标？', '整改闭环怎么追踪？'],
      }
      return shortcuts[role.value] || shortcuts.parent
    })

    const assistantTitle = computed(() => `${config.value.title} · AI 数字人`)
    const assistantChildId = computed(() => {
      if (role.value === 'child') {
        return overview.value?.levels?.child?.id || overview.value?.dashboard?.shared?.summary?.child_id || null
      }
      if (role.value === 'parent') {
        return overview.value?.children?.children?.[0]?.id || null
      }
      if (role.value === 'counselor') {
        return overview.value?.orders?.orders?.[0]?.child_id || null
      }
      return null
    })
    const avatarPreviewIsImage = computed(() => /^https?:\/\//i.test(profileDraft.avatar || ''))
    const profileTags = computed(() => {
      const tags = []
      splitList(profileDraft.hobbiesText).slice(0, 3).forEach((item) => tags.push(item))
      splitList(profileDraft.interestsText).slice(0, 3).forEach((item) => tags.push(item))
      if (profileDraft.favorite_color) tags.push(profileDraft.favorite_color)
      if (profileDraft.favorite_subject) tags.push(profileDraft.favorite_subject)
      return tags.length ? tags : ['未填写资料']
    })

    const stats = computed(() => {
      if (role.value === 'child') {
        return [
          { label: '完成关卡', value: overview.value?.dashboard?.summary?.completed_sessions ?? 0, note: '最近训练' },
          { label: '平均评估分', value: overview.value?.dashboard?.summary?.average_score ?? 0, note: '综合得分' },
          { label: '风险提示', value: overview.value?.dashboard?.summary?.high_risk_count ?? 0, note: '待关注' },
          { label: '奖励徽章', value: overview.value?.rewards?.badge || '星徽章', note: '已解锁' },
        ]
      }
      if (role.value === 'parent') {
        return [
          { label: '儿童档案', value: overview.value?.children?.children?.length || 0, note: '家庭绑定' },
          { label: '筛查报告', value: overview.value?.reports?.reports?.length || 0, note: '最新结果' },
          { label: '预约数量', value: overview.value?.appointments?.orders?.length || 0, note: '待跟进' },
          { label: 'AI 问答', value: overview.value?.chat?.messages?.length || 0, note: '历史记录' },
        ]
      }
      if (role.value === 'counselor') {
        return [
          { label: '咨询订单', value: overview.value?.orders?.orders?.length || 0, note: '待处理' },
          { label: '干预方案', value: overview.value?.plans?.plans?.length || 0, note: '执行中' },
          { label: '知识文章', value: overview.value?.knowledge?.articles?.length || 0, note: '可检索' },
          { label: '评估摘要', value: overview.value?.summary?.kpis?.high_risk_count ?? 0, note: '风险概览' },
        ]
      }
      return [
        { label: '用户总数', value: overview.value?.dashboard?.summary?.users || overview.value?.summary?.children || 0, note: '账号治理' },
        { label: '内容总数', value: overview.value?.articles?.articles?.length || 0, note: '内容审核' },
        { label: '审计记录', value: overview.value?.logs?.logs?.length || 0, note: '平台留痕' },
        { label: '系统脉冲', value: overview.value?.dashboard?.live?.pulse || 0, note: '在线同步' },
      ]
    })

    const primaryList = computed(() => {
      if (role.value === 'child') {
        return [
          { title: '关卡训练', subtitle: '趣味游戏与过程采集', value: overview.value?.levels?.levels?.length || 12 },
          { title: '成长奖励', subtitle: '解锁徽章与星星', value: overview.value?.rewards?.badge || '星徽章' },
          { title: '最近报告', subtitle: '查看当前筛查结果', value: overview.value?.reports?.reports?.[0]?.risk_text || '待更新' },
        ]
      }
      if (role.value === 'parent') {
        return [
          { title: '儿童档案', subtitle: '家庭绑定信息', value: overview.value?.children?.children?.length || 0 },
          { title: '报告阅读', subtitle: '筛查与问卷结果', value: overview.value?.reports?.reports?.length || 0 },
          { title: '咨询预约', subtitle: '订单与人工转接', value: overview.value?.appointments?.orders?.length || 0 },
        ]
      }
      if (role.value === 'counselor') {
        return [
          { title: '咨询订单', subtitle: '待处理与已完成', value: overview.value?.orders?.orders?.length || 0 },
          { title: '干预方案', subtitle: '模板与执行进度', value: overview.value?.plans?.plans?.length || 0 },
          { title: '知识库', subtitle: '文章与资料', value: overview.value?.knowledge?.articles?.length || 0 },
        ]
      }
      return [
        { title: '用户总数', subtitle: '全平台账号', value: overview.value?.dashboard?.summary?.users || 0 },
        { title: '内容总数', subtitle: '文章与资料', value: overview.value?.articles?.articles?.length || 0 },
        { title: '审计记录', subtitle: '系统行为日志', value: overview.value?.logs?.logs?.length || 0 },
      ]
    })

    const recentList = computed(() => {
      if (role.value === 'child') {
        return (overview.value?.dashboard?.alerts || []).map((item) => ({
          title: item.child,
          content: item.suggestion,
          time: item.risk_level,
        }))
      }
      if (role.value === 'parent') {
        return (overview.value?.reports?.reports || []).slice(0, 5).map((item) => ({
          title: item.conclusion || item.risk_text,
          content: item.recommendations?.join('，') || item.summary || '',
          time: item.created_at,
        }))
      }
      if (role.value === 'counselor') {
        return (overview.value?.orders?.orders || []).slice(0, 5).map((item) => ({
          title: item.title,
          content: item.summary || item.status,
          time: item.created_at,
        }))
      }
      return (overview.value?.logs?.logs || []).slice(0, 5).map((item) => ({
        title: item.action,
        content: item.detail || item.target_type,
        time: item.created_at,
      }))
    })

    const tabList = computed(() => {
      if (role.value === 'child') {
        if (activeTab.value === 'levels') return overview.value?.levels?.levels || []
        if (activeTab.value === 'reports') return overview.value?.reports?.reports || []
        if (activeTab.value === 'rewards') return [overview.value?.rewards || {}]
        return []
      }
      if (role.value === 'parent') {
        if (activeTab.value === 'children') return overview.value?.children?.children || []
        if (activeTab.value === 'reports') return overview.value?.reports?.reports || []
        if (activeTab.value === 'appointments') return overview.value?.appointments?.orders || []
        if (activeTab.value === 'chat') return overview.value?.chat?.messages || []
        return []
      }
      if (role.value === 'counselor') {
        if (activeTab.value === 'orders') return overview.value?.orders?.orders || []
        if (activeTab.value === 'plans') return overview.value?.plans?.plans || []
        if (activeTab.value === 'knowledge') return overview.value?.knowledge?.articles || []
        return []
      }
      if (activeTab.value === 'users') return overview.value?.users?.users || []
      if (activeTab.value === 'content') return overview.value?.articles?.articles || []
      if (activeTab.value === 'settings') return overview.value?.settings?.settings || []
      if (activeTab.value === 'logs') return overview.value?.logs?.logs || []
      return []
    })

    const tabTitle = computed(() => config.value.menu.find((item) => item.key === activeTab.value)?.label || '详情')

    watch(
      role,
      async () => {
        activeTab.value = 'overview'
        profileStatus.value = ''
        assistantVisible.value = false
        themeKey.value = getStoredThemeKey(role.value)
        await loadData()
      },
      { immediate: true },
    )

    async function loadData() {
      let profileData = null
      try {
        profileData = await api.get('/api/v1/auth/profile')
      } catch {
        profileData = { profile: state.profile || null }
      }

      profileSnapshot.value = profileData?.profile || null
      Object.assign(profileDraft, formFromProfile(profileSnapshot.value, role.value))
      themeKey.value = profileDraft.theme_key || getStoredThemeKey(role.value)
      applyTheme(role.value, themeKey.value)

      if (role.value === 'child') {
        const [dashboard, levels, reports, rewards] = await Promise.all([
          api.get('/api/v1/child/dashboard'),
          api.get('/api/v1/child/levels'),
          api.get('/api/v1/child/reports'),
          api.get('/api/v1/child/rewards/status'),
        ])
        overview.value = { dashboard, levels, reports, rewards }
        return
      }
      if (role.value === 'parent') {
        const [children, reports, appointments, knowledge, chat] = await Promise.all([
          api.get('/api/v1/parent/children'),
          api.get('/api/v1/parent/reports'),
          api.get('/api/v1/parent/appointments'),
          api.get('/api/v1/parent/knowledge'),
          api.get('/api/v1/parent/chat/history').catch(() => ({ messages: [] })),
        ])
        overview.value = { children, reports, appointments, knowledge, chat }
        return
      }
      if (role.value === 'counselor') {
        const [orders, plans, summary, knowledge] = await Promise.all([
          api.get('/api/v1/counselor/orders'),
          api.get('/api/v1/counselor/interventions'),
          api.get('/api/v1/counselor/statistics/summary'),
          api.get('/api/v1/counselor/knowledge'),
        ])
        overview.value = { orders, plans, summary, knowledge }
        return
      }
      const [dashboard, users, articles, settings, logs] = await Promise.all([
        api.get('/api/v1/admin/dashboard'),
        api.get('/api/v1/admin/users'),
        api.get('/api/v1/admin/articles'),
        api.get('/api/v1/admin/settings'),
        api.get('/api/v1/admin/audit-logs'),
      ])
      overview.value = { dashboard, users, articles, settings, logs }
    }

    async function saveProfile(options = {}) {
      const silent = options.silent || false
      profileStatus.value = silent ? profileStatus.value : '保存中...'
      try {
        const result = await api.put('/api/v1/auth/profile', payloadFromForm(profileDraft))
        profileSnapshot.value = result.profile || null
        state.user = result.user || state.user
        state.profile = result.profile || state.profile
        localStorage.setItem('xm_user', JSON.stringify(state.user))
        localStorage.setItem('xm_profile', JSON.stringify(state.profile || null))
        Object.assign(profileDraft, formFromProfile(profileSnapshot.value, role.value))
        themeKey.value = profileDraft.theme_key || getStoredThemeKey(role.value)
        applyTheme(role.value, themeKey.value)
        profileStatus.value = '资料已保存'
        return result
      } catch (error) {
        profileStatus.value = error.message || '保存失败'
        throw error
      }
    }

    async function selectTheme(key) {
      profileDraft.theme_key = key
      themeKey.value = key
      applyTheme(role.value, key)
      try {
        await saveProfile({ silent: true })
        profileStatus.value = '主题已切换'
      } catch {
        profileStatus.value = '主题切换已应用，但保存失败'
      }
    }

    function setAvatarPreset(value) {
      profileDraft.avatar = value
    }

    function resetProfileForm() {
      Object.assign(profileDraft, formFromProfile(profileSnapshot.value, role.value))
      themeKey.value = profileDraft.theme_key || getStoredThemeKey(role.value)
      applyTheme(role.value, themeKey.value)
      profileStatus.value = '已恢复为当前保存的资料'
    }

    async function logoutAndBack() {
      await logout()
      router.push('/')
    }

    return {
      router,
      state,
      config,
      activeTab,
      stats,
      primaryList,
      recentList,
      tabList,
      tabTitle,
      themeKey,
      themeOptions,
      profileDraft,
      profileStatus,
      assistantVisible,
      assistantShortcuts,
      assistantTitle,
      assistantChildId,
      avatarPreviewIsImage,
      profileTags,
      selectTheme,
      saveProfile,
      resetProfileForm,
      setAvatarPreset,
      avatarDisplay,
      themePreviewStyle,
      logoutAndBack,
    }
  },
}

const BigScreenView = {
  components: { PanelCard, StatCard, AssistantDialog },
  template: `
    <div class="screen-shell">
      <div class="screen-topbar">
        <div>
          <div class="badge">公开展示 · 实时数据大屏</div>
          <h1 class="screen-title">星萌乐学数据大屏</h1>
          <p class="screen-subtitle">统一展示筛查、训练、咨询和管理状态，数据默认每 3 秒刷新一次。</p>
        </div>
        <div class="toolbar-actions">
          <select class="theme-select" v-model="themeKey" @change="selectTheme(themeKey)">
            <option v-for="theme in themeOptions" :key="theme.key" :value="theme.key">
              {{ theme.label }}
            </option>
          </select>
          <span class="badge">主题：{{ currentTheme.label }}</span>
          <button class="button button-ghost" @click="assistantVisible = true">AI 数字人</button>
          <button class="button button-ghost" @click="back">返回首页</button>
          <span class="badge">当前连接：{{ connected ? 'WebSocket' : '轮询' }}</span>
          <span class="badge">更新时间：{{ liveTime }}</span>
        </div>
      </div>

      <div class="screen-grid">
        <div class="stat-grid">
          <StatCard v-for="item in topStats" :key="item.label" :label="item.label" :value="item.value" :note="item.note" />
        </div>

        <div class="screen-main">
          <PanelCard title="重点关注 TOP 10">
            <div class="table-like">
              <div v-for="item in ranking" :key="item.rank" class="row-card">
                <div>
                  <div class="row-title">
                    <span style="display:inline-block;width:30px;color:#ffd65e">{{ item.rank }}</span>
                    {{ item.name }}
                  </div>
                  <div class="row-subtitle">{{ item.school }} · {{ item.status }}</div>
                </div>
                <div class="soft-pill">{{ item.score }} 分</div>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="评分等级分布">
            <div ref="pieRef" class="screen-chart"></div>
          </PanelCard>
        </div>

        <div class="screen-main">
          <PanelCard title="各学校平均分对比">
            <div ref="barRef" class="screen-chart large"></div>
          </PanelCard>

          <PanelCard title="实时趋势">
            <div ref="lineRef" class="screen-chart large"></div>
          </PanelCard>
        </div>
      </div>

      <div class="screen-footer">© 2026 星萌乐学统一平台 · 数据每 5 秒自动刷新</div>

      <AssistantDialog
        :visible="assistantVisible"
        role="screen"
        :title="assistantTitle"
        :profile="assistantProfile"
        :shortcuts="assistantShortcuts"
        :child-id="null"
        @close="assistantVisible = false"
      />
    </div>
  `,
  setup() {
    const router = useRouter()
    const live = ref({})
    const ranking = ref([])
    const distribution = ref([])
    const schoolCompare = ref([])
    const timeline = ref([])
    const connected = ref(false)
    const liveTime = ref('—')
    const pieRef = ref(null)
    const barRef = ref(null)
    const lineRef = ref(null)
    const assistantVisible = ref(false)
    const themeOptions = computed(() => getThemeOptions('screen'))
    const themeKey = ref(getStoredThemeKey('screen'))
    const currentTheme = computed(() => getThemeByKey('screen', themeKey.value))
    const assistantShortcuts = [
      '今天大屏有哪些变化？',
      '当前评分分布怎么理解？',
      '请用一句话总结系统状态',
    ]
    const assistantTitle = computed(() => '星萌乐学数据大屏 · AI 数字人')
    const assistantProfile = computed(() => ({
      assistant_name: '星萌大屏助手',
      avatar: '📊',
      nickname: '大屏指挥官',
      theme_key: themeKey.value,
    }))

    let socket = null
    let timer = null
    let pieChart = null
    let barChart = null
    let lineChart = null

    const topStats = computed(() => [
      { label: '儿童总数', value: live.value.children || 0, note: '累计建档' },
      { label: '筛查报告', value: live.value.screening_reports || 0, note: '近期开具' },
      { label: '待处理订单', value: live.value.pending_orders || 0, note: '咨询转接' },
      { label: '实时脉冲', value: live.value.pulse || 0, note: live.value.refresh_hint || '实时刷新' },
    ])

    onMounted(async () => {
      applyTheme('screen', themeKey.value)
      await refresh()
      initCharts()
      connectSocket()
      window.addEventListener('resize', resizeCharts)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', resizeCharts)
      if (socket) socket.close()
      if (timer) clearInterval(timer)
      pieChart?.dispose()
      barChart?.dispose()
      lineChart?.dispose()
    })

    async function refresh() {
      const data = await api.get('/api/v1/public/dashboard/overview')
      applySnapshot(data)
    }

    function selectTheme(key) {
      themeKey.value = key
      applyTheme('screen', key)
    }

    function applySnapshot(snapshot) {
      live.value = snapshot.summary ? { ...snapshot.summary, ...(snapshot.live || {}) } : snapshot.live || {}
      ranking.value = snapshot.ranking || []
      distribution.value = snapshot.score_distribution || []
      schoolCompare.value = snapshot.school_compare || []
      timeline.value = snapshot.timeline || []
      liveTime.value = snapshot.generated_at
        ? new Date(snapshot.generated_at).toLocaleTimeString('zh-CN', { hour12: false })
        : '—'
      updateCharts()
    }

    function connectSocket() {
      try {
        socket = new WebSocket(`${location.origin.replace('http', 'ws')}/api/v1/public/dashboard/stream`)
        socket.onopen = () => {
          connected.value = true
          if (timer) {
            clearInterval(timer)
            timer = null
          }
        }
        socket.onmessage = (event) => {
          try {
            applySnapshot(JSON.parse(event.data))
          } catch {
            // ignore
          }
        }
        socket.onclose = () => {
          connected.value = false
          if (!timer) {
            timer = setInterval(refresh, 5000)
          }
        }
        socket.onerror = () => {
          connected.value = false
        }
      } catch {
        connected.value = false
        timer = setInterval(refresh, 5000)
      }
    }

    function initCharts() {
      pieChart = echarts.init(pieRef.value)
      barChart = echarts.init(barRef.value)
      lineChart = echarts.init(lineRef.value)
      updateCharts()
    }

    function updateCharts() {
      if (!pieChart || !barChart || !lineChart) return
      const pieOption = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item' },
        legend: {
          orient: 'vertical',
          left: 10,
          top: 40,
          textStyle: { color: '#c9d7ff', fontSize: 13 },
        },
        series: [
          {
            type: 'pie',
            radius: ['58%', '82%'],
            center: ['67%', '50%'],
            avoidLabelOverlap: false,
            label: { show: false },
            data: distribution.value.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })),
          },
        ],
      }

      const barOption = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        grid: { left: 34, right: 18, top: 36, bottom: 28 },
        xAxis: {
          type: 'category',
          data: schoolCompare.value.map((item) => item.name),
          axisLabel: { color: '#b7c7ef', interval: 0 },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.14)' } },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#b7c7ef' },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        },
        series: [
          {
            type: 'bar',
            data: schoolCompare.value.map((item) => item.value),
            barWidth: 56,
            itemStyle: {
              borderRadius: [12, 12, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#78b1ff' },
                { offset: 1, color: '#5be0ef' },
              ]),
            },
          },
        ],
      }

      const lineOption = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        grid: { left: 36, right: 16, top: 38, bottom: 28 },
        xAxis: {
          type: 'category',
          data: timeline.value.map((item) => item.date.slice(5)),
          axisLabel: { color: '#b7c7ef' },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.14)' } },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#b7c7ef' },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        },
        series: [
          {
            name: '筛查',
            type: 'line',
            smooth: true,
            data: timeline.value.map((item) => item.screening),
            symbol: 'circle',
            symbolSize: 10,
            lineStyle: { width: 4, color: '#7bc6ff' },
            itemStyle: { color: '#7bc6ff' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(123,198,255,0.32)' },
                { offset: 1, color: 'rgba(123,198,255,0.02)' },
              ]),
            },
          },
        ],
      }

      pieChart.setOption(pieOption, true)
      barChart.setOption(barOption, true)
      lineChart.setOption(lineOption, true)
    }

    function resizeCharts() {
      pieChart?.resize()
      barChart?.resize()
      lineChart?.resize()
    }

    function back() {
      router.push('/')
    }

    return {
      live,
      ranking,
      connected,
      liveTime,
      topStats,
      themeOptions,
      themeKey,
      currentTheme,
      assistantVisible,
      assistantShortcuts,
      assistantTitle,
      assistantProfile,
      pieRef,
      barRef,
      lineRef,
      selectTheme,
      back,
    }
  },
}

const routes = [
  { path: '/', component: LandingView },
  { path: '/screen', component: BigScreenView, meta: { public: true } },
  { path: '/portal/:role', component: PortalView, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.public) {
    return true
  }
  if (to.meta.requiresAuth && !state.token) {
    return { path: '/' }
  }
  return true
})

const AppRoot = {
  template: `<router-view></router-view>`,
}

async function bootstrap() {
  await hydrateSession()
  createApp(AppRoot)
    .component('RoleCard', RoleCard)
    .component('StatCard', StatCard)
    .component('PanelCard', PanelCard)
    .component('ShellLayout', ShellLayout)
    .component('LoginDialog', LoginDialog)
    .use(router)
    .mount('#app')
}

bootstrap()
