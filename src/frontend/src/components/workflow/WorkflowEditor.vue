<template>
  <div class="workflow-editor">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group>
        <el-button @click="addNode('input')" :icon="Upload">输入节点</el-button>
        <el-button @click="addNode('process')" :icon="Operation">处理节点</el-button>
        <el-button @click="addNode('output')" :icon="Download">输出节点</el-button>
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button-group>
        <el-button @click="saveWorkflow" :icon="DocumentChecked" type="primary">保存</el-button>
        <el-button @click="runWorkflow" :icon="VideoPlay" type="success">运行</el-button>
        <el-button @click="clearWorkflow" :icon="Delete" type="danger">清空</el-button>
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button @click="fitView" :icon="FullScreen">适应视图</el-button>
    </div>

    <!-- 流程图画布 -->
    <div class="canvas-container">
      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :default-viewport="{ zoom: 1 }"
        :min-zoom="0.2"
        :max-zoom="4"
        fit-view-on-init
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        @connect="onConnect"
      >
        <Background pattern-color="#aaa" :gap="16" />
        <MiniMap />
        <Controls />

        <!-- 自定义节点 -->
        <template #node-input="nodeProps">
          <WorkflowNode :data="nodeProps.data" type="input" @delete="deleteNode(nodeProps.id)" />
        </template>
        <template #node-process="nodeProps">
          <WorkflowNode :data="nodeProps.data" type="process" @delete="deleteNode(nodeProps.id)" />
        </template>
        <template #node-output="nodeProps">
          <WorkflowNode :data="nodeProps.data" type="output" @delete="deleteNode(nodeProps.id)" />
        </template>
      </VueFlow>
    </div>

    <!-- 节点配置面板 -->
    <el-drawer v-model="showNodeConfig" title="节点配置" direction="rtl" size="400px">
      <el-form v-if="selectedNode" label-width="100px">
        <el-form-item label="节点名称">
          <el-input v-model="selectedNode.data.label" />
        </el-form-item>
        <el-form-item label="节点类型">
          <el-tag>{{ selectedNode.type }}</el-tag>
        </el-form-item>
        <el-form-item label="脚本/命令">
          <el-input v-model="selectedNode.data.script" type="textarea" rows="5" placeholder="输入 Shell 命令或脚本路径" />
        </el-form-item>
        <el-form-item label="Conda 环境">
          <el-select v-model="selectedNode.data.conda_env" placeholder="选择环境">
            <el-option label="base" value="base" />
            <el-option label="bioinformatics" value="bioinformatics" />
            <el-option label="r-env" value="r-env" />
          </el-select>
        </el-form-item>
        <el-form-item label="输入文件">
          <el-input v-model="selectedNode.data.input_files" placeholder="data/*.fastq" />
        </el-form-item>
        <el-form-item label="输出文件">
          <el-input v-model="selectedNode.data.output_files" placeholder="results/*.bam" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveNodeConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { 
  Upload, Download, Operation, DocumentChecked, 
  VideoPlay, Delete, FullScreen 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import WorkflowNode from './WorkflowNode.vue'

import type { Node, Edge, Connection } from '@vue-flow/core'

const { fitView, addNodes, addEdges } = useVueFlow()

// 节点和边
const nodes = ref<Node[]>([
  {
    id: '1',
    type: 'input',
    position: { x: 100, y: 100 },
    data: { label: '输入数据', script: '', conda_env: 'base', input_files: '', output_files: '' },
  },
])
const edges = ref<Edge[]>([])

// 节点配置
const showNodeConfig = ref(false)
const selectedNode = ref<Node | null>(null)

let nodeId = 2

// 添加节点
const addNode = (type: 'input' | 'process' | 'output') => {
  const labelMap = {
    input: '输入节点',
    process: '处理节点',
    output: '输出节点',
  }
  
  const newNode: Node = {
    id: String(nodeId++),
    type,
    position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
    data: { 
      label: `${labelMap[type]} ${nodeId - 1}`,
      script: '',
      conda_env: 'base',
      input_files: '',
      output_files: '',
    },
  }
  
  addNodes([newNode])
  ElMessage.success(`已添加 ${labelMap[type]}`)
}

// 删除节点
const deleteNode = (nodeId: string) => {
  nodes.value = nodes.value.filter(n => n.id !== nodeId)
  edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
  ElMessage.success('节点已删除')
}

// 连接节点
const onConnect = (connection: Connection) => {
  const newEdge: Edge = {
    id: `e${connection.source}-${connection.target}`,
    source: connection.source,
    target: connection.target,
    animated: true,
  }
  addEdges([newEdge])
}

// 节点点击
const onNodeClick = ({ node }: { node: Node }) => {
  selectedNode.value = node
  showNodeConfig.value = true
}

// 边点击
const onEdgeClick = ({ edge }: { edge: Edge }) => {
  ElMessage.info(`边: ${edge.source} -> ${edge.target}`)
}

// 保存节点配置
const saveNodeConfig = () => {
  showNodeConfig.value = false
  ElMessage.success('节点配置已保存')
}

// 保存工作流
const saveWorkflow = () => {
  const workflow = {
    nodes: nodes.value,
    edges: edges.value,
  }
  console.log('Workflow:', JSON.stringify(workflow, null, 2))
  ElMessage.success('工作流已保存')
}

// 运行工作流
const runWorkflow = () => {
  ElMessage.info('正在生成 Snakemake 规则并提交执行...')
  // TODO: 调用 pipelinesAPI.execute 并传递节点/边描述
}

// 清空工作流
const clearWorkflow = () => {
  nodes.value = []
  edges.value = []
  ElMessage.success('工作流已清空')
}
</script>

<style scoped lang="scss">
.workflow-editor {
  height: 100%;
  display: flex;
  flex-direction: column;

  .toolbar {
    padding: 12px 16px;
    background: #fff;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .canvas-container {
    flex: 1;
    background: #f5f7fa;
  }
}

:deep(.vue-flow) {
  background: #fafafa;
}

:deep(.vue-flow__minimap) {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

:deep(.vue-flow__controls) {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}
</style>
