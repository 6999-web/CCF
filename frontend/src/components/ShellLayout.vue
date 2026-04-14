<template>
  <div class="shell-frame" :class="`shell-${roleKey || 'child'}`">
    <aside class="shell-sidebar">
      <div class="shell-brand">
        <div class="shell-brand-mark">悦</div>
        <div>
          <div class="shell-brand-title">悦读相伴</div>
          <div class="shell-brand-copy">阅读成长 · 训练支持 · 家校协同</div>
        </div>
      </div>

      <div class="shell-rail-copy">
        <div class="shell-rail-kicker">Workspace</div>
        <h2>{{ title }}</h2>
        <p>{{ subtitle }}</p>
      </div>

      <nav class="shell-nav">
        <button
          v-for="item in menu"
          :key="item.key"
          class="shell-nav-item"
          :class="{ active: item.key === activeKey }"
          @click="$emit('change-tab', item.key)"
        >
          <span class="shell-nav-dot"></span>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="shell-user-card">
        <div class="shell-user-meta">
          <span class="shell-user-avatar">{{ (user?.display_name || '悦').slice(0, 1) }}</span>
          <div>
            <div class="shell-user-name">{{ user?.display_name || '当前访客' }}</div>
            <div class="shell-user-org">{{ user?.organization || subtitle }}</div>
          </div>
        </div>
      </div>
    </aside>

    <main class="shell-main">
      <header class="shell-header">
        <div>
          <div class="shell-header-kicker">Portal</div>
          <h1 class="shell-header-title">{{ title }}</h1>
        </div>
        <div class="shell-header-actions">
          <slot name="header-actions" />
        </div>
      </header>

      <section class="shell-body">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String,
  roleKey: String,
  menu: {
    type: Array,
    default: () => [],
  },
  activeKey: String,
  user: Object,
})

defineEmits(['change-tab'])
</script>
