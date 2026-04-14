<template>
  <div class="metric-card">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">{{ value }}</div>
    <div class="metric-note">{{ note }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  note: String,
})
</script>
