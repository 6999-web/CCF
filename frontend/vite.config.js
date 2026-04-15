import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '101.33.210.169',
    port: 5052,
    proxy: {
      '/api': {
        target: 'http://101.33.210.169:5051',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://101.33.210.169:5051',
        ws: true,
      },
    },
  },
})
