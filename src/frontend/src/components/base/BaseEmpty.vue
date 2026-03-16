<template>
  <div :class="['base-empty', `base-empty--${size}`]">
    <!-- 图标 -->
    <div class="base-empty__icon">
      <slot name="icon">
        <svg
          viewBox="0 0 64 64"
          :width="iconSize"
          :height="iconSize"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="2" opacity="0.3" />
          <path
            d="M20 32L28 40L44 24"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <circle cx="32" cy="20" r="4" fill="currentColor" opacity="0.5" />
        </svg>
      </slot>
    </div>

    <!-- 描述文本 -->
    <div v-if="description || $slots.default" class="base-empty__description">
      <slot>{{ description }}</slot>
    </div>

    <!-- 操作按钮 -->
    <div v-if="$slots.extra" class="base-empty__extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * BaseEmpty 空状态组件
 * 
 * 统一的空状态展示，支持自定义图标、描述和操作
 * 基于设计系统构建，支持主题切换
 * 
 * @version 2.0.0
 * @author BioWorkflow Team
 */

// Props 定义
interface Props {
  /** 描述文本 */
  description?: string
  /** 组件尺寸 */
  size?: 'small' | 'medium' | 'large'
  /** 图标大小（像素） */
  iconSize?: number
}

withDefaults(defineProps<Props>(), {
  description: '暂无数据',
  size: 'medium',
  iconSize: 64,
})

// Slots 定义
defineSlots<{
  /** 自定义图标 */
  icon?: () => void
  /** 自定义描述 */
  default?: () => string
  /** 额外操作区 */
  extra?: () => void
}>()
</script>

<style scoped lang="scss">
@import '../../styles/variables.scss';

.base-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  text-align: center;
  color: var(--text-color-secondary);

  // 尺寸
  &--small {
    padding: var(--spacing-lg);

    .base-empty__description {
      font-size: var(--font-size-sm);
      margin-top: var(--spacing-sm);
    }

    .base-empty__extra {
      margin-top: var(--spacing-sm);
    }
  }

  &--medium {
    padding: var(--spacing-2xl);

    .base-empty__description {
      font-size: var(--font-size-base);
      margin-top: var(--spacing-md);
    }

    .base-empty__extra {
      margin-top: var(--spacing-md);
    }
  }

  &--large {
    padding: var(--spacing-4xl);

    .base-empty__description {
      font-size: var(--font-size-lg);
      margin-top: var(--spacing-lg);
    }

    .base-empty__extra {
      margin-top: var(--spacing-lg);
      display: flex;
      gap: var(--spacing-md);
    }
  }

  // 图标
  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-color-placeholder);
    opacity: 0.5;
    transition: color var(--duration-normal) var(--ease-in-out);
  }

  // 描述
  &__description {
    font-size: var(--font-size-base);
    color: var(--text-color-secondary);
    line-height: var(--line-height-relaxed);
    max-width: 400px;
  }

  // 额外操作
  &__extra {
    display: flex;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
  }
}

// 暗色模式适配
html.dark {
  .base-empty {
    &__icon {
      opacity: 0.4;
    }

    &__description {
      color: var(--text-color-secondary);
    }
  }
}
</style>
