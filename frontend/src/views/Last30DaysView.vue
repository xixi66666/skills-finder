<template>
  <main class="last30days-view">
    <header class="page-header">
      <div>
        <p class="eyebrow">MULTI-SOURCE RESEARCH</p>
        <h1>近 30 天研究</h1>
        <p class="page-description">
          聚合社区讨论、开发者动态、预测市场与网页信息，查看最近一个月人们真正关注的内容。
        </p>
      </div>
      <div class="engine-state" :class="`state-${engineStatus}`" role="status">
        <Activity :size="16" aria-hidden="true" />
        <span>{{ engineStatusLabel }}</span>
      </div>
    </header>

    <section class="research-panel" aria-labelledby="research-form-title">
      <h2 id="research-form-title">研究主题</h2>
      <form class="query-form" @submit.prevent="onSubmit">
        <label class="sr-only" for="research-query">研究主题</label>
        <div class="query-control">
          <Search :size="18" class="query-icon" aria-hidden="true" />
          <input
            id="research-query"
            v-model="query"
            type="search"
            required
            maxlength="200"
            autocomplete="off"
            placeholder="例如：AI 编程助手最近有哪些真实反馈？"
            :disabled="loading"
          />
        </div>
        <button type="submit" :disabled="loading || !query.trim()">
          <LoaderCircle v-if="loading" :size="18" class="spinner" aria-hidden="true" />
          <Search v-else :size="18" aria-hidden="true" />
          {{ loading ? '正在研究…' : '研究最近 30 天' }}
        </button>
      </form>

      <div v-if="availableSources.length" class="source-list" aria-label="可用数据来源">
        <span class="source-list-label">当前可用</span>
        <span v-for="source in availableSources" :key="source" class="source-chip">
          {{ sourceLabel(source) }}
        </span>
      </div>
      <p v-if="engineMessage" class="setup-message">{{ engineMessage }}</p>
    </section>

    <div v-if="error" class="notice notice-error" role="alert">
      <CircleAlert :size="18" aria-hidden="true" />
      <span>{{ error }}</span>
    </div>

    <div v-if="loading" class="loading-state" role="status">
      <LoaderCircle :size="28" class="spinner" aria-hidden="true" />
      <div>
        <strong>正在运行真实的 last30days 多源研究</strong>
        <p>不同来源响应时间不同，完整结果可能需要几分钟。</p>
      </div>
    </div>

    <template v-else-if="hasRun">
      <div class="result-summary">
        <div>
          <p class="eyebrow">RESEARCH RESULT</p>
          <h2>{{ resultQuery }}</h2>
        </div>
        <div class="summary-meta">
          <span>{{ items.length }} 条结果</span>
          <span>{{ clusters.length }} 个主题</span>
          <span v-if="fetchedAt"><Clock :size="14" aria-hidden="true" />{{ formatDate(fetchedAt) }}</span>
        </div>
      </div>

      <div v-if="sourceStatus === 'partial' || message" class="notice" role="status">
        <CircleAlert :size="18" aria-hidden="true" />
        <span>{{ message || '部分来源暂时不可用，以下是已获取的结果。' }}</span>
      </div>

      <section v-if="clusters.length" class="clusters-section" aria-labelledby="clusters-title">
        <h2 id="clusters-title">讨论焦点</h2>
        <div class="cluster-grid">
          <article v-for="cluster in clusters" :key="cluster.title" class="cluster-card">
            <h3>{{ cluster.title }}</h3>
            <p>{{ cluster.summary }}</p>
            <div class="cluster-footer">
              <span>{{ cluster.sources.map(sourceLabel).join(' · ') }}</span>
              <span>{{ formatNumber(cluster.engagement_total) }} 互动</span>
            </div>
          </article>
        </div>
      </section>

      <section v-if="items.length" class="results-section" aria-labelledby="results-title">
        <h2 id="results-title">原始信号与摘要</h2>
        <ol class="results-list">
          <li v-for="item in items" :key="item.candidate_id" class="result-item">
            <article>
              <div class="result-source-row">
                <span class="source-chip">{{ sourceLabel(item.source) }}</span>
                <span v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
                <span v-if="item.relevance_score != null">
                  相关度 {{ Math.round(item.relevance_score * 100) }}%
                </span>
              </div>
              <h3>
                <a :href="item.url" target="_blank" rel="noopener noreferrer">
                  {{ item.title }}
                  <ExternalLink :size="15" aria-hidden="true" />
                </a>
              </h3>
              <p v-if="item.summary" class="result-summary-text">{{ item.summary }}</p>
              <div v-if="engagementTotal(item.engagement)" class="engagement">
                <MessageCircle :size="15" aria-hidden="true" />
                {{ formatNumber(engagementTotal(item.engagement)) }} 互动
              </div>
            </article>
          </li>
        </ol>
      </section>

      <div v-else class="empty-state">
        <SearchX :size="32" aria-hidden="true" />
        <h2>最近 30 天没有找到相关结果</h2>
        <p>尝试更换更具体的主题或产品名称。</p>
      </div>
    </template>
  </main>
</template>

<script setup lang="ts">
import {
  Activity,
  CircleAlert,
  Clock,
  ExternalLink,
  LoaderCircle,
  MessageCircle,
  Search,
  SearchX,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'

import { fetchLast30daysStatus, postLast30days } from '@/api/last30days'
import type {
  Last30DaysCluster,
  Last30DaysItem,
  Last30DaysStatus,
} from '@/api/last30days'

const SOURCE_LABELS: Record<string, string> = {
  github: 'GitHub',
  grounding: 'Web',
  hackernews: 'Hacker News',
  polymarket: 'Polymarket',
  reddit: 'Reddit',
  tiktok: 'TikTok',
  x: 'X',
  youtube: 'YouTube',
}

const query = ref('')
const loading = ref(false)
const error = ref('')
const engineStatus = ref<Last30DaysStatus>('working')
const engineMessage = ref('')
const sourceStatus = ref<Last30DaysStatus>('working')
const message = ref('')
const availableSources = ref<string[]>([])
const items = ref<Last30DaysItem[]>([])
const clusters = ref<Last30DaysCluster[]>([])
const resultQuery = ref('')
const fetchedAt = ref('')
const hasRun = ref(false)

const engineStatusLabel = computed(() => {
  if (engineStatus.value === 'unconfigured') return '需要配置'
  if (engineStatus.value === 'error') return '诊断失败'
  if (engineStatus.value === 'skipped') return '模块已停用'
  return '多源引擎就绪'
})

onMounted(async () => {
  try {
    const response = await fetchLast30daysStatus()
    engineStatus.value = response.status
    availableSources.value = response.sources
    engineMessage.value = response.message ?? ''
  } catch {
    engineStatus.value = 'error'
    engineMessage.value = '暂时无法读取 last30days 引擎状态。'
  }
})

async function onSubmit(): Promise<void> {
  const cleanQuery = query.value.trim()
  if (!cleanQuery) return
  loading.value = true
  error.value = ''
  message.value = ''
  hasRun.value = false
  items.value = []
  clusters.value = []
  try {
    const response = await postLast30days(cleanQuery)
    sourceStatus.value = response.status
    message.value = response.message ?? ''
    items.value = response.items
    clusters.value = response.clusters
    resultQuery.value = response.query || cleanQuery
    fetchedAt.value = response.fetched_at
    availableSources.value = response.sources.length ? response.sources : availableSources.value
    hasRun.value = true
    if (response.status === 'error' || response.status === 'unconfigured') {
      error.value = response.message || '研究任务没有成功完成。'
    }
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : '研究请求失败，请稍后重试。'
    sourceStatus.value = 'error'
  } finally {
    loading.value = false
  }
}

function sourceLabel(source: string): string {
  return SOURCE_LABELS[source.toLowerCase()] ?? source
}

function engagementTotal(engagement: Record<string, unknown>): number {
  return Object.values(engagement).reduce<number>((total, value) => {
    return typeof value === 'number' && Number.isFinite(value) ? total + value : total
  }, 0)
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('zh-CN', { notation: 'compact' }).format(value)
}

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('zh-CN', { month: 'short', day: 'numeric' }).format(date)
}
</script>

<style scoped>
.last30days-view {
  width: min(1040px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 64px;
  color: var(--color-text-primary);
}

.page-header,
.result-summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-6);
}

.page-header h1,
.result-summary h2 {
  margin: var(--spacing-1) 0 var(--spacing-2);
  line-height: 1.2;
}

.page-header h1 {
  font-size: clamp(28px, 4vw, 40px);
}

.eyebrow {
  margin: 0;
  color: var(--color-accent);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.page-description {
  max-width: 680px;
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.engine-state {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-success);
  font-size: 13px;
  font-weight: 600;
}

.engine-state.state-error,
.engine-state.state-unconfigured {
  color: var(--color-danger);
}

.research-panel {
  margin-top: 32px;
  padding: var(--spacing-6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-bg);
  box-shadow: 0 8px 24px var(--color-shadow);
}

.research-panel h2,
.clusters-section > h2,
.results-section > h2 {
  margin: 0 0 var(--spacing-3);
  font-size: 16px;
}

.query-form {
  display: flex;
  gap: var(--spacing-3);
}

.query-control {
  position: relative;
  flex: 1;
}

.query-icon {
  position: absolute;
  top: 50%;
  left: 14px;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
}

.query-control input {
  width: 100%;
  min-height: 46px;
  padding: 0 14px 0 42px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  background: var(--color-canvas);
  color: var(--color-text-primary);
  font: inherit;
}

.query-control input:focus {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 1px;
}

.query-form button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  min-height: 46px;
  padding: 0 var(--spacing-4);
  border: 1px solid var(--color-accent-emphasis);
  border-radius: var(--radius-button);
  background: var(--color-accent-emphasis);
  color: var(--color-header-text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.query-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
}

.source-list-label,
.setup-message,
.summary-meta,
.result-source-row,
.engagement {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.source-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px var(--spacing-2);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-canvas);
  color: var(--color-text-primary);
  font-size: 12px;
  font-weight: 600;
}

.setup-message {
  margin: var(--spacing-3) 0 0;
  color: var(--color-danger);
}

.notice,
.loading-state {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
  padding: var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-canvas);
}

.notice-error {
  color: var(--color-danger);
}

.loading-state strong {
  display: block;
  margin-bottom: var(--spacing-1);
}

.loading-state p {
  margin: 0;
  color: var(--color-text-secondary);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.result-summary {
  margin-top: 40px;
  padding-bottom: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
}

.summary-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--spacing-3);
}

.summary-meta span {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
}

.clusters-section,
.results-section {
  margin-top: 32px;
}

.cluster-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-3);
}

.cluster-card {
  padding: var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-bg);
}

.cluster-card h3 {
  margin: 0 0 var(--spacing-2);
  font-size: 15px;
}

.cluster-card p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.cluster-footer {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
  color: var(--color-text-muted);
  font-size: 12px;
}

.results-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.result-item {
  padding: var(--spacing-4) 0;
  border-top: 1px solid var(--color-border);
}

.result-item:first-child {
  border-top: 0;
}

.result-source-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-3);
}

.result-item h3 {
  margin: var(--spacing-2) 0;
  font-size: 18px;
}

.result-item h3 a {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--color-accent);
  text-decoration: none;
}

.result-item h3 a:hover {
  text-decoration: underline;
}

.result-summary-text {
  max-width: 800px;
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.65;
}

.engagement {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  margin-top: var(--spacing-2);
}

.empty-state {
  display: grid;
  justify-items: center;
  margin-top: 40px;
  padding: 48px var(--spacing-4);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-card);
  color: var(--color-text-secondary);
  text-align: center;
}

.empty-state h2 {
  margin: var(--spacing-3) 0 var(--spacing-1);
  color: var(--color-text-primary);
  font-size: 18px;
}

.empty-state p {
  margin: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 720px) {
  .last30days-view {
    width: min(100% - 24px, 1040px);
    padding-top: 28px;
  }

  .page-header,
  .result-summary,
  .query-form {
    flex-direction: column;
  }

  .engine-state,
  .query-control,
  .query-form button {
    width: 100%;
  }

  .engine-state {
    box-sizing: border-box;
    justify-content: center;
  }

  .summary-meta {
    justify-content: flex-start;
  }
}
</style>
