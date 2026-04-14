<template>
  <router-view />
  <DigitalCompanion v-if="showCompanion" />
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { useRoute } from 'vue-router'

const DigitalCompanion = defineAsyncComponent(() => import('./components/DigitalCompanion.vue'))

const route = useRoute()
const showCompanion = computed(() => route.path.startsWith('/portal'))
</script>
