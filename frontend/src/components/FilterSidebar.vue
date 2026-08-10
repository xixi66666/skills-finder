<script setup lang="ts">
import { X } from 'lucide-vue-next'
import { computed } from 'vue'

import type { Category, LanguageStat } from '@/types/api'

const props = defineProps<{
  modelValue: {
    category: Category | ''
    language: string
    minStars: number | null
  }
  languages: LanguageStat[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: { category: Category | ''; language: string; minStars: number | null }]
  close: []
}>()

const categories: { value: Category | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'AGENT', label: 'Agent' },
  { value: 'SKILL', label: 'Skill' },
  { value: 'MCP', label: 'MCP' },
]

const minStarOptions = [
  { value: null, label: '不限' },
  { value: 1000, label: '≥ 1,000' },
  { value: 5000, label: '≥ 5,000' },
  { value: 10000, label: '≥ 10,000' },
]

const hasActive = computed(
  () => props.modelValue.category !== '' || props.modelValue.language !== '' || props.modelValue.minStars != null,
)

function updateCategory(value: Category | '') {
  emit('update:modelValue', { ...props.modelValue, category: value })
}

function updateLanguage(value: string) {
  emit('update:modelValue', { ...props.modelValue, language: value })
}

function updateMinStars(value: number | null) {
  emit('update:modelValue', { ...props.modelValue, minStars: value })
}

function clearAll() {
  emit('update:modelValue', { category: '', language: '', minStars: null })
}
</script>

<template>
  <aside class="filter-sidebar" aria-label="筛选条件">
    <div class="filter-header">
      <h2 class="filter-title">筛选</h2>
      <button
        type="button"
        class="filter-close"
        aria-label="关闭筛选"
        data-testid="close-filters"
        @click="emit('close')"
      >
        <X :size="16" aria-hidden="true" />
      </button>
    </div>

    <div class="filter-group">
      <h3 class="filter-label">分类</h3>
      <div class="filter-options" role="group" aria-label="分类筛选">
        <button
          v-for="cat in categories"
          :key="cat.value"
          type="button"
          class="filter-option"
          :class="{ active: modelValue.category === cat.value }"
          :aria-pressed="modelValue.category === cat.value"
          :data-testid="cat.value === '' ? 'category-all' : `category-${cat.value.toLowerCase()}`"
          @click="updateCategory(cat.value)"
        >
          {{ cat.label }}
        </button>
      </div>
    </div>

    <div class="filter-group">
      <h3 class="filter-label">语言</h3>
      <select
        class="filter-select"
        :value="modelValue.language"
        aria-label="按语言筛选"
        data-testid="language-select"
        @change="updateLanguage(($event.target as HTMLSelectElement).value)"
      >
        <option value="">全部语言</option>
        <option v-for="lang in languages" :key="lang.language" :value="lang.language">
          {{ lang.language }} ({{ lang.count }})
        </option>
      </select>
    </div>

    <div class="filter-group">
      <h3 class="filter-label">最低 Star</h3>
      <select
        class="filter-select"
        :value="String(modelValue.minStars ?? '')"
        aria-label="按最低 Star 筛选"
        data-testid="min-stars-select"
        @change="
          updateMinStars(
            ($event.target as HTMLSelectElement).value === ''
              ? null
              : Number(($event.target as HTMLSelectElement).value),
          )
        "
      >
        <option v-for="opt in minStarOptions" :key="String(opt.value)" :value="String(opt.value ?? '')">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <button
      v-if="hasActive"
      type="button"
      class="filter-reset"
      data-testid="clear-filters"
      @click="clearAll"
    >
      清除筛选
    </button>
  </aside>
</template>

<style scoped>
.filter-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  width: 220px;
  flex-shrink: 0;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-title {
  font-size: 14px;
  font-weight: 600;
}

.filter-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--color-text-secondary);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

.filter-option {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 100px;
  background-color: transparent;
  color: var(--color-text-primary);
  font-size: 12px;
}

.filter-option:hover {
  border-color: var(--color-accent);
}

.filter-option.active {
  border-color: var(--color-accent);
  background-color: var(--color-accent-emphasis);
  color: #ffffff;
}

.filter-select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  background-color: var(--color-bg);
  color: var(--color-text-primary);
  font-size: 13px;
}

.filter-reset {
  align-self: flex-start;
  padding: 4px 8px;
  border: 0;
  background: transparent;
  color: var(--color-accent);
  font-size: 13px;
}
</style>
