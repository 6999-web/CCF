import { reactive } from 'vue'

import { api } from '../services/api.js'

export const state = reactive({
  token: localStorage.getItem('xm_token') || '',
  user: JSON.parse(localStorage.getItem('xm_user') || 'null'),
  profile: JSON.parse(localStorage.getItem('xm_profile') || 'null'),
  portal: localStorage.getItem('xm_portal') || '',
})

export function setSession(payload) {
  state.token = payload.access_token
  state.user = payload.user
  state.profile = payload.profile || state.profile
  state.portal = payload.portal || payload.user.role
  localStorage.setItem('xm_token', payload.access_token)
  localStorage.setItem('xm_user', JSON.stringify(payload.user))
  localStorage.setItem('xm_profile', JSON.stringify(state.profile || null))
  localStorage.setItem('xm_portal', state.portal)
}

export function clearSession() {
  state.token = ''
  state.user = null
  state.profile = null
  state.portal = ''
  localStorage.removeItem('xm_token')
  localStorage.removeItem('xm_user')
  localStorage.removeItem('xm_profile')
  localStorage.removeItem('xm_portal')
}

export async function hydrateSession() {
  if (!state.token || state.user) {
    return
  }
  try {
    const data = await api.get('/api/v1/auth/me')
    state.user = data.user
    state.profile = data.profile || state.profile
    state.portal = data.portal
    localStorage.setItem('xm_user', JSON.stringify(data.user))
    localStorage.setItem('xm_profile', JSON.stringify(state.profile || null))
    localStorage.setItem('xm_portal', data.portal)
  } catch {
    clearSession()
  }
}

export async function login(payload) {
  const data = await api.post('/api/v1/auth/login', payload)
  setSession(data)
  return data
}

export async function switchRole(role) {
  const data = await api.post('/api/v1/auth/switch-role', { role })
  setSession(data)
  return data
}

export async function logout() {
  try {
    await api.post('/api/v1/auth/logout', {})
  } finally {
    clearSession()
  }
}
