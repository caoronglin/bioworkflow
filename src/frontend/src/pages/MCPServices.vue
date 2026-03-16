<template>
  <div class="mcp-page">
    <el-row :gutter="20">
      <!-- 左侧：服务列表 -->
      <el-col :span="7">
        <el-card class="service-list-card">
          <template #header>
            <div class="card-header">
              <span>MCP 服务</span>
              <el-button type="primary" size="small" @click="showRegisterDialog = true">
                <el-icon><Plus /></el-icon> 注册
              </el-button>
            </div>
          </template>

          <el-input
            v-model="serviceSearchQuery"
            placeholder="搜索服务..."
            class="search-input"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <div class="service-list">
            <div
              v-for="service in filteredServices"
              :key="service.id"
              :class="['service-item', { active: selectedService?.id === service.id }]"
              @click="selectService(service)"
            >
              <div class="service-icon">
                <el-icon v-if="service.service_type === 'ai-tool'"><Cpu /></el-icon>
                <el-icon v-else-if="service.service_type === 'workflow-engine'"><Connection /></el-icon>
                <el-icon v-else><DataAnalysis /></el-icon>
              </div>
              <div class="service-info">
                <div class="service-name">{{ service.service_name }}</div>
                <div class="service-meta">
                  <el-tag size="small" :type="getStatusType(service.status)">
                    {{ service.status }}
                  </el-tag>
                  <span class="service-type">{{ service.service_type }}</span>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-if="services.length === 0" description="暂无 MCP 服务" />
        </el-card>
      </el-col>

      <!-- 右侧：服务详情 -->
      <el-col :span="17">
        <template v-if="selectedService">
          <el-card class="service-detail-card">
            <template #header>
              <div class="card-header">
                <div class="header-title">
                  <h3>{{ selectedService.service_name }}</h3>
                  <el-tag :type="getStatusType(selectedService.status)">
                    {{ selectedService.status }}
                  </el-tag>
                </div>
                <div class="header-actions">
                  <el-button type="primary" @click="testConnection">
                    <el-icon><Connection /></el-icon> 测试连接
                  </el-button>
                  <el-dropdown @command="handleServiceCommand">
                    <el-button>
                      更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">编辑配置</el-dropdown-item>
                        <el-dropdown-item command="refresh">刷新状态</el-dropdown-item>
                        <el-dropdown-item command="clone">克隆服务</el-dropdown-item>
                        <el-dropdown-item command="delete" divided type="danger">
                          删除服务
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>

            <!-- 基本信息 -->
            <el-descriptions :column="2" border>
              <el-descriptions-item label="服务ID">{{ selectedService.id }}</el-descriptions-item>
              <el-descriptions-item label="服务类型">{{ selectedService.service_type }}</el-descriptions-item>
              <el-descriptions-item label="服务端点">{{ selectedService.endpoint }}</el-descriptions-item>
              <el-descriptions-item label="注册时间">{{ formatTime(selectedService.registered_at) }}</el-descriptions-item>
              <el-descriptions-item label="最后心跳">{{ formatTime(selectedService.last_heartbeat) }}</el-descriptions-item>
              <el-descriptions-item label="能力标签">
                <el-tag v-for="cap in selectedService.capabilities" :key="cap" size="small" style="margin-right: 4px">
                  {{ cap }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 能力详情 -->
            <div class="capabilities-section">
              <h4>能力详情</h4>
              <el-collapse>
                <el-collapse-item
                  v-for="(cap, index) in selectedService.capabilities"
                  :key="index"
                  :title="cap"
                >
                  <p>这里是 {{ cap }} 能力的详细描述和配置选项。</p>
                  <el-button type="primary" size="small">测试此能力</el-button>
                </el-collapse-item>
              </el-collapse>
            </div>

            <!-- 元数据 -->
            <div v-if="selectedService.metadata" class="metadata-section">
              <h4>附加元数据</h4>
              <pre>{{ JSON.stringify(selectedService.metadata, null, 2) }}</pre>
            </div>
          </el-card>
        </template>

        <el-card v-else class="empty-state">
          <el-empty description="请从左侧选择一个 MCP 服务查看详情">
            <el-button type="primary" @click="showRegisterDialog = true">注册新服务</el-button>
          </el-empty>
        </el-card>
      </el-col>
    </el-row>

    <!-- 注册服务对话框 -->
    <el-dialog v-model="showRegisterDialog" title="注册 MCP 服务" width="600px">
      <el-form :model="registerForm" label-width="120px">
        <el-form-item label="服务名称" required>
          <el-input v-model="registerForm.service_name" placeholder="输入服务名称" />
        </el-form-item>
        <el-form-item label="服务类型" required>
          <el-select v-model="registerForm.service_type" placeholder="选择服务类型" style="width: 100%">
            <el-option label="AI 工具" value="ai-tool" />
            <el-option label="工作流引擎" value="workflow-engine" />
            <el-option label="数据源" value="data-source" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="服务端点" required>
          <el-input v-model="registerForm.endpoint" placeholder="如：http://localhost:8080/api" />
        </el-form-item>
        <el-form-item label="认证 Token">
          <el-input
            v-model="registerForm.auth_token"
            type="password"
            placeholder="可选，用于认证的 Token"
            show-password
          />
        </el-form-item>
        <el-form-item label="能力标签">
          <el-select
            v-model="registerForm.capabilities"
            multiple
            filterable
            allow-create
            placeholder="输入或选择能力标签"
            style="width: 100%"
          >
            <el-option label="文本生成" value="text-generation" />
            <el-option label="代码执行" value="code-execution" />
            <el-option label="数据分析" value="data-analysis" />
            <el-option label="流程编排" value="workflow-orchestration" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegisterDialog = false">取消</el-button>
        <el-button type="primary" @click="registerService" :loading="registering">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Connection, Cpu, DataAnalysis,
  ArrowDown
} from '@element-plus/icons-vue'
import { mcpAPI } from '@/api'

// 服务列表
const services = ref<any[]>([])
const loadingEnvs = ref(false)
const serviceSearchQuery = ref('')
const selectedService = ref<any>(null)

// 注册服务对话框
const showRegisterDialog = ref(false)
const registering = ref(false)
const registerForm = ref({
  service_name: '',
  service_type: 'ai-tool',
  endpoint: '',
  auth_token: '',
  capabilities: [] as string[],
  metadata: {},
})

// 过滤后的服务列表
const filteredServices = computed(() => {
  if (!serviceSearchQuery.value) return services.value
  return services.value.filter(s =>
    s.service_name.toLowerCase().includes(serviceSearchQuery.value.toLowerCase())
  )
})

// 状态类型映射
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    active: 'success',
    inactive: 'info',
    error: 'danger',
  }
  return typeMap[status] || 'info'
}

// 格式化时间
const formatTime = (timeStr: string | null) => {
  if (!timeStr) return '从未'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 加载服务列表
const loadServices = async () => {
  loadingEnvs.value = true
  try {
    const res = await mcpAPI.listServices()
    services.value = (res as any) || []
  } catch (error) {
    ElMessage.error('加载 MCP 服务失败')
  } finally {
    loadingEnvs.value = false
  }
}

// 选择服务
const selectService = (service: any) => {
  selectedService.value = service
}

// 注册服务
const registerService = async () => {
  if (!registerForm.value.service_name || !registerForm.value.endpoint) {
    ElMessage.warning('请填写必要信息')
    return
  }

  registering.value = true
  try {
    await mcpAPI.registerService({
      service_name: registerForm.value.service_name,
      service_type: registerForm.value.service_type,
      endpoint: registerForm.value.endpoint,
      auth_token: registerForm.value.auth_token || undefined,
      capabilities: registerForm.value.capabilities,
      metadata: registerForm.value.metadata,
    })
    ElMessage.success('服务注册成功')
    showRegisterDialog.value = false
    loadServices()
  } catch (error) {
    ElMessage.error('注册服务失败')
  } finally {
    registering.value = false
  }
}

// 测试连接
const testConnection = async () => {
  if (!selectedService.value) return
  try {
    ElMessage.info('正在测试连接...')
    // 这里可以调用一个测试 API
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.error('连接测试失败')
  }
}

// 处理服务命令
const handleServiceCommand = async (command: string) => {
  if (!selectedService.value) return

  switch (command) {
    case 'edit':
      ElMessage.info('编辑功能开发中...')
      break
    case 'refresh':
      await loadServices()
      ElMessage.success('已刷新')
      break
    case 'clone':
      ElMessage.info('克隆功能开发中...')
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除服务 ${selectedService.value.service_name} 吗？`,
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        await mcpAPI.unregisterService(selectedService.value.id)
        ElMessage.success('服务已删除')
        selectedService.value = null
        loadServices()
      } catch (error: any) {
        if (error !== 'cancel') ElMessage.error('删除服务失败')
      }
      break
  }
}

onMounted(() => {
  loadServices()
})
</script>

<style scoped lang="scss">
.mcp-page {
  padding: 20px;
  height: calc(100vh - 120px);

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .header-title {
      display: flex;
      align-items: center;
      gap: 12px;

      h3 {
        margin: 0;
        font-size: 18px;
      }
    }
  }

  .service-list-card {
    height: 100%;

    .search-input {
      margin-bottom: 16px;
    }

    .service-list {
      max-height: calc(100vh - 280px);
      overflow-y: auto;

      .service-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          background: #f5f7fa;
        }

        &.active {
          background: #ecf5ff;
          border: 1px solid #409eff;
        }

        .service-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: #409eff;
          color: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
        }

        .service-info {
          flex: 1;

          .service-name {
            font-weight: 500;
            margin-bottom: 4px;
          }

          .service-meta {
            display: flex;
            align-items: center;
            gap: 8px;

            .service-type {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }

  .service-detail-card {
    .capabilities-section {
      margin-top: 24px;

      h4 {
        margin: 0 0 16px 0;
        font-size: 16px;
      }
    }

    .metadata-section {
      margin-top: 24px;

      h4 {
        margin: 0 0 16px 0;
        font-size: 16px;
      }

      pre {
        background: #f5f7fa;
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;
        font-size: 12px;
      }
    }
  }

  .empty-state {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
