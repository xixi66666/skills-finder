import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'
import RepositoryDetailView from '@/views/RepositoryDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/repositories/:owner/:name', name: 'repository-detail', component: RepositoryDetailView },
  ],
})

export default router
