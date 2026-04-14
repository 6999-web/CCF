<template>
  <section class="panel-card" :class="variant">
    <div v-if="title" class="panel-card-header">
      <h3>{{ title }}</h3>
      <slot name="header-extra" />
    </div>
    <div class="panel-card-body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: String,
  variant: {
    type: String,
    default: 'default',
  },
})
</script>
