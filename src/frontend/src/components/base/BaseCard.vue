<template>
  <div
    :class="[
      'base-card',
      `base-card--${size}`,
      {
        'base-card--hoverable': hoverable,
        'base-card--shadow': shadow,
        'base-card--bordered': bordered,
      }
    ]"
    :style="customStyle"
  >
    <!-- 卡片头部 -->
    <div v-if="$slots.header || title" class="base-card__header">
      <div class="base-card__header-content">
        <slot name="header">
          <h3 v-if="title" class="base-card__title">
            {{ title }}
          </h3>
        </slot>
      </div>
      <div v-if="$slots['header-actions']" class="base-card__header-actions">
        <slot name="header-actions" />
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="base-card__body">
      <slot>
        <p v-if="content" class="base-card__content">{{ content }}</p>
      </slot>
    </div>

    <!-- 卡片底部 -->
    <div v-if="$slots.footer" class="base-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * BaseCard 基础卡片组件
 * 
 * 统一的卡片容器，支持头部、内容和底部区域
 * 基于设计系统构建，支持主题切换
 * 
 * @version 2.0.0
 * @author BioWorkflow Team
 */

// Props 定义
interface Props {
  /** 卡片标题 */
  title?: string
  /** 卡片内容（简单文本） */
  content?: string
  /** 卡片尺寸 */
  size?: 'small' | 'medium' | 'large'
  /** 是否可悬停 */
  hoverable?: boolean
  /** 是否显示阴影 */
  shadow?: boolean
  /** 是否显示边框 */
  bordered?: boolean
  /** 自定义样式 */
  customStyle?: Record<string, string>
}

withDefaults(defineProps<Props>(), {
  title: '',
  content: '',
  size: 'medium',
  hoverable: false,
  shadow: true,
  bordered: false,
  customStyle: () => ({}),
})

// Slots 定义
defineSlots<{
  /** 卡片头部 */
  header?: () => void
  /** 卡片头部操作区 */
  'header-actions'?: () => void
  /** 卡片内容 */
  default?: () => void
  /** 卡片底部 */
  footer?: () => void
}>()
</script>

<style scoped lang="scss">
@import '../../styles/variables.scss';

.base-card {
  // 基础样式
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  border-radius: var(--radius-lg);
  transition: all var(--duration-normal) var(--ease-in-out);
  overflow: hidden;
  
  // 尺寸
  &--small {
    .base-card__header {
      padding: var(--spacing-sm) var(--spacing-md);
    }
    
    .base-card__body {
      padding: var(--spacing-md);
    }
    
    .base-card__footer {
      padding: var(--spacing-sm) var(--spacing-md);
    }
    
    .base-card__title {
      font-size: var(--font-size-base);
    }
  }
  
  &--medium {
    .base-card__header {
      padding: var(--spacing-md) var(--spacing-lg);
    }
    
    .base-card__body {
      padding: var(--spacing-lg);
    }
    
    .base-card__footer {
      padding: var(--spacing-md) var(--spacing-lg);
    }
    
    .base-card__title {
      font-size: var(--font-size-lg);
    }
  }
  
  &--large {
    .base-card__header {
      padding: var(--spacing-lg) var(--spacing-xl);
    }
    
    .base-card__body {
      padding: var(--spacing-xl);
    }
    
    .base-card__footer {
      padding: var(--spacing-lg) var(--spacing-xl);
    }
    
    .base-card__title {
      font-size: var(--font-size-xl);
    }
  }
  
  // 阴影
  &--shadow {
    box-shadow: var(--shadow-base);
    
    &.base-card--hoverable:hover {
      box-shadow: var(--shadow-lg);
      transform: translateY(-4px);
    }
  }
  
  // 边框
  &--bordered {
    border: 1px solid var(--border-color-light);
  }
  
  // 可悬停
  &--hoverable {
    cursor: pointer;
    
    &:hover {
      box-shadow: var(--shadow-lg);
    }
  }
  
  // 头部
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-color-lighter);
    
    &-content {
      flex: 1;
      min-width: 0;
    }
    
    &-actions {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      flex-shrink: 0;
    }
  }
  
  // 标题
  &__title {
    margin: 0;
    font-weight: var(--font-weight-semibold);
    color: var(--text-color-primary);
    line-height: var(--line-height-tight);
  }
  
  // 内容区
  &__body {
    flex: 1;
    padding-top: var(--spacing-md);
  }
  
  &__content {
    margin: 0;
    color: var(--text-color-regular);
    line-height: var(--line-height-relaxed);
  }
  
  // 底部
  &__footer {
    padding-top: var(--spacing-md);
    margin-top: auto;
    border-top: 1px solid var(--border-color-lighter);
  }
}

// 暗色模式适配
html.dark {
  .base-card {
    background-color: var(--bg-color-overlay);
    
    &--bordered {
      border-color: var(--border-color);
    }
    
    &__header,
    &__footer {
      border-color: var(--border-color);
    }
  }
}
</style>
