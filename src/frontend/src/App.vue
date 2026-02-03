<template>
  <div id="app" class="app-container">
    <el-container>
      <!-- 侧边栏导航 -->
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h2>BioWorkflow</h2>
        </div>
        <el-menu
          router
          :default-active="$route.path"
          class="el-menu-vertical-demo"
        >
          <el-menu-item index="/">
            <i class="el-icon-home"></i>
            <span>Dashboard</span>
          </el-menu-item>
          <el-menu-item index="/pipelines">
            <i class="el-icon-document-copy"></i>
            <span>流水线</span>
          </el-menu-item>
          <el-menu-item index="/conda">
            <i class="el-icon-box"></i>
            <span>Conda 环境</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <i class="el-icon-notebook-2"></i>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/mcp">
            <i class="el-icon-connection"></i>
            <span>MCP 服务</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <i class="el-icon-setting"></i>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主容器 -->
      <el-container>
        <!-- 顶部栏 -->
        <el-header class="app-header">
          <div class="header-content">
            <div class="breadcrumb">
              <el-breadcrumb :separator-icon="ArrowRight">
                <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
                <el-breadcrumb-item>{{ $route.meta?.title || '页面' }}</el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            <div class="user-menu">
              <el-dropdown>
                <span class="el-dropdown-link">
                  用户 <i class="el-icon-arrow-down"></i>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item>个人信息</el-dropdown-item>
                    <el-dropdown-item>设置</el-dropdown-item>
                    <el-dropdown-divider></el-dropdown-divider>
                    <el-dropdown-item>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="$route.path" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight } from '@element-plus/icons-vue'
</script>

<style scoped lang="scss">
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;

  .sidebar {
    background-color: #545c64;
    color: #fff;
    border-right: 1px solid #dcdfe6;

    .logo {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid #dcdfe6;
      
      h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
      }
    }
  }

  .app-header {
    background-color: #fff;
    border-bottom: 1px solid #dcdfe6;
    display: flex;
    align-items: center;

    .header-content {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 20px;

      .breadcrumb {
        flex: 1;
      }

      .user-menu {
        cursor: pointer;
      }
    }
  }

  .app-main {
    flex: 1;
    background-color: #f5f7fa;
    overflow: auto;
  }
}

:deep(.el-menu) {
  border-right: none;
  background-color: #545c64;
  color: #fff;

  .el-menu-item {
    background-color: #545c64;
    color: #fff;

    &:hover {
      background-color: #667070 !important;
    }

    &.is-active {
      background-color: #409eff !important;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
