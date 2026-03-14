<template>
  <div
    class="notebook-cell"
    :class="{
      'is-active': isActive,
      'is-running': isRunning,
      'is-error': hasError,
    }"
    @click="$emit('activate')"
  >
    <!-- 单元格头部 -->
    <div class="cell-header">
      <div class="cell-type-badge" :class="cellType">
        {{ cellType === 'code' ? 'In [' + (executionCount || ' ') + ']:' : 'Markdown:' }}
      </div>
      <div class="cell-actions">
        <el-tooltip content="运行单元格">
          <el-button
            :icon="CaretRight"
            size="small"
            circle
            :loading="isRunning"
            @click.stop="$emit('run')"
          />
        </el-tooltip>
        <el-tooltip content="更改类型">
          <el-button
            :icon="cellType === 'code' ? Document : EditPen"
            size="small"
            circle
            @click.stop="toggleType"
          />
        </el-tooltip>
        <el-tooltip content="删除">
          <el-button
            :icon="Delete"
            size="small"
            circle
            type="danger"
            @click.stop="$emit('delete')"
          />
        </el-tooltip>
      </div>
    </div>

    <!-- 代码编辑器 -->
    <div class="cell-editor">
      <div
        v-if="cellType === 'markdown' && !isEditing"
        class="markdown-preview"
        v-html="renderedMarkdown"
        @dblclick="isEditing = true"
      />
      <textarea
        v-else
        ref="editor"
        v-model="localContent"
        class="cell-input"
        :class="cellType"
        @keydown="handleKeydown"
        @blur="cellType === 'markdown' ? isEditing = false : null"
        spellcheck="false"
      />
    </div>

    <!-- 输出区域 -->
    <div v-if="outputs.length > 0" class="cell-outputs">
      <div
        v-for="(output, index) in outputs"
        :key="index"
        class="cell-output"
        :class="output.type"
      >
        <!-- 流输出 -->
        <pre v-if="output.type === 'stream'" class="output-stream">{{ output.content.text }}</pre>

        <!-- 执行结果 -->
        <div v-else-if="output.type === 'execute_result'" class="output-result">
          <div class="execution-count">Out[{{ output.content.execution_count }}]:</div>
          <pre v-if="output.content.data['text/plain']">{{ output.content.data['text/plain'] }}</pre>
          <img
            v-if="output.content.data['image/png']"
            :src="'data:image/png;base64,' + output.content.data['image/png']"
          />
        </div>

        <!-- 显示数据 -->
        <div v-else-if="output.type === 'display_data'" class="output-display">
          <pre v-if="output.content.data['text/plain']">{{ output.content.data['text/plain'] }}</pre>
          <img
            v-if="output.content.data['image/png']"
            :src="'data:image/png;base64,' + output.content.data['image/png']"
          />
          <div
            v-if="output.content.data['text/html']"
            v-html="DOMPurify.sanitize(output.content.data['text/html'])"
          />
        </div>

        <!-- 错误输出 -->
        <div v-else-if="output.type === 'error'" class="output-error">
          <div class="error-name">{{ output.content.ename }}: {{ output.content.evalue }}</div>
          <pre class="error-traceback">{{ formatTraceback(output.content.traceback) }}</pre>
        </div>
      </div>
    </div>

    <!-- 状态指示器 -->
    <div v-if="isRunning" class="cell-status">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>运行中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  CaretRight,
  Delete,
  Document,
  EditPen,
  Loading,
} from '@element-plus/icons-vue'

interface Output {
  type: string
  content: any
}

interface Props {
  content: string
  cellType: 'code' | 'markdown'
  isActive: boolean
  isRunning?: boolean
  executionCount?: number
  outputs?: Output[]
}

const props = withDefaults(defineProps<Props>(), {
  isRunning: false,
  executionCount: 0,
  outputs: () => [],
})

const emit = defineEmits<{
  (e: 'update:content', value: string): void
  (e: 'update:cellType', value: 'code' | 'markdown'): void
  (e: 'run'): void
  (e: 'delete'): void
  (e: 'activate'): void
  (e: 'addBelow'): void
}>()

const editor = ref<HTMLTextAreaElement>()
const localContent = ref(props.content)
const isEditing = ref(false)
const hasError = computed(() => props.outputs.some(o => o.type === 'error'))

// 渲染 Markdown
const renderedMarkdown = computed(() => {
  return DOMPurify.sanitize(marked(localContent.value || '') as string)
})

// 同步内容
watch(() => props.content, (newVal) => {
  localContent.value = newVal
})

watch(localContent, (newVal) => {
  emit('update:content', newVal)
})

// 切换单元格类型
const toggleType = () => {
  const newType = props.cellType === 'code' ? 'markdown' : 'code'
  emit('update:cellType', newType)
  if (newType === 'markdown') {
    isEditing.value = false
  }
}

// 处理键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  // Shift + Enter: 运行并移动到下一个
  if (e.shiftKey && e.key === 'Enter') {
    e.preventDefault()
    emit('run')
    return
  }

  // Ctrl + Enter: 运行并保持在当前
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault()
    emit('run')
    return
  }

  // Alt + Enter: 运行并在下方插入新单元格
  if (e.altKey && e.key === 'Enter') {
    e.preventDefault()
    emit('run')
    emit('addBelow')
    return
  }

  // Esc: 退出编辑模式 (Markdown)
  if (e.key === 'Escape' && props.cellType === 'markdown') {
    isEditing.value = false
    return
  }
}

// 格式化错误堆栈
const formatTraceback = (traceback: string[]) => {
  if (!traceback) return ''
  return traceback.join('\n')
}

// 激活时聚焦
watch(() => props.isActive, (active) => {
  if (active && props.cellType === 'code') {
    nextTick(() => {
      editor.value?.focus()
    })
  }
})
</script>

<style scoped lang="scss">
.notebook-cell {
  border: 2px solid transparent;
  border-radius: 8px;
  margin-bottom: 12px;
  background: var(--el-bg-color);
  transition: all 0.2s;

  &.is-active {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 3px var(--el-color-primary-light-9);
  }

  &.is-running {
    .cell-type-badge {
      background: var(--el-color-warning);
    }
  }

  &.is-error {
    border-color: var(--el-color-danger);
  }
}

.cell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.cell-type-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  font-family: 'Monaco', 'Menlo', monospace;

  &.code {
    color: var(--el-color-primary);
  }

  &.markdown {
    color: var(--el-color-success);
  }
}

.cell-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;

  .notebook-cell:hover &,
  .notebook-cell.is-active & {
    opacity: 1;
  }
}

.cell-editor {
  padding: 12px;
}

.cell-input {
  width: 100%;
  min-height: 60px;
  padding: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: var(--el-color-primary);
  }

  &.code {
    background: #f8f9fa;
  }

  &.markdown {
    background: var(--el-bg-color);
  }
}

.markdown-preview {
  padding: 12px;
  min-height: 60px;
  cursor: pointer;

  &:hover {
    background: var(--el-fill-color-light);
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    margin-top: 0;
    margin-bottom: 12px;
  }

  :deep(p) {
    margin-bottom: 8px;
  }

  :deep(code) {
    background: var(--el-fill-color);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
  }

  :deep(pre) {
    background: var(--el-fill-color);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;

    code {
      background: none;
      padding: 0;
    }
  }
}

.cell-outputs {
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.cell-output {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-bottom: none;
  }
}

.output-stream {
  margin: 0;
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--el-text-color-primary);
}

.output-result {
  .execution-count {
    font-size: 12px;
    color: var(--el-color-success);
    font-weight: 600;
    margin-bottom: 4px;
  }

  pre {
    margin: 0;
    font-family: monospace;
    font-size: 13px;
  }

  img {
    max-width: 100%;
    height: auto;
  }
}

.output-display {
  img {
    max-width: 100%;
    height: auto;
  }
}

.output-error {
  .error-name {
    color: var(--el-color-danger);
    font-weight: 600;
    margin-bottom: 8px;
  }

  .error-traceback {
    margin: 0;
    padding: 12px;
    background: var(--el-color-danger-light-9);
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    color: var(--el-color-danger);
    overflow-x: auto;
  }
}

.cell-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-color-warning-light-9);
  border-radius: 0 0 8px 8px;
  font-size: 12px;
  color: var(--el-color-warning);

  .is-loading {
    animation: rotating 2s linear infinite;
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 暗色模式
html.dark {
  .cell-input.code {
    background: #1e1e1e;
  }

  .output-error .error-traceback {
    background: rgba(245, 108, 108, 0.1);
  }
}
</style>
