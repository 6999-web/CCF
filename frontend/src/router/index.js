import { createRouter, createWebHistory } from 'vue-router'

import { state } from '../store/auth'

const routes = [
  { path: '/', name: 'landing', component: () => import('../views/LandingView.vue') },
  { path: '/screen', name: 'screen', component: () => import('../views/BigScreenView.vue'), meta: { public: true } },
  { path: '/portal/:role', name: 'portal', component: () => import('../views/PortalView.vue'), meta: { requiresAuth: true } },
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

export default router
