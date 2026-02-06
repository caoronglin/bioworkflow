<template>
  <div class="dashboard">
    <el-row :gutter="20" class="mb-20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.pipelines }}</div>
            <div class="stat-label">活跃流水线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.condaEnvs }}</div>
            <div class="stat-label">Conda 环境</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.documents }}</div>
            <div class="stat-label">知识库文档</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.mcpServices }}</div>
            <div class="stat-label">MCP 服务</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card class="chart-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>最近执行</span>
              <el-button link type="primary" @click="$router.push('/pipelines')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentExecutions" size="small" v-if="recentExecutions.length > 0">
            <el-table-column prop="pipeline_name" label="流水线" width="150" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ formatStatus(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="时间" width="150">
              <template #default="{ row }">
                {{ formatTime(row.started_at) }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无执行记录" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <el-space direction="vertical" fill style="width: 100%">
            <el-button type="primary" block @click="$router.push('/pipelines')">
              <el-icon><Plus /></el-icon> 创建新流水线
            </el-button>
            <el-button block @click="$router.push('/conda')">
              <el-icon><Box /></el-icon> 管理 Conda 环境
            </el-button>
            <el-button block @click="$router.push('/knowledge')">
              <el-icon><Document /></el-icon> 查询知识库
            </el-button>
            <el-button block @click="$router.push('/mcp')">
              <el-icon><Connection /></el-icon> 配置 MCP 服务
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Box, Document, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { pipelinesAPI, condaAPI, knowledgeAPI, mcpAPI } from '@/api'

// 统计数据
const stats = ref({
  pipelines: 0,
  condaEnvs: 0,
  documents: 0,
  mcpServices: 0,
})

const loading = ref(false)
const recentExecutions = ref<any[]>([])

// 格式化状态
const formatStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待执行',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
    draft: '草稿',
    active: '活跃',
  }
  return statusMap[status] || status
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟
  if (diff < 60000) return '刚刚'
  // 小于1小时
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  // 小于24小时
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  // 大于24小时
  return `${Math.floor(diff / 86400000)}天前`
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    running: 'info',
    completed: 'success',
    failed: 'danger',
    pending: 'warning',
    draft: 'info',
    active: 'success',
  }
  return typeMap[status] || 'info'
}

// 加载统计数据
const loadStats = async () => {
  try {
    // 并行加载统计数据
    const [pipelinesRes, condaRes, knowledgeRes, mcpRes] = await Promise.allSettled([
      pipelinesAPI.list(),
      condaAPI.listEnvironments(),
      knowledgeAPI.listDocuments(),
      mcpAPI.listServices(),
    ])

    stats.value.pipelines = pipelinesRes.status === 'fulfilled' ? (pipelinesRes.value?.data?.length || 0) : 0
    stats.value.condaEnvs = condaRes.status === 'fulfilled' ? (condaRes.value?.data?.length || 0) : 0
    stats.value.documents = knowledgeRes.status === 'fulfilled' ? (knowledgeRes.value?.data?.length || 0) : 0
    stats.value.mcpServices = mcpRes.status === 'fulfilled' ? (mcpRes.value?.data?.length || 0) : 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载最近执行
const loadRecentExecutions = async () => {
  loading.value = true
  try {
    // 获取流水线列表，然后获取每个流水线的执行历史
    const pipelinesRes = await pipelinesAPI.list()
    const pipelines = pipelinesRes.data || []

    const executions: any[] = []
    for (const pipeline of pipelines.slice(0, 5)) {
      try {
        const execRes = await pipelinesAPI.getExecutions(pipeline.id)
        const pipelineExecutions = execRes.data?.executions || []
        executions.push(...pipelineExecutions.map((e: any) => ({
          ...e,
          pipeline_name: pipeline.name,
        })))
      } catch (error) {
        // 忽略单个流水线执行记录获取失败
      }
    }

    // 按开始时间排序，取最近的10条
    executions.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
    recentExecutions.value = executions.slice(0, 10)
  } catch (error) {
    console.error('加载最近执行失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadRecentExecutions()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 20px;

  .mb-20 {
    margin-bottom: 20px;
  }

  .stat-card {
    :deep(.el-card__body) {
      padding: 20px;
    }
  }

  .stat-item {
    text-align: center;

    .stat-value {
      font-size: 32px;
      font-weight: bold;
      color: #409eff;
      margin-bottom: 10px;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
    }
  }

  .chart-card {
    :deep(.el-card__body) {
      padding: 20px;
    }
  }

  .card-header {
    font-size: 16px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
