<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import FilterSidebar from '@/components/FilterSidebar.vue'
import RepositoryListItem from '@/components/RepositoryListItem.vue'
import StatePanel from '@/components/StatePanel.vue'
import { fetchLanguages, fetchRepositories, fetchStats } from '@/api/repositories'
import type { Category, LanguageStat, RepositoryListResponse, RepositoryQuery, SortKey } from '@/types/api'

const route = useRoute()
const router = useRouter()

const items = ref<RepositoryListResponse['items']>([])
const total = ref(0)
const loading = ref(false)
const initialLoading = ref(true)
const error = ref(false)
const lastCollectionAt = ref<string | null>(null)
const stats = ref<{ total_repositories: number }>({ total_repositories: 0 })
const languages = ref<LanguageStat[]>([])
const page = ref(1)
const filtersVisible = ref(false)

const filters = reactive({
  sort: 'daily_stars' as SortKey,
  category: '' as Category | '',
  language: '',
  minStars: null as number | null,
  q: '',
})

const pageSize = 20

function queryFromRoute(): Partial<RepositoryQuery> {
  const params = route.query
  return {
    sort: (params.sort as SortKey) || 'daily_stars',
    category: ((params.category as string) || '') as Category | '',
    language: (params.language as string) || '',
    min_stars: params.min_stars ? Number(params.min_stars) : null,
    q: (params.q as string) || '',
  }
}

function writeFiltersToUrl() {
  const query: Record<string, string> = {}
  if (filters.sort !== 'daily_stars') query.sort = filters.sort
  if (filters.category) query.category = filters.category
  if (filters.language) query.language = filters.language
  if (filters.minStars != null) query.min_stars = String(filters.minStars)
  if (filters.q) query.q = filters.q
  router.replace({ query })
}

async function loadRepositories() {
  loading.value = true
  error.value = false
  try {
    const params: RepositoryQuery = {
      page: page.value,
      page_size: pageSize,
      sort: filters.sort,
      category: filters.category || undefined,
      language: filters.language || undefined,
      min_stars: filters.minStars ?? undefined,
      q: filters.q || undefined,
    }
    const data = await fetchRepositories(params)
    items.value = data.items
    total.value = data.total
    lastCollectionAt.value = data.last_successful_collection_at
  } catch {
    error.value = true
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

function onSortChange(sort: SortKey) {
  if (filters.sort === sort) return
  filters.sort = sort
  page.value = 1
  writeFiltersToUrl()
  void loadRepositories()
}

function updateFilters(partial: Partial<typeof filters>) {
  Object.assign(filters, partial)
  page.value = 1
  writeFiltersToUrl()
  void loadRepositories()
}

function resetFilters() {
  updateFilters({ category: '', language: '', minStars: null, q: '' })
}

function goToPage(next: number) {
  page.value = next
  writeFiltersToUrl()
  void loadRepositories()
}

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize))

function applyRouteFilters() {
  const fromRoute = queryFromRoute()
  const { min_stars: minStars, ...rest } = fromRoute
  Object.assign(filters, rest, { minStars: minStars ?? null })
}

watch(
  () => route.query,
  () => {
    applyRouteFilters()
    void loadRepositories()
  },
)

onMounted(async () => {
  applyRouteFilters()
  void loadRepositories()
  const [langs, statsData] = await Promise.all([fetchLanguages(), fetchStats()])
  languages.value = langs
  stats.value = statsData
  document.addEventListener('keydown', onKeydown)
})

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && filtersVisible.value) {
    filtersVisible.value = false
    const trigger = document.querySelector<HTMLButtonElement>('[data-testid="open-filters"]')
    trigger?.focus()
  }
}

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="home-layout">
    <div v-if="filtersVisible" class="drawer-backdrop" data-testid="drawer-backdrop" @click="filtersVisible = false"></div>
    <aside
      class="filter-drawer"
      :class="{ open: filtersVisible }"
      aria-hidden="false"
    >
      <FilterSidebar
        :model-value="{ category: filters.category, language: filters.language, minStars: filters.minStars }"
        :languages="languages"
        @update:model-value="
          (value) =>
            updateFilters({ category: value.category, language: value.language, minStars: value.minStars })
        "
        @close="filtersVisible = false"
      />
    </aside>
    <div class="home-content">
      <header class="home-header">
        <div class="header-stats">
          <button
            type="button"
            class="mobile-filter-button"
            data-testid="open-filters"
            @click="filtersVisible = true"
          >
            筛选
          </button>
          <span>{{ stats.total_repositories }} 个仓库</span>
          <span v-if="lastCollectionAt" class="header-muted">
            最近更新：{{ lastCollectionAt }}
          </span>
        </div>
        <div class="sort-tabs" role="tablist" aria-label="排序方式">
          <button
            v-for="tab in [
              { key: 'daily_stars', label: '今日增长' },
              { key: 'weekly_stars', label: '7 日增长' },
              { key: 'total_stars', label: '总 Star' },
            ]"
            :key="tab.key"
            type="button"
            role="tab"
            class="sort-tab"
            :class="{ active: filters.sort === tab.key }"
            :aria-selected="filters.sort === tab.key"
            :data-testid="`sort-${tab.key}`"
            @click="onSortChange(tab.key as SortKey)"
          >
            {{ tab.label }}
          </button>
        </div>
      </header>

      <StatePanel v-if="initialLoading" variant="skeleton" title="加载中" />

      <StatePanel
        v-else-if="error"
        variant="error"
        title="加载失败"
        message="无法获取仓库数据，请检查网络后重试。"
        @action="loadRepositories"
      />

      <StatePanel
        v-else-if="items.length === 0"
        variant="empty"
        title="没有匹配的仓库"
        message="试试调整筛选条件或清空搜索。"
        @action="resetFilters"
      />

      <template v-else>
        <div class="repo-list" role="list">
          <RepositoryListItem v-for="repo in items" :key="repo.id" :repo="repo" />
        </div>
        <nav v-if="totalPages() > 1" class="pagination" aria-label="分页">
          <button
            type="button"
            class="page-button"
            :disabled="page <= 1"
            :aria-label="'上一页'"
            @click="goToPage(page - 1)"
          >
            上一页
          </button>
          <span class="page-info">第 {{ page }} / {{ totalPages() }} 页</span>
          <button
            type="button"
            class="page-button"
            :disabled="page >= totalPages()"
            :aria-label="'下一页'"
            @click="goToPage(page + 1)"
          >
            下一页
          </button>
        </nav>
      </template>
    </div>
  </div>
</template>

<style scoped>
.home-layout {
  display: flex;
  gap: var(--spacing-6);
}

.home-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.filter-drawer {
  width: 220px;
  flex-shrink: 0;
}

.drawer-backdrop {
  display: none;
}

.mobile-filter-button {
  display: none;
}

.home-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .home-layout {
    display: block;
  }

  .filter-drawer {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 40;
    width: 280px;
    max-width: 85vw;
    padding: var(--spacing-4);
    background-color: var(--color-bg);
    border-right: 1px solid var(--color-border);
    box-shadow: var(--color-shadow);
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    overflow-y: auto;
  }

  .filter-drawer.open {
    transform: translateX(0);
  }

  .drawer-backdrop {
    position: fixed;
    inset: 0;
    z-index: 39;
    display: block;
    background-color: rgba(0, 0, 0, 0.5);
  }

  .mobile-filter-button {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-button);
    background-color: transparent;
    color: var(--color-accent);
    font-size: 13px;
  }
}

.header-muted {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-secondary);
}

.sort-tabs {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  overflow: hidden;
  width: fit-content;
}

.sort-tab {
  padding: 6px 14px;
  border: 0;
  background-color: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.sort-tab:hover {
  background-color: var(--color-canvas);
}

.sort-tab.active {
  background-color: var(--color-accent-emphasis);
  color: #ffffff;
}

.repo-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-4);
  padding: var(--spacing-4) 0;
}

.page-button {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  background-color: transparent;
  color: var(--color-accent);
  font-size: 13px;
}

.page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
