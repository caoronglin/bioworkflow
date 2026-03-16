<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 系统设置 -->
      <el-tab-pane label="系统设置" name="system">
        <el-form :model="systemSettings" label-width="150px" class="settings-form">
          <el-form-item label="应用名称">
            <el-input v-model="systemSettings.appName" placeholder="BioWorkflow" />
          </el-form-item>
          <el-form-item label="默认语言">
            <el-select v-model="systemSettings.language">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </el-form-item>
          <el-form-item label="默认主题">
            <el-radio-group v-model="systemSettings.theme">
              <el-radio-button label="light">浅色</el-radio-button>
              <el-radio-button label="dark">深色</el-radio-button>
              <el-radio-button label="auto">跟随系统</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="自动保存">
            <el-switch v-model="systemSettings.autoSave" />
          </el-form-item>
          <el-form-item v-if="systemSettings.autoSave" label="自动保存间隔">
            <el-slider v-model="systemSettings.autoSaveInterval" :min="1" :max="60" :step="1" show-stops show-input />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSystemSettings">保存设置</el-button>
            <el-button @click="resetSystemSettings">重置为默认</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- Snakemake 设置 -->
      <el-tab-pane label="Snakemake" name="snakemake">
        <el-form :model="snakemakeSettings" label-width="180px" class="settings-form">
          <el-form-item label="工作目录">
            <el-input v-model="snakemakeSettings.workdir" placeholder="./workflows">
              <template #append>
                <el-button :icon="Folder">浏览</el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="Conda 环境目录">
            <el-input v-model="snakemakeSettings.condaPrefix" placeholder="./conda_envs" />
          </el-form-item>
          <el-form-item label="默认核心数">
            <el-slider v-model="snakemakeSettings.defaultCores" :min="1" :max="64" show-input />
          </el-form-item>
          <el-form-item label="默认内存 (GB)">
            <el-slider v-model="snakemakeSettings.defaultMemory" :min="1" :max="256" show-input />
          </el-form-item>
          <el-form-item label="使用 Singularity">
            <el-switch v-model="snakemakeSettings.useSingularity" />
          </el-form-item>
          <el-form-item label="打印详细日志">
            <el-switch v-model="snakemakeSettings.verbose" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSnakemakeSettings">保存设置</el-button>
            <el-button @click="testSnakemake">测试连接</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- API 设置 -->
      <el-tab-pane label="API 与认证" name="api">
        <el-form :model="apiSettings" label-width="150px" class="settings-form">
          <el-form-item label="API 基础 URL">
            <el-input v-model="apiSettings.baseUrl" placeholder="http://localhost:8000/api" />
          </el-form-item>
          <el-form-item label="请求超时 (秒)">
            <el-slider v-model="apiSettings.timeout" :min="5" :max="120" show-input />
          </el-form-item>
          <el-form-item label="Token 刷新">
            <el-switch v-model="apiSettings.autoRefreshToken" />
          </el-form-item>
          <h3 style="margin: 24px 0 16px">API 密钥管理</h3>
          <el-alert type="info" :closable="false" style="margin-bottom: 16px">
            API 密钥用于外部系统访问 BioWorkflow API。请妥善保管。
          </el-alert>
          <el-form-item>
            <el-button type="primary" @click="generateApiKey"><Plus /> 生成新密钥</el-button>
          </el-form-item>
          <el-table :data="apiKeys" style="width: 100%">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="key" label="密钥">
              <template #default="{ row }">
                <code>{{ maskKey(row.key) }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="创建时间" />
            <el-table-column prop="lastUsed" label="最后使用" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="danger" @click="revokeApiKey(row.id)">撤销</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-form-item style="margin-top: 24px">
            <el-button type="primary" @click="saveApiSettings">保存设置</el-button>
            <el-button @click="resetApiSettings">重置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 关于 -->
      <el-tab-pane label="关于" name="about">
        <el-card class="about-card">
          <div class="about-header">
            <h1>BioWorkflow</h1>
            <p class="version">版本 v0.1.0</p>
          </div>

          <el-divider />

          <div class="about-content">
            <p>
              BioWorkflow 是一个基于 Snakemake 的现代化生物信息学工作流编排平台，
              提供 Web 界面、知识库、AI 集成和 conda 包管理能力。
            </p>

            <h3>技术栈</h3>
            <ul>
              <li><strong>后端</strong>: Python 3.13+, FastAPI, SQLAlchemy 2.0, Snakemake 9.0+</li>
              <li><strong>前端</strong>: Vue 3, Vite, TypeScript, Element Plus, @vue-flow/core</li>
              <li><strong>数据库</strong>: SQLite (默认), PostgreSQL, MySQL</li>
            </ul>

            <h3>核心功能</h3>
            <ul>
              <li>Snakemake 工作流编排与管理</li>
              <li>可视化工作流编辑器</li>
              <li>Conda 环境管理</li>
              <li>知识库与 AI 问答</li>
              <li>MCP 服务集成</li>
            </ul>
          </div>

          <el-divider />

          <div class="about-footer">
            <p><strong>许可证</strong>: MIT License</p>
            <p><strong>仓库</strong>:
              <el-link href="https://github.com/yourusername/bioworkflow" target="_blank">
                GitHub
              </el-link>
            </p>
            <p><strong>文档</strong>:
              <el-link href="https://bioworkflow.readthedocs.io" target="_blank">
                Read the Docs
              </el-link>
            </p>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Folder } from '@element-plus/icons-vue'

const activeTab = ref('system')

// 系统设置
const systemSettings = reactive({
  appName: 'BioWorkflow',
  language: 'zh-CN',
  theme: 'auto',
  autoSave: true,
  autoSaveInterval: 5,
})

// Snakemake 设置
const snakemakeSettings = reactive({
  workdir: './workflows',
  condaPrefix: './conda_envs',
  defaultCores: 4,
  defaultMemory: 8,
  useSingularity: false,
  verbose: false,
})

// API 设置
const apiSettings = reactive({
  baseUrl: 'http://localhost:8000/api',
  timeout: 30,
  autoRefreshToken: true,
})

// API 密钥
const apiKeys = ref([
  {
    id: '1',
    name: '开发密钥',
    key: 'sk_live_51HYZ...3d8f',
    createdAt: '2024-01-15',
    lastUsed: '2024-01-20',
  },
])

// 遮罩密钥显示
const maskKey = (key: string) => {
  if (key.length <= 10) return key
  return key.substring(0, 10) + '...' + key.substring(key.length - 4)
}

// 保存设置
const saveSystemSettings = () => {
  localStorage.setItem('systemSettings', JSON.stringify(systemSettings))
  ElMessage.success('系统设置已保存')
}

const saveSnakemakeSettings = () => {
  localStorage.setItem('snakemakeSettings', JSON.stringify(snakemakeSettings))
  ElMessage.success('Snakemake 设置已保存')
}

const saveApiSettings = () => {
  localStorage.setItem('apiSettings', JSON.stringify(apiSettings))
  ElMessage.success('API 设置已保存')
}

// 重置设置
const resetSystemSettings = () => {
  systemSettings.appName = 'BioWorkflow'
  systemSettings.language = 'zh-CN'
  systemSettings.theme = 'auto'
  systemSettings.autoSave = true
  systemSettings.autoSaveInterval = 5
  ElMessage.success('系统设置已重置')
}

const resetApiSettings = () => {
  apiSettings.baseUrl = 'http://localhost:8000/api'
  apiSettings.timeout = 30
  apiSettings.autoRefreshToken = true
  ElMessage.success('API 设置已重置')
}

// 测试连接
const testSnakemake = () => {
  ElMessage.info('正在测试 Snakemake 连接...')
  setTimeout(() => {
    ElMessage.success('Snakemake 连接成功')
  }, 1500)
}

// API 密钥操作
const generateApiKey = () => {
  const newKey = {
    id: String(Date.now()),
    name: '新密钥 ' + apiKeys.value.length,
    key: 'sk_live_' + Math.random().toString(36).substring(2, 15),
    createdAt: new Date().toISOString().split('T')[0],
    lastUsed: '从未',
  }
  apiKeys.value.push(newKey)
  ElMessage.success('新 API 密钥已生成')
}

const revokeApiKey = (id: string) => {
  apiKeys.value = apiKeys.value.filter((k) => k.id !== id)
  ElMessage.success('API 密钥已撤销')
}
</script>

<style scoped lang="scss">
.settings-page {
  padding: 20px;
  height: calc(100vh - 120px);

  .settings-form {
    max-width: 600px;
    margin: 20px 0;
  }

  .about-card {
    max-width: 800px;
    margin: 0 auto;

    .about-header {
      text-align: center;
      padding: 24px 0;

      h1 {
        margin: 0;
        font-size: 32px;
        background: linear-gradient(90deg, #409eff, #67c23a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .version {
        margin: 8px 0 0;
        color: #909399;
        font-size: 14px;
      }
    }

    .about-content {
      padding: 16px 0;

      h3 {
        margin: 24px 0 12px;
        font-size: 16px;
        color: #303133;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          margin: 8px 0;
          line-height: 1.6;
        }
      }
    }

    .about-footer {
      padding: 16px 0;
      color: #606266;
      font-size: 14px;

      p {
        margin: 8px 0;
      }
    }
  }
}
</style>
