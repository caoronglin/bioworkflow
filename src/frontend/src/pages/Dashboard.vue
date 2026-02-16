<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div
        v-for="stat in statsList"
        :key="stat.key"
        class="stat-card"
        :class="stat.color"
      >
        <div class="stat-header">
          <div class="stat-icon" :style="{ backgroundColor: stat.iconBg }">
            <el-icon :size="24" :color="stat.iconColor">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <span class="stat-title">{{ stat.title }}</span>
        </div>
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-change" :class="stat.trend > 0 ? 'positive' : 'negative'">
          <el-icon>
            <component :is="stat.trend > 0 ? ArrowUp : ArrowDown" />
          </el-icon>
          <span>{{ Math.abs(stat.trend) }}%</span>
          <span class="stat-period">较上周</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <el-icon><TrendCharts /></el-icon>
                <span>执行统计</span>
              </div>
              <el-radio-group v-model="chartPeriod" size="small">
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
                <el-radio-button label="year">全年</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="executionChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <el-icon><PieChart /></el-icon>
                <span>状态分布</span>
              </div>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="statusChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动和快速操作 -->
    <el-row :gutter="20" class="bottom-row">
      <el-col :xs="24" :lg="14">
        <el-card class="activity-card" shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <el-icon><Clock /></el-icon>
                <span>最近活动</span>
              </div>
              <el-button link type="primary" @click="refreshActivities">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <el-timeline v-if="recentActivities.length > 0">
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :type="activity.type"
              :timestamp="activity.time"
              :icon="getActivityIcon(activity.category)"
            >
              <div class="activity-item">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-desc">{{ activity.description }}</div>
                <el-tag :type="activity.statusType" size="small">
                  {{ activity.status }}
                </el-tag>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无活动记录" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card class="quick-actions-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <el-icon><Operation /></el-icon>
                <span>快速操作</span>
              </div>
            </div>
          </template>
          <div class="quick-actions">
            <div
              v-for="action in quickActions"
              :key="action.key"
              class="action-item"
              @click="handleAction(action)"
            >
              <div class="action-icon" :style="{ background: action.gradient }">
                <el-icon :size="24" color="#fff">
                  <component :is="action.icon" />
                </el-icon>
              </div>
              <div class="action-info">
                <div class="action-title">{{ action.title }}</div>
                <div class="action-desc">{{ action.description }}</div>
              </div>
              <el-icon class="action-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import {
  SetUp,
  Box,
  Document,
  Link,
  TrendCharts,
  Clock,
  Operation,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Refresh,
  Plus,
  Search,
  Setting,
  CircleCheck,
  Warning,
  InfoFilled,
  PieChart,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { pipelinesAPI, condaAPI, knowledgeAPI, mcpAPI } from '@/api'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const router = useRouter()
const loading = ref(false)
const chartPeriod = ref('week')

// 统计数据
const stats = ref({
  pipelines: 12,
  condaEnvs: 8,
  documents: 156,
  mcpServices: 5,
})

const statsList = computed(() => [
  {
    key: 'pipelines',
    title: '活跃流水线',
    value: stats.value.pipelines,
    icon: SetUp,
    iconBg: 'rgba(64, 158, 255, 0.1)',
    iconColor: '#409eff',
    color: 'blue',
    trend: 12.5,
  },
  {
    key: 'condaEnvs',
    title: 'Conda 环境',
    value: stats.value.condaEnvs,
    icon: Box,
    iconBg: 'rgba(103, 194, 58, 0.1)',
    iconColor: '#67c23a',
    color: 'green',
    trend: 8.2,
  },
  {
    key: 'documents',
    title: '知识库文档',
    value: stats.value.documents,
    icon: Document,
    iconBg: 'rgba(230, 162, 60, 0.1)',
    iconColor: '#e6a23c',
    color: 'orange',
    trend: -3.1,
  },
  {
    key: 'mcpServices',
    title: 'MCP 服务',
    value: stats.value.mcpServices,
    icon: Link,
    iconBg: 'rgba(144, 147, 153, 0.1)',
    iconColor: '#909399',
    color: 'gray',
    trend: 0,
  },
])

// 执行统计图表配置
const executionChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
  },
  legend: {
    data: ['成功', '失败', '运行中'],
    bottom: 0,
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '10%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    axisLine: { lineStyle: { color: '#909399' } },
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: '#909399' } },
    splitLine: { lineStyle: { color: '#e4e7ed' } },
  },
  series: [
    {
      name: '成功',
      type: 'line',
      smooth: true,
      data: [12, 15, 8, 20, 18, 25, 22],
      itemStyle: { color: '#67c23a' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.05)' },
          ],
        },
      },
    },
    {
      name: '失败',
      type: 'line',
      smooth: true,
      data: [2, 1, 3, 2, 1, 0, 1],
      itemStyle: { color: '#f56c6c' },
    },
    {
      name: '运行中',
      type: 'line',
      smooth: true,
      data: [5, 8, 6, 10, 12, 8, 15],
      itemStyle: { color: '#409eff' },
    },
  ],
}))

// 状态分布图表配置
const statusChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)',
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center',
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2,
      },
      label: {
        show: false,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold',
        },
      },
      data: [
        { value: 45, name: '已完成', itemStyle: { color: '#67c23a' } },
        { value: 12, name: '运行中', itemStyle: { color: '#409eff' } },
        { value: 8, name: '失败', itemStyle: { color: '#f56c6c' } },
        { value: 15, name: '待执行', itemStyle: { color: '#e6a23c' } },
      ],
    },
  ],
}))

// 最近活动
const recentActivities = ref([
  {
    id: '1',
    title: 'RNA-seq 分析流水线执行完成',
    description: '执行时间: 2小时15分钟 | 输出文件: 128个',
    time: '10分钟前',
    type: 'success',
    category: 'execution',
    status: '已完成',
    statusType: 'success',
  },
  {
    id: '2',
    title: '创建 Conda 环境: rnaseq-env',
    description: 'Python 3.10 | 包含包: 45个',
    time: '1小时前',
    type: 'primary',
    category: 'conda',
    status: '成功',
    statusType: 'success',
  },
  {
    id: '3',
    title: '知识库文档更新',
    description: '新增文档: 3个 | 更新文档: 12个',
    time: '2小时前',
    type: 'info',
    category: 'knowledge',
    status: '已同步',
    statusType: 'info',
  },
  {
    id: '4',
    title: '系统警告: 磁盘空间不足',
    description: '当前使用率: 85% | 建议清理临时文件',
    time: '3小时前',
    type: 'warning',
    category: 'system',
    status: '警告',
    statusType: 'warning',
  },
  {
    id: '5',
    title: 'MCP 服务注册成功',
    description: '服务名称: BioTools API | 版本: 2.1.0',
    time: '5小时前',
    type: 'success',
    category: 'mcp',
    status: '在线',
    statusType: 'success',
  },
])

// 快速操作
const quickActions = [
  {
    key: 'create-pipeline',
    title: '创建流水线',
    description: '快速创建新的 Snakemake 流水线',
    icon: Plus,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    route: '/pipelines',
  },
  {
    key: 'search-knowledge',
    title: '搜索知识库',
    description: '搜索文档、教程和最佳实践',
    icon: Search,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    route: '/knowledge',
  },
  {
    key: 'manage-conda',
    title: '管理环境',
    description: '创建、更新或删除 Conda 环境',
    icon: Box,
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    route: '/conda',
  },
  {
    key: 'system-settings',
    title: '系统设置',
    description: '配置系统参数和偏好设置',
    icon: Setting,
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    route: '/settings',
  },
]

// 获取活动图标
const getActivityIcon = (category: string) => {
  const iconMap: Record<string, any> = {
    execution: CircleCheck,
    conda: Box,
    knowledge: Document,
    system: Warning,
    mcp: Link,
  }
  return iconMap[category] || InfoFilled
}

// 处理快速操作
const handleAction = (action: any) => {
  if (action.route) {
    router.push(action.route)
  }
}

// 刷新活动
const refreshActivities = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.success('已刷新')
  }, 500)
}

// 加载统计数据
const loadStats = async () => {
  try {
    const [pipelinesRes, condaRes, knowledgeRes, mcpRes] = await Promise.allSettled([
      pipelinesAPI.list(),
      condaAPI.listEnvironments(),
      knowledgeAPI.listDocuments(),
      mcpAPI.listServices(),
    ])

    stats.value.pipelines = pipelinesRes.status === 'fulfilled' ? (pipelinesRes.value?.data?.length || 0) : 0
    stats.value.condaEnvs = condaRes.status === 'fulfilled' ? (condaRes.value?.data?.length || 0) : 0
    stats.value.documents = knowledgeRes.status === 'fulfilled' ? (knowledgeRes.value?.data?.length || 0) : 0
    stats.value.mcpServices = mcpRes.status === 'fulfilled' ? (mcpRes.value?.data?.length || 0) : 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 20px;

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;

    @media (max-width: 1200px) {
      grid-template-columns: repeat(2, 1fr);
    }

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  .stat-card {
    background: var(--el-bg-color);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.1);
    }

    .stat-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .stat-title {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        font-weight: 500;
      }
    }

    .stat-value {
      font-size: 36px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      margin-bottom: 12px;
      line-height: 1;
    }

    .stat-change {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 13px;
      font-weight: 500;

      &.positive {
        color: var(--el-color-success);
      }

      &.negative {
        color: var(--el-color-danger);
      }

      .stat-period {
        color: var(--el-text-color-secondary);
        font-weight: 400;
        margin-left: 4px;
      }
    }
  }

  .chart-row {
    margin-bottom: 24px;
  }

  .chart-card {
    border-radius: 16px;
    overflow: hidden;

    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-lighter);
    }

    :deep(.el-card__body) {
      padding: 20px;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        font-weight: 600;

        .el-icon {
          color: var(--el-color-primary);
        }
      }
    }

    .chart-container {
      height: 300px;

      .chart {
        width: 100%;
        height: 100%;
      }
    }
  }

  .bottom-row {
    .activity-card,
    .quick-actions-card {
      border-radius: 16px;
      overflow: hidden;

      :deep(.el-card__header) {
        padding: 16px 20px;
        border-bottom: 1px solid var(--el-border-color-lighter);
      }

      :deep(.el-card__body) {
        padding: 20px;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .header-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 16px;
          font-weight: 600;

          .el-icon {
            color: var(--el-color-primary);
          }
        }
      }
    }

    .activity-item {
      .activity-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }

      .activity-desc {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;
      }
    }

    .quick-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;

      .action-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid transparent;

        &:hover {
          background: var(--el-fill-color-light);
          border-color: var(--el-border-color);
          transform: translateX(4px);

          .action-arrow {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .action-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .action-info {
          flex: 1;

          .action-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }

          .action-desc {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }

        .action-arrow {
          opacity: 0;
          transform: translateX(-8px);
          transition: all 0.3s ease;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
}

// 暗色模式适配
html.dark {
  .dashboard {
    .stat-card {
      background: var(--el-bg-color-overlay);
    }
  }
}
</style>
