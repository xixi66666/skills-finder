<script setup lang="ts">
import { ExternalLink } from 'lucide-vue-next'

import SparklineChart from '@/components/SparklineChart.vue'
import type { RepositoryListItem as Repo } from '@/types/api'

defineProps<{
  repo: Repo
}>()

const CATEGORY_COLORS: Record<string, string> = {
  AGENT: 'var(--color-accent)',
  SKILL: 'var(--color-success)',
  MCP: 'var(--color-danger)',
}

const LANGUAGE_COLORS: Record<string, string> = {
  Python: 'var(--lang-python)',
  TypeScript: 'var(--lang-typescript)',
  JavaScript: 'var(--lang-javascript)',
  Go: 'var(--lang-go)',
  Rust: 'var(--lang-rust)',
}

function languageColor(language: string | null): string {
  if (!language) return 'var(--lang-default)'
  return LANGUAGE_COLORS[language] ?? 'var(--lang-default)'
}

function formatStars(value: number): string {
  return value.toLocaleString('en-US')
}

function formatGrowth(value: number | null): string {
  return value == null ? '--' : formatSigned(value)
}

function formatSigned(value: number): string {
  return value > 0 ? `+${value.toLocaleString('en-US')}` : value.toLocaleString('en-US')
}

function categoryColor(category: string): string {
  return CATEGORY_COLORS[category] ?? 'var(--color-text-secondary)'
}
</script>

<template>
  <article class="repo-item" data-testid="repo-item">
    <div class="repo-main">
      <div class="repo-title-row">
        <RouterLink
          :to="`/repositories/${encodeURIComponent(repo.owner)}/${encodeURIComponent(repo.name)}`"
          class="repo-name"
          :data-testid="`repo-link-${repo.name}`"
        >
          {{ repo.owner }}/{{ repo.name }}
        </RouterLink>
        <span
          v-for="cat in repo.categories"
          :key="cat"
          class="repo-category"
          :style="{ color: categoryColor(cat) }"
        >
          {{ cat }}
        </span>
      </div>
      <p class="repo-description">{{ repo.description }}</p>
      <div class="repo-meta">
        <span
          v-for="topic in repo.topics.slice(0, 4)"
          :key="topic"
          class="repo-topic"
          data-testid="topic"
        >
          {{ topic }}
        </span>
        <span class="repo-language" data-testid="language">
          <span class="language-dot" :style="{ backgroundColor: languageColor(repo.language) }"></span>
          {{ repo.language }}
        </span>
        <span class="repo-stars">{{ formatStars(repo.stars_count) }} stars</span>
      </div>
    </div>
    <div class="repo-growth">
      <div class="growth-metric">
        <span class="growth-label">今日</span>
        <span class="growth-value">{{ formatGrowth(repo.daily_stars) }}</span>
      </div>
      <div class="growth-metric">
        <span class="growth-label">7 日</span>
        <span class="growth-value">{{ formatGrowth(repo.weekly_stars) }}</span>
      </div>
      <SparklineChart :points="repo.trend" />
      <a
        :href="repo.html_url"
        class="repo-external"
        target="_blank"
        rel="noopener noreferrer"
        :aria-label="`在 GitHub 上打开 ${repo.owner}/${repo.name}`"
        data-testid="external-link"
      >
        <ExternalLink :size="16" aria-hidden="true" />
      </a>
    </div>
  </article>
</template>

<style scoped>
.repo-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding: var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background-color: var(--color-bg);
}

.repo-item:hover {
  border-color: var(--color-accent);
}

.repo-main {
  flex: 1;
  min-width: 0;
}

.repo-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.repo-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.repo-name:hover {
  color: var(--color-accent);
  text-decoration: none;
}

.repo-category {
  padding: 1px 8px;
  border: 1px solid currentColor;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
}

.repo-description {
  margin-top: var(--spacing-1);
  font-size: 13px;
  color: var(--color-text-secondary);
  word-break: break-word;
}

.repo-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-3);
  margin-top: var(--spacing-3);
}

.repo-topic {
  padding: 2px 8px;
  border-radius: 100px;
  background-color: var(--color-canvas);
  color: var(--color-accent);
  font-size: 11px;
}

.repo-language {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.language-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.repo-stars {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.repo-growth {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  flex-shrink: 0;
}

.growth-metric {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 44px;
}

.growth-label {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.growth-value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
}

.repo-external {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-button);
  color: var(--color-text-secondary);
}

.repo-external:hover {
  color: var(--color-accent);
  background-color: var(--color-canvas);
}
</style>
