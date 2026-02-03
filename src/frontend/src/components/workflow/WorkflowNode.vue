<template>
  <div :class="['workflow-node', `node-${type}`]">
    <div class="node-header">
      <span class="node-icon">
        <el-icon v-if="type === 'input'"><Upload /></el-icon>
        <el-icon v-else-if="type === 'process'"><Operation /></el-icon>
        <el-icon v-else><Download /></el-icon>
      </span>
      <span class="node-label">{{ data.label }}</span>
      <el-button 
        class="delete-btn" 
        :icon="Close" 
        size="small" 
        circle 
        @click.stop="$emit('delete')"
      />
    </div>
    <div class="node-body">
      <div v-if="data.script" class="node-info">
        <el-icon><Document /></el-icon>
        <span>{{ truncate(data.script, 20) }}</span>
      </div>
      <div v-if="data.conda_env" class="node-info">
        <el-icon><Box /></el-icon>
        <span>{{ data.conda_env }}</span>
      </div>
    </div>
    <!-- 连接点 -->
    <Handle v-if="type !== 'output'" type="source" :position="Position.Right" />
    <Handle v-if="type !== 'input'" type="target" :position="Position.Left" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { Upload, Download, Operation, Close, Document, Box } from '@element-plus/icons-vue'

defineProps<{
  data: {
    label: string
    script?: string
    conda_env?: string
  }
  type: 'input' | 'process' | 'output'
}>()

defineEmits<{
  delete: []
}>()

const truncate = (str: string, len: number) => {
  return str.length > len ? str.slice(0, len) + '...' : str
}
</script>

<style scoped lang="scss">
.workflow-node {
  min-width: 180px;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  
  &.node-input {
    border-color: #67c23a;
    .node-header { background: #f0f9eb; color: #67c23a; }
  }
  
  &.node-process {
    border-color: #409eff;
    .node-header { background: #ecf5ff; color: #409eff; }
  }
  
  &.node-output {
    border-color: #e6a23c;
    .node-header { background: #fdf6ec; color: #e6a23c; }
  }

  .node-header {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 6px 6px 0 0;
    font-weight: 600;

    .node-icon {
      margin-right: 8px;
      display: flex;
      align-items: center;
    }

    .node-label {
      flex: 1;
      font-size: 14px;
    }

    .delete-btn {
      opacity: 0;
      transition: opacity 0.2s;
    }
  }

  &:hover .delete-btn {
    opacity: 1;
  }

  .node-body {
    padding: 8px 12px;
    font-size: 12px;
    color: #909399;

    .node-info {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 4px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

:deep(.vue-flow__handle) {
  width: 12px;
  height: 12px;
  background: #409eff;
  border: 2px solid #fff;
  
  &.vue-flow__handle-right {
    right: -8px;
  }
  
  &.vue-flow__handle-left {
    left: -8px;
  }
}
</style>
