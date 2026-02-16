import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

interface User {
  id: string
  username: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
}

interface VisitedView {
  title: string
  path: string
  name: string
}

export const useAppStore = defineStore('app', () => {
  // 用户状态
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const token = ref<string | null>(localStorage.getItem('token'))
  const apiUrl = ref(import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

  // UI 状态
  const isDarkMode = ref(localStorage.getItem('theme') === 'dark')
  const sidebarCollapsed = ref(false)
  
  // 标签页状态
  const visitedViews = ref<VisitedView[]>([])
  const cachedViews = ref<string[]>([])

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // 主题切换
  const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
  }

  // 标签页管理
  const addView = (view: VisitedView) => {
    if (!visitedViews.value.some(v => v.path === view.path)) {
      visitedViews.value.push(view)
    }
    if (view.name && !cachedViews.value.includes(view.name)) {
      cachedViews.value.push(view.name)
    }
  }

  const removeView = (path: string) => {
    const index = visitedViews.value.findIndex(v => v.path === path)
    if (index > -1) {
      const view = visitedViews.value[index]
      visitedViews.value.splice(index, 1)
      // 从缓存中移除
      const cacheIndex = cachedViews.value.indexOf(view.name)
      if (cacheIndex > -1) {
        cachedViews.value.splice(cacheIndex, 1)
      }
    }
  }

  const closeAllViews = () => {
    visitedViews.value = []
    cachedViews.value = []
  }

  const closeOthersViews = (path: string) => {
    const current = visitedViews.value.find(v => v.path === path)
    if (current) {
      visitedViews.value = [current]
      cachedViews.value = [current.name]
    }
  }

  // 设置认证 token
  const setToken = (newToken: string | null) => {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    } else {
      localStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
    }
  }

  // 初始化 token
  if (token.value) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  async function login(username: string, password: string) {
    isLoading.value = true
    try {
      const response = await api.post('/auth/login', { username, password })
      const { access_token } = response.data

      setToken(access_token)
      await fetchUserInfo()

      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || '登录失败'
      throw new Error(message)
    } finally {
      isLoading.value = false
    }
  }

  async function register(username: string, email: string, password: string, fullName?: string) {
    isLoading.value = true
    try {
      await api.post('/auth/register', {
        username,
        email,
        password,
        full_name: fullName,
      })
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || '注册失败'
      throw new Error(message)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserInfo() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return user.value
    } catch (error) {
      setToken(null)
      user.value = null
      throw error
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // 忽略登出错误
    } finally {
      setToken(null)
      user.value = null
      // 清除标签页
      closeAllViews()
    }
  }

  async function refreshToken() {
    try {
      const response = await api.post('/auth/refresh-token')
      const { access_token } = response.data
      setToken(access_token)
      return true
    } catch (error) {
      setToken(null)
      user.value = null
      return false
    }
  }

  return {
    // 状态
    user,
    isLoading,
    token,
    apiUrl,
    isDarkMode,
    sidebarCollapsed,
    visitedViews,
    cachedViews,
    // 计算属性
    isAuthenticated,
    // 方法
    toggleTheme,
    addView,
    removeView,
    closeAllViews,
    closeOthersViews,
    login,
    register,
    logout,
    refreshToken,
    fetchUserInfo,
    setToken,
  }
})
