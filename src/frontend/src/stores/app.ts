import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const user = ref<any>(null)
  const isLoading = ref(false)
  const apiUrl = ref(import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

  const isAuthenticated = computed(() => !!user.value)

  async function login(username: string, password: string) {
    isLoading.value = true
    try {
      // TODO: 实现登录逻辑
      user.value = { username, id: '1' }
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    user.value = null
  }

  return {
    user,
    isLoading,
    apiUrl,
    isAuthenticated,
    login,
    logout,
  }
})
