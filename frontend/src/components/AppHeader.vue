<script setup lang="ts">
import { Moon, Sun } from 'lucide-vue-next'
import { computed } from 'vue'

import { usePreferencesStore } from '@/stores/preferences'

const preferences = usePreferencesStore()

const isDark = computed(() => preferences.theme === 'dark')

function toggleTheme() {
  preferences.setTheme(isDark.value ? 'light' : 'dark')
}
</script>

<template>
  <header class="app-header">
    <RouterLink to="/" class="brand">Skill Finder</RouterLink>
    <button
      class="theme-toggle"
      type="button"
      :aria-label="isDark ? '切换到亮色主题' : '切换到暗色主题'"
      :title="isDark ? '切换到亮色主题' : '切换到暗色主题'"
      @click="toggleTheme"
    >
      <Sun v-if="isDark" :size="18" aria-hidden="true" />
      <Moon v-else :size="18" aria-hidden="true" />
    </button>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-4);
  height: 56px;
  background-color: var(--color-header);
  color: var(--color-header-text);
}

.brand {
  color: var(--color-header-text);
  font-weight: 600;
  text-decoration: none;
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--color-header-text);
}

.theme-toggle:hover {
  background-color: var(--color-canvas-subtle);
}
</style>
