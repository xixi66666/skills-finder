<template>
  <div class="last30days-view">
    <h1>Last 30 Days – Hacker News</h1>
    <form class="query-form" @submit.prevent="onSubmit">
      <input
        v-model="query"
        type="text"
        placeholder="Search Hacker News (optional)"
        class="query-input"
      />
      <button type="submit" :disabled="loading" class="submit-btn">
        {{ loading ? 'Searching…' : 'Search' }}
      </button>
    </form>

    <div v-if="sourceStatus" class="source-status" :class="sourceStatus">
      Source: {{ sourceStatus }}<span v-if="message"> – {{ message }}</span>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <ul v-if="items.length" class="results-list">
      <li v-for="item in items" :key="item.object_id" class="result-item">
        <a :href="item.citation_url" target="_blank" rel="noopener" class="result-title">
          {{ item.title || '(no title)' }}
        </a>
        <div class="result-meta">
          <span v-if="item.author">by {{ item.author }}</span>
          <span v-if="item.points != null">▲ {{ item.points }}</span>
          <span v-if="item.num_comments != null">💬 {{ item.num_comments }}</span>
          <span v-if="item.created_at">{{ item.created_at }}</span>
        </div>
        <p v-if="item.story_text" class="result-text">{{ item.story_text }}</p>
      </li>
    </ul>

    <p v-else-if="!loading && sourceStatus === 'working'" class="no-results">
      No results found.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { postLast30days } from '@/api/last30days'
import type { Last30DaysItem } from '@/api/last30days'

const query = ref('')
const loading = ref(false)
const error = ref('')
const sourceStatus = ref('')
const message = ref('')
const items = ref<Last30DaysItem[]>([])

async function onSubmit(): Promise<void> {
  loading.value = true
  error.value = ''
  sourceStatus.value = ''
  message.value = ''
  items.value = []
  try {
    const res = await postLast30days(query.value || undefined)
    sourceStatus.value = res.status
    message.value = res.message ?? ''
    items.value = res.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Request failed'
    sourceStatus.value = 'error'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.last30days-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 1.5rem;
}
.query-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.query-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ccc);
  border-radius: 4px;
}
.submit-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background: var(--color-primary, #4a90d9);
  color: #fff;
  cursor: pointer;
}
.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.source-status {
  padding: 0.4rem 0.6rem;
  margin-bottom: 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
  background: #eef;
}
.source-status.error {
  background: #fee;
  color: #900;
}
.source-status.no-results {
  background: #ffe;
}
.error-message {
  color: #c00;
  margin-bottom: 0.75rem;
}
.results-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.result-item {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border, #eee);
}
.result-title {
  font-weight: 600;
  color: var(--color-primary, #4a90d9);
  text-decoration: none;
}
.result-title:hover {
  text-decoration: underline;
}
.result-meta {
  font-size: 0.8rem;
  color: #666;
  margin-top: 0.25rem;
  display: flex;
  gap: 0.75rem;
}
.result-text {
  margin-top: 0.4rem;
  font-size: 0.85rem;
  color: #444;
  white-space: pre-wrap;
}
.no-results {
  color: #888;
}
</style>
