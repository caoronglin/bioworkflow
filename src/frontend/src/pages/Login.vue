<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <el-icon class="login-logo" :size="48"><Connection /></el-icon>
        <h1 class="login-title">BioWorkflow</h1>
        <p class="login-subtitle">生物信息学工作流管理平台</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            :disabled="loading"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span class="footer-text">还没有账号？</span>
        <el-button type="primary" link @click="showRegister = true">立即注册</el-button>
      </div>
    </div>

    <!-- 注册对话框 -->
    <el-dialog v-model="showRegister" title="注册新账号" width="420px" :close-on-click-modal="false">
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-position="top"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="姓名" prop="fullName">
          <el-input v-model="registerForm.fullName" placeholder="请输入姓名（可选）" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="handleRegister">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const appStore = useAppStore()

const formRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  email: '',
  fullName: '',
  password: '',
  confirmPassword: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度为3-32个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await appStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = (router.currentRoute.value.query.redirect as string) || '/'
    router.push(redirect)
  } catch (error: any) {
    ElMessage.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return

  registerLoading.value = true
  try {
    await appStore.register(
      registerForm.username,
      registerForm.email,
      registerForm.password,
      registerForm.fullName || undefined,
    )
    ElMessage.success('注册成功，请登录')
    showRegister.value = false
    form.username = registerForm.username
    form.password = ''
  } catch (error: any) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-card {
  width: 400px;
  padding: 48px 40px 36px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-logo {
  color: #409eff;
  margin-bottom: 12px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #e0e0e0;
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.login-subtitle {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.login-card :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  box-shadow: none;
  transition: border-color 0.3s;
}

.login-card :deep(.el-input__wrapper:hover) {
  border-color: rgba(64, 158, 255, 0.4);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
}

.login-card :deep(.el-input__inner) {
  color: #e0e0e0;
}

.login-card :deep(.el-input__inner::placeholder) {
  color: #6c6c6c;
}

.login-card :deep(.el-input__prefix .el-icon) {
  color: #6c6c6c;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
  letter-spacing: 4px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
}

.footer-text {
  color: #6c6c6c;
  font-size: 13px;
}
</style>
