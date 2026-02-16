<template>
  <div class="notebook-page">
    <!-- 工具栏 -->
    <div class="notebook-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button :icon="Plus" @click="addCell('code')">
            代码
          </el-button>
          <el-button :icon="Document" @click="addCell('markdown')">
            Markdown
          </el-button>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button-group>
          <el-button
            :icon="CaretRight"
            type="primary"
            :loading="isRunning"
            @click="runCurrentCell"
          >
            运行
          </el-button>
          <el-button
            :icon="VideoPlay"
            :loading="isRunningAll"
            @click="runAllCells"
          >
            全部运行
          </el-button>
          <el-button :icon="CircleClose" @click="interruptKernel">
            中断
          </el-button>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button-group>
          <el-button :icon="Delete" @click="clearAllOutputs">
            清除输出
          </el-button>
          <el-button :icon="Refresh" @click="restartKernel">
            重启内核
          </el-button>
        </el-button-group>
      </div>

      <div class="toolbar-right">
        <el-select
          v-model="selectedKernel"
          placeholder="选择内核"
          size="small"
          style="width: 150px"
        >
          <el-option
            v-for="kernel in availableKernels"
            :key="kernel.name"
            :label="kernel.display_name"
            :value="kernel.name"
          />
        </el-select>

        <el-tag
          :type="connectionStatus === 'connected' ? 'success' : 'danger'"
          size="small"
          effect="dark"
        >
          <el-icon v-if="connectionStatus === 'connected'"><CircleCheck /></el-icon>
          <el-icon v-else><CircleClose /></el-icon>
          {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
        </el-tag>
      </div>
    </div>

    <!-- 笔记本主体 -->
    <div class="notebook-container" @click="handleContainerClick">
      <!-- 标题 -->
      <div class="notebook-header">
        <input
          v-model="notebookTitle"
          class="notebook-title"
          placeholder="无标题笔记本"
        />
      </div>

      <!-- 单元格列表 -->
      <div class="cells-container">
        <NotebookCell
          v-for="(cell, index) in cells"
          :key="cell.id"
          v-model:content="cell.content"
          v-model:cell-type="cell.cell_type"
          :is-active="activeCellIndex === index"
          :is-running="runningCellIndex === index"
          :execution-count="cell.execution_count"
          :outputs="cell.outputs"
          @activate="activeCellIndex = index"
          @run="runCell(index)"
          @delete="deleteCell(index)"
          @add-below="addCell('code', index + 1)"
        />
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="cells.length === 0"
        description="点击添加第一个单元格"
      >
        <el-button type="primary" @click="addCell('code')">
          添加代码单元格
        </el-button>
      </el-empty>
    </div>

    <!-- 内核状态栏 -->
    <div class="kernel-status-bar">
      <div class="status-left">
        <span v-if="kernelId">
          内核: {{ selectedKernel }} ({{ kernelId.slice(0, 8) }}...)
        </span>
        <span v-else>内核未启动</span>
      </div>
      <div class="status-right">
        <span v-if="lastSaved">上次保存: {{ formatTime(lastSaved) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Document,
  CaretRight,
  VideoPlay,
  CircleClose,
  Delete,
  Refresh,
  CircleCheck,
} from '@element-plus/icons-vue'
import NotebookCell from '@/components/jupyter/NotebookCell.vue'
import { jupyterAPI } from '@/api'

interface Cell {
  id: string
  cell_type: 'code' | 'markdown'
  content: string
  execution_count: number
  outputs: any[]
}

// 状态
const notebookTitle = ref('无标题笔记本')
const cells = ref<Cell[]>([])
const activeCellIndex = ref(0)
const runningCellIndex = ref(-1)
const isRunning = ref(false)
const isRunningAll = ref(false)
const kernelId = ref('')
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')
const lastSaved = ref<Date | null>(null)
const selectedKernel = ref('python3')

// 可用内核列表
const availableKernels = ref([
  { name: 'python3', display_name: 'Python 3' },
  { name: 'ir', display_name: 'R' },
  { name: 'julia-1.9', display_name: 'Julia 1.9' },
])

// WebSocket
let ws: WebSocket | null = null

// 生成唯一ID
const generateId = () => Math.random().toString(36).substr(2, 9)

// 添加单元格
const addCell = (type: 'code' | 'markdown', index?: number) => {
  const newCell: Cell = {
    id: generateId(),
    cell_type: type,
    content: '',
    execution_count: 0,
    outputs: [],
  }

  if (index !== undefined) {
    cells.value.splice(index, 0, newCell)
    activeCellIndex.value = index
  } else {
    cells.value.push(newCell)
    activeCellIndex.value = cells.value.length - 1
  }

  nextTick(() => {
    const cellElements = document.querySelectorAll('.notebook-cell')
    const targetCell = cellElements[activeCellIndex.value] as HTMLElement
    targetCell?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

// 删除单元格
const deleteCell = (index: number) => {
  if (cells.value.length <= 1) {
    ElMessage.warning('至少保留一个单元格')
    return
  }

  cells.value.splice(index, 1)

  if (activeCellIndex.value >= cells.value.length) {
    activeCellIndex.value = cells.value.length - 1
  }
}

// 运行单元格
const runCell = async (index: number) => {
  const cell = cells.value[index]
  if (!cell || cell.cell_type !== 'code') return

  // 确保内核已启动
  if (!kernelId.value) {
    await startKernel()
  }

  isRunning.value = true
  runningCellIndex.value = index
  cell.outputs = []

  try {
    const executionId = generateId()

    // 发送执行请求
    ws?.send(JSON.stringify({
      type: 'execute',
      code: cell.content,
      execution_id: executionId,
    }))

    // 等待执行完成
    await waitForExecution(executionId, cell)

    cell.execution_count += 1
  } catch (error) {
    ElMessage.error('执行失败: ' + error)
  } finally {
    isRunning.value = false
    runningCellIndex.value = -1
  }
}

// 等待执行完成
const waitForExecution = (executionId: string, cell: Cell): Promise<void> => {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('执行超时'))
    }, 300000) // 5分钟超时

    const handleMessage = (event: MessageEvent) => {
      const msg = JSON.parse(event.data)

      if (msg.execution_id !== executionId) return

      if (msg.type === 'status' && msg.content.execution_state === 'idle') {
        clearTimeout(timeout)
        ws?.removeEventListener('message', handleMessage)
        resolve()
      } else if (msg.type === 'error') {
        clearTimeout(timeout)
        ws?.removeEventListener('message', handleMessage)
        reject(new Error(msg.content.message))
      } else {
        cell.outputs.push(msg)
      }
    }

    ws?.addEventListener('message', handleMessage)
  })
}

// 运行当前单元格
const runCurrentCell = () => {
  if (activeCellIndex.value >= 0) {
    runCell(activeCellIndex.value)
  }
}

// 运行所有单元格
const runAllCells = async () => {
  isRunningAll.value = true

  for (let i = 0; i < cells.value.length; i++) {
    if (cells.value[i].cell_type === 'code') {
      activeCellIndex.value = i
      await runCell(i)
    }
  }

  isRunningAll.value = false
  ElMessage.success('所有单元格执行完成')
}

// 清除所有输出
const clearAllOutputs = () => {
  cells.value.forEach(cell => {
    cell.outputs = []
    if (cell.cell_type === 'code') {
      cell.execution_count = 0
    }
  })
  ElMessage.success('输出已清除')
}

// 启动内核
const startKernel = async () => {
  try {
    connectionStatus.value = 'connecting'

    const response = await jupyterAPI.createKernel(selectedKernel.value)
    kernelId.value = response.kernel_id

    // 连接 WebSocket
    connectWebSocket()

    ElMessage.success('内核已启动')
  } catch (error) {
    connectionStatus.value = 'disconnected'
    ElMessage.error('启动内核失败: ' + error)
  }
}

// 连接 WebSocket
const connectWebSocket = () => {
  if (!kernelId.value) return

  ws = jupyterAPI.createKernelWebSocket(kernelId.value)

  ws.onopen = () => {
    connectionStatus.value = 'connected'
    console.log('WebSocket connected')
  }

  ws.onclose = () => {
    connectionStatus.value = 'disconnected'
    console.log('WebSocket disconnected')
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    ElMessage.error('连接错误')
  }
}

// 中断内核
const interruptKernel = async () => {
  if (!kernelId.value) return

  try {
    await jupyterAPI.interruptKernel(kernelId.value)
    ElMessage.success('已发送中断信号')
  } catch (error) {
    ElMessage.error('中断失败: ' + error)
  }
}

// 重启内核
const restartKernel = async () => {
  try {
    await ElMessageBox.confirm(
      '重启内核将清除所有变量，是否继续？',
      '确认重启',
      { type: 'warning' }
    )

    // 关闭现有内核
    if (kernelId.value) {
      ws?.close()
      await jupyterAPI.shutdownKernel(kernelId.value)
    }

    // 启动新内核
    await startKernel()
    ElMessage.success('内核已重启')
  } catch {
    // 用户取消
  }
}

// 处理容器点击
const handleContainerClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (target.classList.contains('notebook-container')) {
    activeCellIndex.value = -1
  }
}

// 格式化时间
const formatTime = (date: Date) => {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 键盘快捷键
const handleKeydown = (e: KeyboardEvent) => {
  // 全局快捷键
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case 's':
        e.preventDefault()
        // 保存功能
        lastSaved.value = new Date()
        ElMessage.success('已保存')
        break
    }
  }
}

onMounted(() => {
  // 添加默认单元格
  if (cells.value.length === 0) {
    addCell('code')
  }

  // 启动内核
  startKernel()

  // 监听键盘事件
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  // 清理
  ws?.close()

  if (kernelId.value) {
    jupyterAPI.shutdownKernel(kernelId.value)
  }

  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped lang="scss">
.notebook-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color-page);
}

.notebook-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  gap: 16px;
  flex-wrap: wrap;

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.notebook-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.notebook-header {
  margin-bottom: 24px;

  .notebook-title {
    width: 100%;
    font-size: 24px;
    font-weight: 600;
    border: none;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--el-text-color-primary);
    padding: 8px 0;
    outline: none;
    transition: border-color 0.2s;

    &:focus {
      border-color: var(--el-color-primary);
    }

    &::placeholder {
      color: var(--el-text-color-secondary);
    }
  }
}

.cells-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kernel-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

// 响应式
@media (max-width: 768px) {
  .notebook-toolbar {
    .toolbar-left,
    .toolbar-right {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
