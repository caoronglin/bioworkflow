<template>
  <div class="conda-page">
    <el-row :gutter="20">
      <!-- 左侧：环境列表 -->
      <el-col :span="8">
        <el-card class="env-list-card">
          <template #header>
            <div class="card-header">
              <span>Conda 环境</span>
              <el-button type="primary" size="small" @click="showCreateDialog = true">
                <el-icon><Plus /></el-icon> 创建
              </el-button>
            </div>
          </template>

          <el-input
            v-model="envSearchQuery"
            placeholder="搜索环境..."
            class="search-input"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-table
            :data="filteredEnvironments"
            style="width: 100%"
            highlight-current-row
            @row-click="selectEnvironment"
            v-loading="loadingEnvs"
          >
            <el-table-column prop="name" label="环境名称" show-overflow-tooltip />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-dropdown trigger="click" @command="(cmd: string) => handleEnvCommand(cmd, row)">
                  <el-button link type="primary" size="small">
                    <el-icon><More /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="clone">克隆</el-dropdown-item>
                      <el-dropdown-item command="export">导出</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="environments.length === 0 && !loadingEnvs" description="暂无 Conda 环境" />
        </el-card>
      </el-col>

      <!-- 右侧：包列表和详情 -->
      <el-col :span="16">
        <el-card v-if="selectedEnv" class="package-list-card">
          <template #header>
            <div class="card-header">
              <span>{{ selectedEnv.name }} - 已安装包</span>
              <div class="header-actions">
                <el-input
                  v-model="packageSearchQuery"
                  placeholder="搜索包..."
                  style="width: 200px; margin-right: 12px"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-button type="primary" size="small" @click="showInstallDialog = true">
                  <el-icon><Plus /></el-icon> 安装包
                </el-button>
              </div>
            </div>
          </template>

          <div style="height: 400px; overflow-y: auto" ref="packageListRef">
            <div :style="{ height: `${packageVirtualizer.getTotalSize()}px`, position: 'relative' }">
              <div
                v-for="virtualRow in packageVirtualizer.getVirtualItems()"
                :key="String(virtualRow.key)"
                :style="{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                }"
              >
                <el-table :data="[filteredPackages[virtualRow.index]]" style="width: 100%">
                  <el-table-column prop="name" label="包名" sortable />
                  <el-table-column prop="version" label="版本" width="120" />
                  <el-table-column prop="channel" label="渠道" width="120" />
                  <el-table-column prop="build" label="构建" width="150" />
                  <el-table-column label="操作" width="100">
                    <template #default="{ row }">
                      <el-button link type="danger" size="small" @click="uninstallPackage(row.name)">
                        卸载
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>

          <el-empty v-if="packages.length === 0 && !loadingPackages" description="该环境暂无安装包" />
        </el-card>

        <el-card v-else class="empty-state">
          <el-empty description="请从左侧选择一个 Conda 环境查看详情">
            <el-button type="primary" @click="showCreateDialog = true">创建新环境</el-button>
          </el-empty>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建环境对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建 Conda 环境" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="环境名称" required>
          <el-input v-model="createForm.name" placeholder="输入环境名称（如：bio-env）" />
        </el-form-item>
        <el-form-item label="Python 版本">
          <el-select v-model="createForm.pythonVersion" placeholder="选择 Python 版本">
            <el-option label="Python 3.12" value="3.12" />
            <el-option label="Python 3.11" value="3.11" />
            <el-option label="Python 3.10" value="3.10" />
            <el-option label="Python 3.9" value="3.9" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始包">
          <el-input
            v-model="createForm.packages"
            type="textarea"
            rows="3"
            placeholder="输入要初始安装的包，用空格分隔（如：numpy pandas biopython）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createEnvironment" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 安装包对话框 -->
    <el-dialog v-model="showInstallDialog" title="安装包" width="500px">
      <el-form :model="installForm" label-width="80px">
        <el-form-item label="包名" required>
          <el-input v-model="installForm.name" placeholder="输入包名（如：scipy）" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="installForm.version" placeholder="可选，如：1.10.0" />
        </el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="installForm.channel" placeholder="选择渠道">
            <el-option label="conda-forge" value="conda-forge" />
            <el-option label="bioconda" value="bioconda" />
            <el-option label="defaults" value="defaults" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInstallDialog = false">取消</el-button>
        <el-button type="primary" @click="installPackage" :loading="installing">安装</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, More,
} from '@element-plus/icons-vue'
import { useVirtualizer } from '@tanstack/vue-virtual'
import { condaAPI } from '@/api'

// 环境列表
const environments = ref<any[]>([])
const loadingEnvs = ref(false)
const envSearchQuery = ref('')

// 包列表
const packages = ref<any[]>([])
const loadingPackages = ref(false)
const packageSearchQuery = ref('')
const selectedEnv = ref<any>(null)

// 创建环境对话框
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  name: '',
  pythonVersion: '3.11',
  packages: '',
})

// 安装包对话框
const showInstallDialog = ref(false)
const installing = ref(false)
const installForm = ref({
  name: '',
  version: '',
  channel: 'conda-forge',
})

// 过滤后的环境列表
const filteredEnvironments = computed(() => {
  if (!envSearchQuery.value) return environments.value
  return environments.value.filter(env =>
    env.name.toLowerCase().includes(envSearchQuery.value.toLowerCase())
  )
})

// 过滤后的包列表
const filteredPackages = computed(() => {
  if (!packageSearchQuery.value) return packages.value
  return packages.value.filter(pkg =>
    pkg.name.toLowerCase().includes(packageSearchQuery.value.toLowerCase())
  )
})

// 包列表虚拟滚动
const packageListRef = ref<HTMLElement | null>(null)
const packageVirtualizer = useVirtualizer({
  count: filteredPackages.value.length,
  getScrollElement: () => packageListRef.value,
  estimateSize: () => 50,
  overscan: 10,
})

// 加载环境列表
const loadEnvironments = async () => {
  loadingEnvs.value = true
  try {
    const res = await condaAPI.listEnvironments()
    environments.value = (res as any) || []
  } catch (error) {
    ElMessage.error('加载 Conda 环境失败')
  } finally {
    loadingEnvs.value = false
  }
}

// 选择环境
const selectEnvironment = (row: any) => {
  selectedEnv.value = row
  loadPackages(row.name)
}

// 加载包列表
const loadPackages = async (envName: string) => {
  loadingPackages.value = true
  try {
    const res = await condaAPI.listPackages(envName)
    packages.value = (res as any) || []
  } catch (error) {
    ElMessage.error('加载包列表失败')
  } finally {
    loadingPackages.value = false
  }
}

// 创建环境
const createEnvironment = async () => {
  if (!createForm.value.name) {
    ElMessage.warning('请输入环境名称')
    return
  }

  creating.value = true
  try {
    const packages = createForm.value.packages
      ? createForm.value.packages.split(/\s+/).filter(Boolean)
      : []

    if (createForm.value.pythonVersion) {
      packages.unshift(`python=${createForm.value.pythonVersion}`)
    }

    await condaAPI.createEnvironment(createForm.value.name, packages)
    ElMessage.success('环境创建成功')
    showCreateDialog.value = false
    loadEnvironments()
  } catch (error) {
    ElMessage.error('创建环境失败')
  } finally {
    creating.value = false
  }
}

// 安装包
const installPackage = async () => {
  if (!installForm.value.name) {
    ElMessage.warning('请输入包名')
    return
  }

  installing.value = true
  try {
    const envName = selectedEnv.value?.name
    await condaAPI.installPackage(
      installForm.value.name,
      installForm.value.version || undefined,
      envName
    )
    ElMessage.success('包安装成功')
    showInstallDialog.value = false
    if (envName) loadPackages(envName)
  } catch (error) {
    ElMessage.error('安装包失败')
  } finally {
    installing.value = false
  }
}

// 卸载包
const uninstallPackage = async (packageName: string) => {
  try {
    await ElMessageBox.confirm(`确定要卸载 ${packageName} 吗？`, '确认卸载', {
      confirmButtonText: '卸载',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const envName = selectedEnv.value?.name
    await condaAPI.uninstallPackage(packageName, envName)
    ElMessage.success('包已卸载')
    if (envName) loadPackages(envName)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('卸载包失败')
    }
  }
}

// 处理环境命令
const handleEnvCommand = async (command: string, env: any) => {
  switch (command) {
    case 'clone':
      ElMessage.info('克隆功能开发中...')
      break
    case 'export':
      ElMessage.info('导出功能开发中...')
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除环境 ${env.name} 吗？此操作不可恢复。`,
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        await condaAPI.deleteEnvironment(env.name)
        ElMessage.success('环境已删除')
        loadEnvironments()
        if (selectedEnv.value?.name === env.name) {
          selectedEnv.value = null
          packages.value = []
        }
      } catch (error: any) {
        if (error !== 'cancel') ElMessage.error('删除环境失败')
      }
      break
  }
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped lang="scss">
.conda-page {
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
  }

  .env-list-card {
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

  .package-list-card {
    height: 100%;
  }

  .empty-state {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
