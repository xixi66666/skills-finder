<script setup lang="ts">
import { onMounted } from 'vue'

import AppHeader from '@/components/AppHeader.vue'
import { usePreferencesStore } from '@/stores/preferences'

const preferences = usePreferencesStore()

onMounted(() => {
  document.documentElement.setAttribute('data-theme', preferences.theme)
})
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg);
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: var(--spacing-4);
}
</style>
