<template>
  <div v-if="visible" class="dialog-mask">
    <div class="login-dialog glass-strong">
      <section class="login-dialog-copy">
        <span class="badge">{{ badgeText }}</span>
        <h3 style="margin: 12px 0 0; font-size: 28px; font-family: var(--font-display)">{{ card?.title || '统一登录' }}</h3>
        <p class="muted" style="line-height: 1.8">{{ card?.description || '登录后按角色进入对应工作台。' }}</p>
        <div class="portal-card-tags">
          <span v-for="tag in card?.features || []" :key="tag">{{ tag }}</span>
        </div>
      </section>

      <section class="login-dialog-form">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <strong>账号登录</strong>
          <button class="button button-ghost" @click="$emit('close')">关闭</button>
        </div>

        <div class="field">
          <label>用户名</label>
          <input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
        </div>

        <div class="field">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </div>

        <div v-if="showRoleSelector" class="field">
          <label>角色入口</label>
          <select v-model="form.subRole">
            <option v-for="item in roles" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </div>

        <div style="display: grid; gap: 10px; margin-top: 6px">
          <button class="button button-primary" :disabled="loading" @click="submit">{{ loading ? '登录中...' : '进入工作台' }}</button>
          <button class="button button-ghost" @click="reset">重置</button>
        </div>

        <p v-if="error" style="margin: 8px 0 0; color: #d95f5f; font-weight: 700">{{ error }}</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'

import { login } from '../store/auth'

const props = defineProps({
  visible: Boolean,
  card: Object,
  roles: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close', 'success'])

const form = reactive({
  username: '',
  password: '',
  role: '',
  subRole: '',
})

const loading = ref(false)
const error = ref('')
const isManagementPortal = computed(() => props.card?.code === 'management')
const badgeText = computed(() => (isManagementPortal.value ? '管理端安全登录' : '统一登录入口'))
const showRoleSelector = computed(() => (props.roles?.length || 0) > 1)
const currentRole = computed(() => form.subRole || form.role)

const previousBodyOverflow = ref('')

watch(
  () => props.card,
  (card) => {
    form.role = props.roles?.[0]?.value || card?.entry_roles?.[0] || card?.code || ''
    form.subRole = props.roles?.[0]?.value || ''
    error.value = ''
  },
  { immediate: true },
)

watch(
  () => props.visible,
  (visible) => {
    if (typeof document === 'undefined') return
    if (visible) {
      previousBodyOverflow.value = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      return
    }
    document.body.style.overflow = previousBodyOverflow.value || ''
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = previousBodyOverflow.value || ''
})

function reset() {
  form.username = ''
  form.password = ''
  form.role = props.roles?.[0]?.value || props.card?.entry_roles?.[0] || props.card?.code || ''
  form.subRole = props.roles?.[0]?.value || ''
  error.value = ''
}

async function submit() {
  try {
    loading.value = true
    error.value = ''
    const data = await login({
      username: form.username.trim(),
      password: form.password,
      portal: props.card?.code || 'child',
      role: currentRole.value || props.card?.entry_roles?.[0] || '',
    })
    emit('success', data)
  } catch (err) {
    error.value = err.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
