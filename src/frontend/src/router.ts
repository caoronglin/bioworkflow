import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/pipelines',
    name: 'Pipelines',
    component: () => import('@/pages/Pipelines.vue'),
    meta: { title: '流水线管理' },
  },
  {
    path: '/pipelines/:id',
    name: 'PipelineDetail',
    component: () => import('@/pages/PipelineDetail.vue'),
    meta: { title: '流水线详情' },
  },
  {
    path: '/conda',
    name: 'CondaManager',
    component: () => import('@/pages/CondaManager.vue'),
    meta: { title: 'Conda 环境管理' },
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/pages/Knowledge.vue'),
    meta: { title: '知识库' },
  },
  {
    path: '/mcp',
    name: 'MCPServices',
    component: () => import('@/pages/MCPServices.vue'),
    meta: { title: 'MCP 服务' },
  },
  {
    path: '/notebook',
    name: 'Notebook',
    component: () => import('@/pages/Notebook.vue'),
    meta: { title: 'Notebook' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/pages/Settings.vue'),
    meta: { title: '设置' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫 - 未登录时重定向到登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (!to.meta?.noAuth && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
