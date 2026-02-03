<template>
  <div class="dashboard">
    <el-row :gutter="20" class="mb-20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">12</div>
            <div class="stat-label">活跃流水线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">5</div>
            <div class="stat-label">Conda 环境</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">48</div>
            <div class="stat-label">知识库文档</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">3</div>
            <div class="stat-label">MCP 服务</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>最近执行</span>
            </div>
          </template>
          <el-table :data="recentExecutions" size="small">
            <el-table-column prop="name" label="流水线" width="150" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="time" label="时间" width="150" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <el-space direction="vertical" fill>
            <el-button type="primary" block>创建新流水线</el-button>
            <el-button block>管理 Conda 环境</el-button>
            <el-button block>查询知识库</el-button>
            <el-button block>配置 MCP 服务</el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const recentExecutions = ref([
  { name: 'Pipeline A', status: 'success', time: '2分钟前' },
  { name: 'Pipeline B', status: 'running', time: '5分钟前' },
  { name: 'Pipeline C', status: 'failed', time: '1小时前' },
])

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    running: 'info',
    failed: 'danger',
    pending: 'warning',
  }
  return typeMap[status] || 'info'
}
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
  }
}
</style>
