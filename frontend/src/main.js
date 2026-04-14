import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { hydrateSession } from './store/auth'
import './styles/global.css'

async function bootstrap() {
  await hydrateSession()
  createApp(App).use(router).mount('#app')
}

bootstrap()

