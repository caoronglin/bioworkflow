<template>
  <div
    :class="[
      'base-input-wrapper',
      `base-input-wrapper--${size}`,
      {
        'base-input-wrapper--error': error,
        'base-input-wrapper--disabled': disabled,
        'base-input-wrapper--prefix': $slots.prefix || prefixIcon,
        'base-input-wrapper--suffix': $slots.suffix || showClear || showPassword,
      }
    ]"
  >
    <!-- 标签 -->
    <label v-if="label" :for="inputId" class="base-input__label">
      {{ label }}
      <span v-if="required" class="base-input__required">*</span>
    </label>

    <!-- 输入框容器 -->
    <div class="base-input">
      <!-- 前缀图标 -->
      <span v-if="$slots.prefix || prefixIcon" class="base-input__prefix">
        <slot name="prefix">
          <el-icon v-if="prefixIcon">
            <component :is="prefixIcon" />
          </el-icon>
        </slot>
      </span>

      <!-- 输入框 -->
      <input
        :id="inputId"
        ref="inputRef"
        :type="computedType"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :maxlength="maxlength"
        :minlength="minlength"
        :autocomplete="autocomplete"
        class="base-input__inner"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />

      <!-- 后缀图标 -->
      <span v-if="$slots.suffix || showClear || showPassword" class="base-input__suffix">
        <slot name="suffix">
          <el-icon
            v-if="showClear && modelValue"
            class="base-input__clear"
            @click="handleClear"
          >
            <CircleClose />
          </el-icon>
          <el-icon
            v-else-if="showPassword"
            class="base-input__password"
            @click="togglePasswordVisible"
          >
            <component :is="isPasswordVisible ? View : Hide" />
          </el-icon>
        </slot>
      </span>
    </div>

    <!-- 错误提示 -->
    <transition name="fade">
      <div v-if="error" class="base-input__error">
        {{ error }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, useId } from 'vue'
import { CircleClose, View, Hide } from '@element-plus/icons-vue'
import type { Component } from 'vue'

/**
 * BaseInput 基础输入框组件
 * 
 * 统一的输入框样式，支持多种功能和验证
 * 基于设计系统构建，支持主题切换
 * 
 * @version 2.0.0
 * @author BioWorkflow Team
 */

// Props 定义
interface Props {
  /** 绑定值 */
  modelValue?: string | number
  /** 输入框类型 */
  type?: 'text' | 'password' | 'number' | 'email' | 'tel' | 'url'
  /** 输入框尺寸 */
  size?: 'small' | 'medium' | 'large'
  /** 标签文本 */
  label?: string
  /** 占位符 */
  placeholder?: string
  /** 前缀图标 */
  prefixIcon?: Component
  /** 是否必填 */
  required?: boolean
  /** 是否禁用 */
  disabled?: boolean
  /** 是否只读 */
  readonly?: boolean
  /** 最大长度 */
  maxlength?: number
  /** 最小长度 */
  minlength?: number
  /** 自动完成 */
  autocomplete?: 'on' | 'off'
  /** 是否显示清除按钮 */
  showClear?: boolean
  /** 是否显示密码切换 */
  showPassword?: boolean
  /** 错误信息 */
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  size: 'medium',
  label: '',
  placeholder: '请输入...',
  required: false,
  disabled: false,
  readonly: false,
  showClear: false,
  showPassword: false,
  autocomplete: 'off',
  error: '',
})

// Emits 定义
const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
}>()

// 生成唯一 ID
const inputId = useId()

// 输入框引用
const inputRef = ref<HTMLInputElement>()

// 密码可见性
const isPasswordVisible = ref(false)

// 计算实际类型
const computedType = computed(() => {
  if (props.type === 'password' && isPasswordVisible.value) {
    return 'text'
  }
  return props.type
})

// 输入处理
function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

// 焦点处理
function handleFocus(event: FocusEvent) {
  emit('focus', event)
}

// 失焦处理
function handleBlur(event: FocusEvent) {
  emit('blur', event)
}

// 清除处理
function handleClear() {
  emit('update:modelValue', '')
  inputRef.value?.focus()
}

// 切换密码可见性
function togglePasswordVisible() {
  isPasswordVisible.value = !isPasswordVisible.value
}

// 暴露方法
defineExpose({
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
  select: () => inputRef.value?.select(),
})
</script>

<style scoped lang="scss">
@import '../../styles/variables.scss';

.base-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);

  // 尺寸
  &--small {
    .base-input {
      height: 28px;

      &__inner {
        font-size: var(--font-size-sm);
      }

      &__prefix,
      &__suffix {
        font-size: 14px;
      }
    }
  }

  &--medium {
    .base-input {
      height: 36px;

      &__inner {
        font-size: var(--font-size-base);
      }

      &__prefix,
      &__suffix {
        font-size: 16px;
      }
    }
  }

  &--large {
    .base-input {
      height: 44px;

      &__inner {
        font-size: var(--font-size-md);
      }

      &__prefix,
      &__suffix {
        font-size: 18px;
      }
    }
  }

  // 错误状态
  &--error {
    .base-input {
      &__inner {
        border-color: var(--color-danger);

        &:focus {
          border-color: var(--color-danger);
          box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.1);
        }
      }
    }

    .base-input__label {
      color: var(--color-danger);
    }
  }

  // 禁用状态
  &--disabled {
    .base-input {
      &__inner {
        background-color: var(--fill-color-light);
        color: var(--text-color-disabled);
        cursor: not-allowed;
      }

      &__prefix,
      &__suffix {
        color: var(--text-color-disabled);
      }
    }
  }
}

.base-input__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-color-regular);
  line-height: var(--line-height-normal);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.base-input__required {
  color: var(--color-danger);
}

.base-input {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-base);
  background-color: var(--bg-color);
  transition: all var(--duration-fast) var(--ease-in-out);

  &:hover:not(.base-input-wrapper--disabled) {
    border-color: var(--color-primary);
  }

  &:has(.base-input__inner:focus) {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
  }

  &__prefix,
  &__suffix {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-color-secondary);
    flex-shrink: 0;
    transition: color var(--duration-fast) var(--ease-in-out);
  }

  &__prefix {
    padding-left: var(--spacing-sm);
    padding-right: var(--spacing-xs);
  }

  &__suffix {
    padding-right: var(--spacing-sm);
    padding-left: var(--spacing-xs);
  }

  &__inner {
    flex: 1;
    width: 100%;
    min-width: 0;
    height: 100%;
    padding: 0 var(--spacing-md);
    border: none;
    outline: none;
    background: transparent;
    color: var(--text-color-primary);
    font-family: var(--font-family-base);
    transition: all var(--duration-fast) var(--ease-in-out);

    &::placeholder {
      color: var(--text-color-placeholder);
    }

    &:disabled {
      cursor: not-allowed;
    }
  }

  &__clear,
  &__password {
    cursor: pointer;
    transition: color var(--duration-fast) var(--ease-in-out);

    &:hover {
      color: var(--color-primary);
    }
  }
}

.base-input__error {
  font-size: var(--font-size-xs);
  color: var(--color-danger);
  line-height: var(--line-height-normal);
  padding-left: var(--spacing-xs);
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-in-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 暗色模式适配
html.dark {
  .base-input-wrapper {
    &--disabled {
      .base-input {
        &__inner {
          background-color: var(--fill-color-dark);
        }
      }
    }
  }
}
</style>
