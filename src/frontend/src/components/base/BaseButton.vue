<template>
  <button
    :class="[
      'base-button',
      `base-button--${type}`,
      `base-button--${size}`,
      `base-button--${variant}`,
      {
        'base-button--loading': loading,
        'base-button--disabled': disabled,
        'base-button--block': block,
        'base-button--icon-only': iconOnly,
      }
    ]"
    :disabled="disabled || loading"
    :type="nativeType"
    @click="handleClick"
  >
    <!-- 加载图标 -->
    <span v-if="loading" class="base-button__loading">
      <svg class="loading-spinner" viewBox="0 0 50 50">
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke="currentColor"
          stroke-width="4"
          stroke-dasharray="80, 200"
          stroke-linecap="round"
        />
      </svg>
    </span>

    <!-- 图标 -->
    <el-icon v-else-if="icon" class="base-button__icon">
      <component :is="icon" />
    </el-icon>

    <!-- 文本 -->
    <span v-if="$slots.default || text" class="base-button__text">
      <slot>{{ text }}</slot>
    </span>
  </button>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

/**
 * BaseButton 基础按钮组件
 * 
 * 统一的按钮样式，支持多种类型、尺寸和变体
 * 基于设计系统构建，支持主题切换
 * 
 * @version 2.0.0
 * @author BioWorkflow Team
 */

// Props 定义
interface Props {
  /** 按钮类型 */
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  /** 按钮尺寸 */
  size?: 'small' | 'medium' | 'large'
  /** 按钮变体 */
  variant?: 'solid' | 'outline' | 'ghost' | 'text'
  /** 原生按钮类型 */
  nativeType?: 'button' | 'submit' | 'reset'
  /** 按钮文本 */
  text?: string
  /** 按钮图标 */
  icon?: Component
  /** 是否禁用 */
  disabled?: boolean
  /** 是否加载中 */
  loading?: boolean
  /** 是否块级按钮 */
  block?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  size: 'medium',
  variant: 'solid',
  nativeType: 'button',
  text: '',
  disabled: false,
  loading: false,
  block: false,
})

// 计算是否仅为图标按钮
const iconOnly = computed(() => {
  return !!(props.icon && !props.text && !slots.default)
})

// Emits 定义
const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// 点击处理
function handleClick(event: MouseEvent) {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}

// Slots 定义
const slots = defineSlots<{
  default?: () => string
}>()
</script>

<style scoped lang="scss">
@import '../../styles/variables.scss';

.base-button {
  // 基础样式
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  font-family: var(--font-family-base);
  font-weight: var(--font-weight-medium);
  border: none;
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-in-out);
  white-space: nowrap;
  user-select: none;
  -webkit-user-select: none;
  
  // 尺寸
  &--small {
    height: 28px;
    padding: 0 var(--spacing-sm);
    font-size: var(--font-size-sm);
    
    &.base-button--icon-only {
      width: 28px;
      padding: 0;
    }
    
    .base-button__icon {
      font-size: 14px;
    }
  }
  
  &--medium {
    height: 36px;
    padding: 0 var(--spacing-md);
    font-size: var(--font-size-base);
    
    &.base-button--icon-only {
      width: 36px;
      padding: 0;
    }
    
    .base-button__icon {
      font-size: 16px;
    }
  }
  
  &--large {
    height: 44px;
    padding: 0 var(--spacing-lg);
    font-size: var(--font-size-md);
    
    &.base-button--icon-only {
      width: 44px;
      padding: 0;
    }
    
    .base-button__icon {
      font-size: 18px;
    }
  }
  
  // 类型和变体
  &--primary {
    &.base-button--solid {
      background: var(--gradient-primary);
      color: #ffffff;
      box-shadow: var(--shadow-primary);
      
      &:hover:not(:disabled) {
        box-shadow: 0 6px 20px 0 rgba(64, 158, 255, 0.4);
        transform: translateY(-1px);
      }
      
      &:active:not(:disabled) {
        transform: translateY(0);
        box-shadow: 0 2px 8px 0 rgba(64, 158, 255, 0.3);
      }
    }
    
    &.base-button--outline {
      background: transparent;
      color: var(--color-primary);
      border: 2px solid var(--color-primary);
      
      &:hover:not(:disabled) {
        background: var(--color-primary-light-9);
      }
      
      &:active:not(:disabled) {
        background: var(--color-primary-light-8);
      }
    }
    
    &.base-button--ghost {
      background: rgba(64, 158, 255, 0.1);
      color: var(--color-primary);
      
      &:hover:not(:disabled) {
        background: rgba(64, 158, 255, 0.2);
      }
      
      &:active:not(:disabled) {
        background: rgba(64, 158, 255, 0.15);
      }
    }
    
    &.base-button--text {
      background: transparent;
      color: var(--color-primary);
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
      
      &:hover:not(:disabled) {
        background: var(--color-primary-light-9);
      }
    }
  }
  
  &--success {
    &.base-button--solid {
      background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
      color: #ffffff;
      box-shadow: var(--shadow-success);
      
      &:hover:not(:disabled) {
        box-shadow: 0 6px 20px 0 rgba(103, 194, 58, 0.4);
      }
    }
    
    &.base-button--outline {
      background: transparent;
      color: var(--color-success);
      border: 2px solid var(--color-success);
      
      &:hover:not(:disabled) {
        background: var(--color-success-lighter);
      }
    }
    
    &.base-button--ghost {
      background: rgba(103, 194, 58, 0.1);
      color: var(--color-success);
      
      &:hover:not(:disabled) {
        background: rgba(103, 194, 58, 0.2);
      }
    }
    
    &.base-button--text {
      background: transparent;
      color: var(--color-success);
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
      
      &:hover:not(:disabled) {
        background: var(--color-success-lighter);
      }
    }
  }
  
  &--warning {
    &.base-button--solid {
      background: linear-gradient(135deg, #e6a23c 0%, #b88230 100%);
      color: #ffffff;
      box-shadow: var(--shadow-warning);
      
      &:hover:not(:disabled) {
        box-shadow: 0 6px 20px 0 rgba(230, 162, 60, 0.4);
      }
    }
    
    &.base-button--outline {
      background: transparent;
      color: var(--color-warning);
      border: 2px solid var(--color-warning);
      
      &:hover:not(:disabled) {
        background: var(--color-warning-lighter);
      }
    }
    
    &.base-button--ghost {
      background: rgba(230, 162, 60, 0.1);
      color: var(--color-warning);
      
      &:hover:not(:disabled) {
        background: rgba(230, 162, 60, 0.2);
      }
    }
    
    &.base-button--text {
      background: transparent;
      color: var(--color-warning);
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
      
      &:hover:not(:disabled) {
        background: var(--color-warning-lighter);
      }
    }
  }
  
  &--danger {
    &.base-button--solid {
      background: linear-gradient(135deg, #f56c6c 0%, #c45656 100%);
      color: #ffffff;
      box-shadow: var(--shadow-danger);
      
      &:hover:not(:disabled) {
        box-shadow: 0 6px 20px 0 rgba(245, 108, 108, 0.4);
      }
    }
    
    &.base-button--outline {
      background: transparent;
      color: var(--color-danger);
      border: 2px solid var(--color-danger);
      
      &:hover:not(:disabled) {
        background: var(--color-danger-lighter);
      }
    }
    
    &.base-button--ghost {
      background: rgba(245, 108, 108, 0.1);
      color: var(--color-danger);
      
      &:hover:not(:disabled) {
        background: rgba(245, 108, 108, 0.2);
      }
    }
    
    &.base-button--text {
      background: transparent;
      color: var(--color-danger);
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
      
      &:hover:not(:disabled) {
        background: var(--color-danger-lighter);
      }
    }
  }
  
  &--info {
    &.base-button--solid {
      background: linear-gradient(135deg, #909399 0%, #73767a 100%);
      color: #ffffff;
      
      &:hover:not(:disabled) {
        opacity: 0.9;
      }
    }
    
    &.base-button--outline {
      background: transparent;
      color: var(--color-info);
      border: 2px solid var(--color-info);
      
      &:hover:not(:disabled) {
        background: var(--color-info-lighter);
      }
    }
    
    &.base-button--ghost {
      background: rgba(144, 147, 153, 0.1);
      color: var(--color-info);
      
      &:hover:not(:disabled) {
        background: rgba(144, 147, 153, 0.2);
      }
    }
    
    &.base-button--text {
      background: transparent;
      color: var(--color-info);
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
      
      &:hover:not(:disabled) {
        background: var(--color-info-lighter);
      }
    }
  }
  
  &--default {
    &.base-button--solid {
      background: var(--bg-color);
      color: var(--text-color-primary);
      border: 1px solid var(--border-color);
      box-shadow: var(--shadow-sm);
      
      &:hover:not(:disabled) {
        border-color: var(--color-primary);
        color: var(--color-primary);
        box-shadow: var(--shadow-md);
      }
      
      &:active:not(:disabled) {
        background: var(--fill-color-light);
      }
    }
    
    &.base-button--outline {
      background: transparent;
      color: var(--text-color-primary);
      border: 2px solid var(--border-color);
      
      &:hover:not(:disabled) {
        border-color: var(--color-primary);
        color: var(--color-primary);
      }
    }
    
    &.base-button--ghost {
      background: var(--fill-color-light);
      color: var(--text-color-primary);
      
      &:hover:not(:disabled) {
        background: var(--fill-color);
      }
    }
    
    &.base-button--text {
      background: transparent;
      color: var(--text-color-regular);
      padding-left: var(--spacing-sm);
      padding-right: var(--spacing-sm);
      
      &:hover:not(:disabled) {
        background: var(--fill-color-light);
        color: var(--text-color-primary);
      }
    }
  }
  
  // 块级按钮
  &--block {
    display: flex;
    width: 100%;
  }
  
  // 禁用状态
  &--disabled,
  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
    
    &:hover {
      transform: none;
      box-shadow: none;
    }
  }
  
  // 加载状态
  &--loading {
    cursor: wait;
    
    .base-button__text {
      opacity: 0.7;
    }
  }
  
  // 内部元素
  &__loading {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    animation: spin 1s linear infinite;
    
    .loading-spinner {
      width: 1em;
      height: 1em;
      
      circle {
        animation: loading-circle 1.5s cubic-bezier(0.35, 0, 0.25, 1) infinite;
      }
    }
  }
  
  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  
  &__text {
    display: inline-flex;
    align-items: center;
  }
}

// 动画
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes loading-circle {
  0% {
    stroke-dasharray: 1, 200;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 200;
    stroke-dashoffset: -35px;
  }
  100% {
    stroke-dasharray: 90, 200;
    stroke-dashoffset: -124px;
  }
}

// 暗色模式适配
html.dark {
  .base-button {
    &--primary {
      &.base-button--outline {
        &:hover:not(:disabled) {
          background: rgba(64, 158, 255, 0.1);
        }
      }
      
      &.base-button--text {
        &:hover:not(:disabled) {
          background: rgba(64, 158, 255, 0.1);
        }
      }
    }
    
    &--default {
      &.base-button--solid {
        background: var(--bg-color-overlay);
      }
    }
  }
}
</style>
