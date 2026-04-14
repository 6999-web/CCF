<template>
  <button class="portal-card glass" :style="accentStyle" @click="$emit('select', card)">
    <div class="badge">{{ icon }} {{ card.subtitle || '统一入口' }}</div>
    <div class="portal-card-body">
      <div class="portal-card-title">{{ card.title }}</div>
      <p class="portal-card-desc">{{ card.description }}</p>
    </div>
    <div class="portal-card-tags">
      <span v-for="tag in card.features || []" :key="tag">{{ tag }}</span>
    </div>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  card: {
    type: Object,
    required: true,
  },
})

defineEmits(['select'])

const icon = computed(() => {
  const map = {
    blue: '儿童',
    pink: '家长',
    orange: '家长',
    green: '咨询',
    indigo: '管理',
  }
  return map[props.card.accent] || '入口'
})

const accentStyle = computed(() => {
  const map = {
    blue: 'border-top: 4px solid #39adff',
    pink: 'border-top: 4px solid #f58aa9',
    orange: 'border-top: 4px solid #ffb45c',
    green: 'border-top: 4px solid #53cd99',
    indigo: 'border-top: 4px solid #7e9bff',
  }
  return map[props.card.accent] || map.blue
})
</script>
