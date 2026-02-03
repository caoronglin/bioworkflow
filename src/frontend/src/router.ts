import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/pipelines',
    component: () => import('@/pages/Pipelines.vue'),
    meta: { title: '流水线管理' },
  },
  {
    path: '/pipelines/:id',
    component: () => import('@/pages/PipelineDetail.vue'),
    meta: { title: '流水线详情' },
  },
  {
    path: '/conda',
    component: () => import('@/pages/CondaManager.vue'),
    meta: { title: 'Conda 环境管理' },
  },
  {
    path: '/knowledge',
    component: () => import('@/pages/Knowledge.vue'),
    meta: { title: '知识库' },
  },
  {
    path: '/mcp',
    component: () => import('@/pages/MCPServices.vue'),
    meta: { title: 'MCP 服务' },
  },
  {
    path: '/settings',
    component: () => import('@/pages/Settings.vue'),
    meta: { title: '设置' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
