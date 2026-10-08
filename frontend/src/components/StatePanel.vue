<script setup lang="ts">
import { AlertTriangle, Inbox, RotateCw } from 'lucide-vue-next'

defineProps<{
  variant: 'skeleton' | 'empty' | 'error'
  title: string
  message?: string
  actionLabel?: string
}>()

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <section
    v-if="variant === 'skeleton'"
    class="state-panel"
    data-testid="skeleton"
    aria-busy="true"
    aria-label="正在加载"
  >
    <div v-for="n in 5" :key="n" class="skeleton-row"></div>
  </section>

  <section
    v-else
    class="state-panel state-centered"
    :data-testid="`${variant}-state`"
  >
    <Inbox v-if="variant === 'empty'" :size="32" class="state-icon" aria-hidden="true" />
    <AlertTriangle v-else :size="32" class="state-icon" aria-hidden="true" />
    <h2 class="state-title">{{ title }}</h2>
    <p v-if="message" class="state-message">{{ message }}</p>
    <button
      v-if="variant === 'empty' || variant === 'error'"
      type="button"
      class="state-action"
      :data-testid="variant === 'empty' ? 'reset-filters' : 'retry'"
      @click="emit('action')"
    >
      <RotateCw :size="14" aria-hidden="true" />
      {{ actionLabel ?? (variant === 'empty' ? '清空筛选条件' : '重试') }}
    </button>
  </section>
</template>

<style scoped>
.state-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.state-centered {
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
  text-align: center;
  color: var(--color-text-secondary);
}

.state-icon {
  margin-bottom: var(--spacing-2);
  opacity: 0.7;
}

.state-title {
  font-size: 16px;
  font-weight: 600;
}

.state-message {
  font-size: 13px;
}

.state-action {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  margin-top: var(--spacing-3);
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  background-color: transparent;
  color: var(--color-accent);
  font-size: 13px;
}

.state-action:hover {
  background-color: var(--color-canvas);
}

.skeleton-row {
  height: 64px;
  border-radius: var(--radius-card);
  background-color: var(--color-skeleton);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}
</style>
