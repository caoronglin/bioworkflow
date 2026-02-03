<template>
  <div class="pipelines-page">
    <!-- 切换视图 -->
    <div class="view-toggle">
      <el-radio-group v-model="viewMode" size="large">
        <el-radio-button value="list">
          <el-icon><List /></el-icon> 列表视图
        </el-radio-button>
        <el-radio-button value="editor">
          <el-icon><Edit /></el-icon> 可视化编辑器
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 列表视图 -->
    <el-card v-if="viewMode === 'list'">
      <template #header>
        <div class="card-header">
          <span>流水线管理</span>
          <el-button type="primary" @click="viewMode = 'editor'">
            <el-icon><Plus /></el-icon> 创建流水线
          </el-button>
        </div>
      </template>

      <el-table :data="pipelines" v-loading="loading">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="editPipeline(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button link type="success" size="small" @click="executePipeline(row.id)">
              <el-icon><VideoPlay /></el-icon> 执行
            </el-button>
            <el-button link type="danger" size="small" @click="deletePipeline(row.id)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 示例数据提示 -->
      <el-empty v-if="pipelines.length === 0" description="暂无流水线，点击「创建流水线」开始">
        <el-button type="primary" @click="viewMode = 'editor'">创建第一个流水线</el-button>
      </el-empty>
    </el-card>

    <!-- 可视化编辑器视图 -->
    <div v-else class="editor-container">
      <WorkflowEditor />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { List, Edit, Plus, VideoPlay, Delete } from '@element-plus/icons-vue'
import WorkflowEditor from '@/components/workflow/WorkflowEditor.vue'
import { pipelinesAPI } from '@/api'

const viewMode = ref<'list' | 'editor'>('list')
const pipelines = ref<any[]>([])
const loading = ref(false)

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    active: 'success',
    running: 'warning',
    draft: 'info',
    failed: 'danger',
  }
  return typeMap[status] || 'info'
}

const loadPipelines = async () => {
  loading.value = true
  try {
    const res = await pipelinesAPI.list()
    pipelines.value = res || []
  } catch (error) {
    ElMessage.error('加载流水线失败')
  } finally {
    loading.value = false
  }
}

const editPipeline = (row: any) => {
  viewMode.value = 'editor'
  ElMessage.info(`编辑流水线: ${row.name}`)
}

const executePipeline = (id: string) => {
  pipelinesAPI.execute(id).then(() => {
    ElMessage.success('流水线已提交执行')
  }).catch(() => ElMessage.error('执行失败'))
}

const deletePipeline = (id: string) => {
  pipelinesAPI.delete(id).then(() => {
    ElMessage.success('已删除')
    loadPipelines()
  }).catch(() => ElMessage.error('删除失败'))
}

onMounted(() => {
  loadPipelines()
})
</script>

<style scoped lang="scss">
.pipelines-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  padding: 20px;

  .view-toggle {
    margin-bottom: 16px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-size: 16px;
      font-weight: 600;
    }
  }

  .editor-container {
    flex: 1;
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }
}
</style>
