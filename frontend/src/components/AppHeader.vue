<script setup lang="ts">
import { Moon, Search, Sun } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { usePreferencesStore } from '@/stores/preferences'

const preferences = usePreferencesStore()
const route = useRoute()
const router = useRouter()

const isDark = computed(() => preferences.theme === 'dark')
const searchText = ref(typeof route.query.q === 'string' ? route.query.q : '')

let searchTimer: ReturnType<typeof setTimeout> | null = null

function toggleTheme() {
  preferences.setTheme(isDark.value ? 'light' : 'dark')
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    const query = { ...route.query }
    if (searchText.value) {
      query.q = searchText.value
    } else {
      delete query.q
    }
    if (route.name !== 'home') {
      void router.push({ name: 'home', query })
    } else {
      void router.replace({ query })
    }
  }, 300)
}
</script>

<template>
  <header class="app-header">
    <RouterLink to="/" class="brand">Skill Finder</RouterLink>
    <div class="search-box">
      <Search :size="16" class="search-icon" aria-hidden="true" />
      <input
        v-model="searchText"
        type="search"
        class="search-input"
        placeholder="搜索仓库"
        aria-label="搜索仓库"
        data-testid="global-search"
        @input="onSearchInput"
      />
    </div>
    <button
      class="theme-toggle"
      type="button"
      :aria-label="isDark ? '切换到亮色主题' : '切换到暗色主题'"
      :title="isDark ? '切换到亮色主题' : '切换到暗色主题'"
      data-testid="theme-toggle"
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
  gap: var(--spacing-4);
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

.search-box {
  position: relative;
  flex: 1;
  max-width: 480px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
}

.search-input {
  width: 100%;
  padding: 6px 12px 6px 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  background-color: var(--color-canvas);
  color: var(--color-text-primary);
  font-size: 13px;
}

.search-input::placeholder {
  color: var(--color-text-secondary);
}

.search-input:focus {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 0;
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-left: auto;
  border: 0;
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--color-header-text);
}

.theme-toggle:hover {
  background-color: var(--color-canvas-subtle);
}
</style>
