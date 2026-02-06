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

export const useAppStore = defineStore('app', () => {
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const token = ref<string | null>(localStorage.getItem('token'))
  const apiUrl = ref(import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

  const isAuthenticated = computed(() => !!token.value && !!user.value)

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
      const { access_token, token_type } = response.data

      setToken(access_token)

      // 获取用户信息
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
      // 如果获取用户信息失败，清除 token
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
    }
  }

  async function refreshToken() {
    try {
      const response = await api.post('/auth/refresh-token')
      const { access_token } = response.data
      setToken(access_token)
      return true
    } catch (error) {
      // 刷新失败，清除登录状态
      setToken(null)
      user.value = null
      return false
    }
  }

  return {
    user,
    isLoading,
    token,
    apiUrl,
    isAuthenticated,
    login,
    register,
    logout,
    refreshToken,
    fetchUserInfo,
    setToken,
  }
})
