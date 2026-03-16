<template>
  <div class="knowledge-page">
    <el-row :gutter="20">
      <!-- 左侧：文档列表 -->
      <el-col :span="8">
        <el-card class="doc-list-card">
          <template #header>
            <div class="card-header">
              <span>知识库文档</span>
              <el-button type="primary" size="small" @click="showUploadDialog = true">
                <el-icon><Upload /></el-icon> 上传
              </el-button>
            </div>
          </template>

          <!-- 搜索框 -->
          <el-input v-model="searchQuery" placeholder="搜索文档..." class="search-input" clearable>
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <!-- 文档分类 -->
          <el-tree
            :data="documentTree"
            :props="{ label: 'name', children: 'children' }"
            default-expand-all
            @node-click="onDocClick"
            highlight-current
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.type === 'folder'"><Folder /></el-icon>
                <el-icon v-else><Document /></el-icon>
                <span>{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧：内容区 -->
      <el-col :span="16">
        <!-- AI 问答 -->
        <el-card class="qa-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><ChatDotRound /></el-icon> AI 知识问答</span>
            </div>
          </template>

          <div class="chat-container">
          <div class="chat-messages" ref="chatMessagesRef">
            <div
              style="height: 300px; overflow-y: auto"
              ref="virtualParentRef"
            >
              <div :style="{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }">
                <div
                  v-for="virtualRow in virtualizer.getVirtualItems()"
                  :key="String(virtualRow.key)"
                  :style="{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    transform: `translateY(${virtualRow.start}px)`,
                  }"
                >
                  <div :class="['message', chatMessages[virtualRow.index].role]">
                    <div class="message-content">
                      <div class="avatar">
                        <el-icon v-if="chatMessages[virtualRow.index].role === 'user'"><User /></el-icon>
                        <el-icon v-else><Monitor /></el-icon>
                      </div>
                      <div class="text" v-html="chatMessages[virtualRow.index].content"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

            <div class="chat-input">
              <el-input
                v-model="userQuestion"
                placeholder="输入问题，AI 将基于知识库回答..."
                @keyup.enter="askQuestion"
              >
                <template #append>
                  <el-button @click="askQuestion" :loading="asking">
                    <el-icon><Promotion /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </div>
          </div>
        </el-card>

        <!-- 文档预览 -->
        <el-card v-if="selectedDoc" class="preview-card">
          <template #header>
            <div class="card-header">
              <span>{{ selectedDoc.name }}</span>
              <el-button-group>
                <el-button size="small"><el-icon><Edit /></el-icon></el-button>
                <el-button size="small" type="danger"><el-icon><Delete /></el-icon></el-button>
              </el-button-group>
            </div>
          </template>
          <div class="doc-content" v-html="selectedDoc.content"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px">
      <el-upload
        drag
        action="/api/knowledge/upload"
        multiple
        :on-success="onUploadSuccess"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、Markdown、TXT 文件</div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Upload, Search, Folder, Document, ChatDotRound,
  User, Monitor, Promotion, Edit, Delete, UploadFilled
} from '@element-plus/icons-vue'
import { useVirtualizer } from '@tanstack/vue-virtual'
import { knowledgeAPI } from '@/api'

const searchQuery = ref('')
const showUploadDialog = ref(false)
const selectedDoc = ref<any>(null)
const userQuestion = ref('')
const asking = ref(false)
const chatMessagesRef = ref<HTMLElement>()
const virtualParentRef = ref<HTMLElement>()

// 聊天消息 - 必须在虚拟列表配置之前声明
const chatMessages = ref([
  { role: 'assistant', content: '你好！我是 BioWorkflow AI 助手，可以回答关于生物信息学工作流的问题。' },
])

// 虚拟列表配置 - 使用 getter 函数
const virtualizer = useVirtualizer({
  get count() { return chatMessages.value.length },
  getScrollElement: () => virtualParentRef.value as Element | null,
  estimateSize: () => 80,
  overscan: 5,
})

const scrollToBottom = () => {
  nextTick(() => {
    virtualizer.value?.scrollToIndex(chatMessages.value.length - 1, { align: 'end' })
  })
}

// 文档树数据（从后端获取）
const documentTree = ref<any[]>([])

// 点击文档
const onDocClick = (data: any) => {
  if (data.type === 'file') {
    knowledgeAPI.getDocument(data.id)
      .then((res: any) => {
        selectedDoc.value = {
          name: (res as any).title || data.name,
          content: (res as any).content || '<p>暂无内容</p>',
        }
      })
      .catch(() => ElMessage.error('加载文档失败'))
  }
}

// AI 问答
const askQuestion = async () => {
  if (!userQuestion.value.trim()) return
  
  const question = userQuestion.value
  chatMessages.value.push({ role: 'user', content: question })
  userQuestion.value = ''
  asking.value = true

  await scrollToBottom()

  knowledgeAPI.aiQuery(question, true)
    .then((res: any) => {
      chatMessages.value.push({
        role: 'assistant',
        content: (res as any).answer || '暂无回答',
      })
    })
    .catch(() => {
      chatMessages.value.push({ role: 'assistant', content: '抱歉，回答失败，请稍后重试。' })
    })
    .finally(() => {
      asking.value = false
      scrollToBottom()
    })
}

// 上传成功
const onUploadSuccess = () => {
  ElMessage.success('文档上传成功')
  showUploadDialog.value = false
  loadDocuments()
}

const loadDocuments = () => {
  knowledgeAPI.listDocuments()
    .then((res: any) => {
      const docs = (res as any)?.items || (res as any) || []
      documentTree.value = docs.map((d: any) => ({
        name: d.title,
        id: d.id,
        type: 'file',
      }))
    })
    .catch(() => ElMessage.error('加载文档列表失败'))
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped lang="scss">
.knowledge-page {
  padding: 20px;
  height: calc(100vh - 120px);

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .doc-list-card {
    height: 100%;

    .search-input {
      margin-bottom: 16px;
    }

    .tree-node {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .qa-card {
    margin-bottom: 20px;

    .chat-container {
      .chat-messages {
        height: 300px;
        overflow-y: auto;
        padding: 16px;
        background: #f5f7fa;
        border-radius: 8px;
        margin-bottom: 16px;

        .message {
          margin-bottom: 16px;

          .message-content {
            display: flex;
            gap: 12px;

            .avatar {
              width: 36px;
              height: 36px;
              border-radius: 50%;
              background: #409eff;
              color: #fff;
              display: flex;
              align-items: center;
              justify-content: center;
              flex-shrink: 0;
            }

            .text {
              background: #fff;
              padding: 12px 16px;
              border-radius: 8px;
              max-width: 80%;
              line-height: 1.6;
            }
          }

          &.user {
            .message-content {
              flex-direction: row-reverse;
              .avatar { background: #67c23a; }
              .text { background: #ecf5ff; }
            }
          }
        }
      }
    }
  }

  .preview-card {
    .doc-content {
      padding: 16px;
      line-height: 1.8;

      :deep(pre) {
        background: #f5f7fa;
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;
      }
    }
  }
}
</style>
