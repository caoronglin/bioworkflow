<template>
  <div id="app" :class="['app-container', { 'dark-mode': isDarkMode }]">
    <el-container class="main-layout">
      <!-- 侧边栏导航 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
        <div class="logo">
          <el-icon class="logo-icon"><Connection /></el-icon>
          <span v-show="!isCollapse" class="logo-text">BioWorkflow</span>
        </div>
        <el-menu
          router
          :default-active="$route.path"
          :collapse="isCollapse"
          :collapse-transition="false"
          class="sidebar-menu"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <template #title>Dashboard</template>
          </el-menu-item>
          <el-menu-item index="/pipelines">
            <el-icon><SetUp /></el-icon>
            <template #title>流水线</template>
          </el-menu-item>
          <el-menu-item index="/conda">
            <el-icon><Box /></el-icon>
            <template #title>Conda 环境</template>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Notebook /></el-icon>
            <template #title>知识库</template>
          </el-menu-item>
          <el-menu-item index="/mcp">
            <el-icon><Link /></el-icon>
            <template #title>MCP 服务</template>
          </el-menu-item>
          <el-menu-item index="/notebook">
            <el-icon><EditPen /></el-icon>
            <template #title>Notebook</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>设置</template>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-footer">
          <el-button
            :icon="isCollapse ? Expand : Fold"
            text
            @click="toggleCollapse"
            class="collapse-btn"
          />
        </div>
      </el-aside>

      <!-- 主容器 -->
      <el-container class="content-container">
        <!-- 顶部栏 -->
        <el-header class="app-header">
          <div class="header-content">
            <div class="header-left">
              <el-breadcrumb :separator-icon="ArrowRight">
                <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
                <el-breadcrumb-item>{{ $route.meta?.title || '页面' }}</el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            <div class="header-right">
              <!-- 搜索框 -->
              <el-input
                v-model="searchQuery"
                placeholder="全局搜索..."
                class="global-search"
                :prefix-icon="Search"
                clearable
              />
              
              <!-- 主题切换 -->
              <el-tooltip :content="isDarkMode ? '切换亮色模式' : '切换暗色模式'">
                <el-button
                  :icon="isDarkMode ? Sunny : Moon"
                  circle
                  text
                  @click="toggleTheme"
                  class="theme-btn"
                />
              </el-tooltip>
              
              <!-- 通知 -->
              <el-badge :value="notifications.length" class="notification-badge">
                <el-button :icon="Bell" circle text @click="showNotifications" />
              </el-badge>
              
              <!-- 用户菜单 -->
              <el-dropdown trigger="click" @command="handleCommand">
                <div class="user-info">
                  <el-avatar :size="32" :icon="UserFilled" />
                  <span class="username">{{ appStore.user?.username || '未登录' }}</span>
                  <el-icon><ArrowDown /></el-icon>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :icon="User" command="profile">个人信息</el-dropdown-item>
                    <el-dropdown-item :icon="Setting" command="settings">账号设置</el-dropdown-item>
                    <el-dropdown-divider />
                    <el-dropdown-item :icon="SwitchButton" command="logout" divided>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>

        <!-- 标签页导航 -->
        <div class="tabs-container">
          <el-tabs
            v-model="activeTab"
            type="card"
            closable
            @tab-remove="removeTab"
            @tab-click="handleTabClick"
          >
            <el-tab-pane
              v-for="tab in tabs"
              :key="tab.path"
              :label="tab.title"
              :name="tab.path"
            />
          </el-tabs>
        </div>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="page-slide" mode="out-in">
              <keep-alive :include="cachedViews">
                <component :is="Component" :key="$route.path" />
              </keep-alive>
            </transition>
          </router-view>
        </el-main>

        <!-- 页脚 -->
        <el-footer class="app-footer">
          <span>BioWorkflow v2.0.0 - 生物信息学工作流管理平台</span>
        </el-footer>
      </el-container>
    </el-container>

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="notificationDrawer"
      title="通知中心"
      size="400px"
      :with-header="true"
    >
      <div class="notification-list">
        <el-timeline>
          <el-timeline-item
            v-for="(notification, index) in notifications"
            :key="index"
            :type="notification.type"
            :timestamp="notification.time"
          >
            <el-card class="notification-card">
              <template #header>
                <div class="notification-header">
                  <span>{{ notification.title }}</span>
                  <el-tag :type="notification.type" size="small">{{ notification.category }}</el-tag>
                </div>
              </template>
              <p>{{ notification.content }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight,
  ArrowDown,
  HomeFilled,
  SetUp,
  Box,
  Notebook,
  Link,
  Setting,
  Search,
  Bell,
  UserFilled,
  User,
  SwitchButton,
  Moon,
  Sunny,
  Expand,
  Fold,
  Connection,
  EditPen,
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

// 侧边栏折叠
const isCollapse = ref(false)
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 主题切换
const isDarkMode = computed(() => appStore.isDarkMode)
const toggleTheme = () => {
  appStore.toggleTheme()
  document.documentElement.classList.toggle('dark', isDarkMode.value)
}

// 搜索
const searchQuery = ref('')

// 标签页
const activeTab = ref(route.path)
const tabs = computed(() => appStore.visitedViews)
const cachedViews = computed(() => appStore.cachedViews)

watch(() => route.path, (newPath) => {
  activeTab.value = newPath
  appStore.addView({
    title: route.meta?.title as string || '未命名',
    path: newPath,
    name: route.name as string,
  })
})

const removeTab = (targetPath: string) => {
  appStore.removeView(targetPath)
  if (activeTab.value === targetPath) {
    const lastTab = tabs.value[tabs.value.length - 1]
    if (lastTab) {
      router.push(lastTab.path)
    }
  }
}

const handleTabClick = (tab: any) => {
  router.push(tab.props.name)
}

// 通知
const notificationDrawer = ref(false)
const notifications = ref([
  {
    title: '流水线执行完成',
    content: 'RNA-seq 分析流水线已成功完成',
    type: 'success',
    category: '执行',
    time: '10分钟前',
  },
  {
    title: 'Conda 环境创建成功',
    content: '环境 "rnaseq-env" 已创建',
    type: 'success',
    category: '环境',
    time: '1小时前',
  },
  {
    title: '系统警告',
    content: '磁盘空间使用率超过 80%',
    type: 'warning',
    category: '系统',
    time: '2小时前',
  },
])

const showNotifications = () => {
  notificationDrawer.value = true
}

// 用户下拉菜单命令处理
const handleCommand = async (command: string) => {
  if (command === 'logout') {
    await appStore.logout()
    router.push({ name: 'Login' })
  } else if (command === 'profile') {
    router.push({ name: 'Settings' })
  } else if (command === 'settings') {
    router.push({ name: 'Settings' })
  }
}

onMounted(async () => {
  // 初始化主题
  document.documentElement.classList.toggle('dark', isDarkMode.value)
  
  // 加载用户信息
  if (appStore.token) {
    try {
      await appStore.fetchUserInfo()
    } catch {
      // token 无效时忽略，由路由守卫处理跳转
    }
  }
  
  // 添加当前路由到标签页
  appStore.addView({
    title: route.meta?.title as string || 'Dashboard',
    path: route.path,
    name: route.name as string,
  })
})
</script>

<style scoped lang="scss">
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
  color: var(--el-text-color-primary);

  .main-layout {
    height: 100%;
  }

  .sidebar {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    color: #fff;
    transition: width 0.3s;
    display: flex;
    flex-direction: column;

    .logo {
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      .logo-icon {
        font-size: 28px;
        color: #409eff;
        margin-right: 12px;
      }

      .logo-text {
        font-size: 20px;
        font-weight: 600;
        background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        white-space: nowrap;
      }
    }

    .sidebar-menu {
      flex: 1;
      border-right: none;
      background: transparent;

      :deep(.el-menu-item) {
        color: rgba(255, 255, 255, 0.7);
        margin: 4px 8px;
        border-radius: 8px;

        &:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }

        &.is-active {
          background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
          color: #fff;
        }

        .el-icon {
          font-size: 18px;
        }
      }
    }

    .sidebar-footer {
      padding: 16px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);

      .collapse-btn {
        color: rgba(255, 255, 255, 0.7);
        width: 100%;

        &:hover {
          color: #fff;
          background: rgba(255, 255, 255, 0.1);
        }
      }
    }
  }

  .content-container {
    background-color: var(--el-bg-color-page);
  }

  .app-header {
    height: 64px;
    background-color: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-light);
    display: flex;
    align-items: center;
    padding: 0 24px;

    .header-content {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-left {
        display: flex;
        align-items: center;
      }

      .header-right {
        display: flex;
        align-items: center;
        gap: 16px;

        .global-search {
          width: 280px;
        }

        .theme-btn {
          font-size: 18px;
        }

        .notification-badge {
          :deep(.el-badge__content) {
            background-color: #f56c6c;
          }
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          padding: 4px 8px;
          border-radius: 8px;
          transition: background-color 0.3s;

          &:hover {
            background-color: var(--el-fill-color-light);
          }

          .username {
            font-size: 14px;
            font-weight: 500;
          }
        }
      }
    }
  }

  .tabs-container {
    background-color: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-light);
    padding: 0 16px;

    :deep(.el-tabs__header) {
      margin: 0;
    }

    :deep(.el-tabs__nav) {
      border: none;
    }

    :deep(.el-tabs__item) {
      border: none;
      border-radius: 4px 4px 0 0;
      margin-right: 4px;

      &.is-active {
        background-color: var(--el-fill-color-light);
      }
    }
  }

  .app-main {
    flex: 1;
    padding: 20px;
    overflow: auto;
    background-color: var(--el-bg-color-page);
  }

  .app-footer {
    height: 40px;
    background-color: var(--el-bg-color);
    border-top: 1px solid var(--el-border-color-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

// 页面切换动画
.page-slide-enter-active,
.page-slide-leave-active {
  transition: all 0.3s ease;
}

.page-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 通知样式
.notification-list {
  padding: 16px;

  .notification-card {
    margin-bottom: 8px;

    .notification-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}

// 暗色模式
.dark-mode {
  .sidebar {
    background: linear-gradient(180deg, #0f0f1a 0%, #0a0a14 100%);
  }
}
</style>
