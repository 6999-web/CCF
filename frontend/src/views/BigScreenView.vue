<template>
  <div class="page-shell">
    <div class="page-inner">
      <header class="landing-head glass-strong">
        <div>
          <span class="badge">Realtime Command Screen</span>
          <h2 style="margin: 10px 0 0; font-size: clamp(30px, 4.4vw, 50px); font-family: var(--font-display)">悦读相伴 · 全局学习态势</h2>
          <p class="muted" style="margin: 6px 0 0">实时展示筛查、训练、咨询和学校分布，支持 WebSocket 自动刷新。</p>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap">
          <button class="button button-ghost" @click="router.push('/')">返回首页</button>
          <span class="badge">连接：{{ connected ? 'WebSocket' : '轮询' }}</span>
          <span class="badge">更新时间：{{ liveTime }}</span>
        </div>
      </header>

      <section class="screen-grid">
        <div class="screen-metrics">
          <article v-for="item in topStats" :key="item.label" class="stat-card glass">
            <div class="label">{{ item.label }}</div>
            <div class="value">{{ item.value }}</div>
            <div class="muted" style="margin-top: 5px; font-size: 12px">{{ item.note }}</div>
          </article>
        </div>

        <div class="screen-main">
          <section class="screen-card glass-strong">
            <h3>重点关注 TOP 10</h3>
            <div class="panel-list" style="margin-top: 10px; max-height: 320px; overflow: auto">
              <div v-for="item in ranking" :key="item.rank" class="panel-item" style="display: flex; justify-content: space-between; gap: 10px; align-items: center">
                <div>
                  <strong>{{ item.rank }}. {{ item.name }}</strong>
                  <div class="muted" style="font-size: 12px; margin-top: 2px">{{ item.school }} · {{ item.status }}</div>
                </div>
                <span class="badge">{{ item.score }} 分</span>
              </div>
            </div>
          </section>

          <section class="screen-card glass-strong">
            <h3>评分等级分布</h3>
            <div ref="pieRef" class="chart"></div>
          </section>
        </div>

        <div class="screen-main">
          <section class="screen-card glass-strong">
            <h3>学校平均分对比</h3>
            <div ref="barRef" class="chart large"></div>
          </section>

          <section class="screen-card glass-strong">
            <h3>七日趋势</h3>
            <div ref="lineRef" class="chart large"></div>
          </section>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

import { api } from '../services/api'

const router = useRouter()
const live = ref({})
const ranking = ref([])
const distribution = ref([])
const schoolCompare = ref([])
const timeline = ref([])
const connected = ref(false)
const liveTime = ref('--:--:--')

const pieRef = ref(null)
const barRef = ref(null)
const lineRef = ref(null)

let socket
let timer
let pieChart
let barChart
let lineChart

const topStats = computed(() => [
  { label: '儿童总数', value: live.value.children || 0, note: '累计建档' },
  { label: '筛查报告', value: live.value.screening_reports || 0, note: '已生成' },
  { label: '待处理咨询', value: live.value.pending_orders || 0, note: '流转中' },
  { label: '实时脉冲', value: live.value.pulse || 0, note: live.value.refresh_hint || '实时刷新' },
])

onMounted(async () => {
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

function applySnapshot(snapshot) {
  live.value = snapshot.summary ? { ...snapshot.summary, ...(snapshot.live || {}) } : snapshot.live || {}
  ranking.value = snapshot.ranking || []
  distribution.value = snapshot.score_distribution || []
  schoolCompare.value = snapshot.school_compare || []
  timeline.value = snapshot.timeline || []
  liveTime.value = snapshot.generated_at ? new Date(snapshot.generated_at).toLocaleTimeString('zh-CN', { hour12: false }) : '--:--:--'
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
        // ignore invalid frame
      }
    }
    socket.onclose = () => {
      connected.value = false
      if (!timer) timer = setInterval(refresh, 5000)
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

  pieChart.setOption(
    {
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#3e6f8a' } },
      series: [
        {
          type: 'pie',
          radius: ['46%', '70%'],
          center: ['50%', '42%'],
          label: { color: '#2e607b', formatter: '{b}\n{d}%' },
          data: distribution.value.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })),
        },
      ],
    },
    true,
  )

  barChart.setOption(
    {
      tooltip: { trigger: 'axis' },
      grid: { left: 30, right: 12, top: 28, bottom: 34 },
      xAxis: {
        type: 'category',
        data: schoolCompare.value.map((item) => item.name),
        axisLabel: { color: '#3e6f8a', interval: 0 },
        axisLine: { lineStyle: { color: 'rgba(85,145,176,0.35)' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#3e6f8a' },
        splitLine: { lineStyle: { color: 'rgba(85,145,176,0.18)' } },
      },
      series: [
        {
          type: 'bar',
          barWidth: 44,
          data: schoolCompare.value.map((item) => item.value),
          itemStyle: {
            borderRadius: [10, 10, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#47b4ff' },
              { offset: 1, color: '#5fd8b8' },
            ]),
          },
        },
      ],
    },
    true,
  )

  lineChart.setOption(
    {
      tooltip: { trigger: 'axis' },
      grid: { left: 34, right: 14, top: 26, bottom: 26 },
      xAxis: {
        type: 'category',
        data: timeline.value.map((item) => String(item.date || '').slice(5)),
        axisLabel: { color: '#3e6f8a' },
        axisLine: { lineStyle: { color: 'rgba(85,145,176,0.35)' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#3e6f8a' },
        splitLine: { lineStyle: { color: 'rgba(85,145,176,0.18)' } },
      },
      series: [
        {
          name: '筛查趋势',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          data: timeline.value.map((item) => item.screening),
          lineStyle: { width: 4, color: '#40afff' },
          itemStyle: { color: '#40afff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,175,255,0.34)' },
              { offset: 1, color: 'rgba(64,175,255,0.03)' },
            ]),
          },
        },
      ],
    },
    true,
  )
}

function resizeCharts() {
  pieChart?.resize()
  barChart?.resize()
  lineChart?.resize()
}
</script>
