/**
 * BioWorkflow Design Tokens - TypeScript 类型化设计令牌
 * 
 * 提供类型安全的设计令牌访问，支持在 JavaScript/TypeScript 中使用
 * 
 * @version 2.0.0
 * @author BioWorkflow Team
 */

// ============================================================================
// 类型定义
// ============================================================================

/** 主题颜色类型 */
export type ThemeColor =
  | 'primary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'

/** 中性色类型 */
export type NeutralColor =
  | 'neutral-0'
  | 'neutral-50'
  | 'neutral-100'
  | 'neutral-200'
  | 'neutral-300'
  | 'neutral-400'
  | 'neutral-500'
  | 'neutral-600'
  | 'neutral-700'
  | 'neutral-800'
  | 'neutral-900'
  | 'neutral-950'

/** 间距类型 */
export type SpacingSize =
  | 'xs'
  | 'sm'
  | 'md'
  | 'lg'
  | 'xl'
  | '2xl'
  | '3xl'
  | '4xl'

/** 字体大小类型 */
export type FontSize =
  | 'xs'
  | 'sm'
  | 'base'
  | 'md'
  | 'lg'
  | 'xl'
  | '2xl'
  | '3xl'
  | '4xl'

/** 字重类型 */
export type FontWeight =
  | 'light'
  | 'normal'
  | 'medium'
  | 'semibold'
  | 'bold'

/** 圆角类型 */
export type RadiusSize =
  | 'none'
  | 'sm'
  | 'base'
  | 'md'
  | 'lg'
  | 'xl'
  | '2xl'
  | '3xl'
  | 'full'

/** 阴影类型 */
export type ShadowSize =
  | 'xs'
  | 'sm'
  | 'base'
  | 'md'
  | 'lg'
  | 'xl'
  | '2xl'
  | 'inner'

/** 动画时长类型 */
export type DurationSize =
  | 'instant'
  | 'fast'
  | 'normal'
  | 'slow'
  | 'slower'
  | 'slowest'

/** 断点类型 */
export type Breakpoint =
  | 'sm'
  | 'md'
  | 'lg'
  | 'xl'
  | '2xl'

/** 渐变类型 */
export type GradientName =
  | 'primary'
  | 'blue'
  | 'pink'
  | 'cyan'
  | 'green'
  | 'sunset'
  | 'ocean'
  | 'fire'

// ============================================================================
// 设计令牌接口
// ============================================================================

export interface DesignTokens {
  colors: {
    primary: Record<string, string>
    semantic: {
      success: Record<string, string>
      warning: Record<string, string>
      danger: Record<string, string>
      info: Record<string, string>
    }
    gradients: Record<GradientName, string>
    neutral: Record<string, string>
    background: {
      page: string
      base: string
      overlay: string
      light: string
    }
    text: {
      primary: string
      regular: string
      secondary: string
      placeholder: string
      disabled: string
    }
    border: {
      base: string
      light: string
      lighter: string
      dark: string
    }
    fill: {
      base: string
      light: string
      lighter: string
      dark: string
    }
  }
  spacing: Record<SpacingSize, string>
  fontSize: Record<FontSize, string>
  fontWeight: Record<FontWeight, number>
  lineHeight: {
    none: number
    tight: number
    snug: number
    normal: number
    relaxed: number
    loose: number
  }
  letterSpacing: {
    tighter: string
    tight: string
    normal: string
    wide: string
    wider: string
    widest: string
  }
  radius: Record<RadiusSize, string>
  shadow: Record<ShadowSize, string>
  breakpoint: Record<Breakpoint, string>
  duration: Record<DurationSize, string>
  ease: {
    linear: string
    in: string
    out: string
    inOut: string
    bounce: string
    elastic: string
    smooth: string
  }
}

// ============================================================================
// 设计令牌值
// ============================================================================

/** 设计令牌常量 */
export const tokens: DesignTokens = {
  colors: {
    primary: {
      base: 'var(--color-primary)',
      light3: 'var(--color-primary-light-3)',
      light5: 'var(--color-primary-light-5)',
      light7: 'var(--color-primary-light-7)',
      light8: 'var(--color-primary-light-8)',
      light9: 'var(--color-primary-light-9)',
      dark2: 'var(--color-primary-dark-2)',
    },
    semantic: {
      success: {
        base: 'var(--color-success)',
        light: 'var(--color-success-light)',
        lighter: 'var(--color-success-lighter)',
        dark: 'var(--color-success-dark)',
      },
      warning: {
        base: 'var(--color-warning)',
        light: 'var(--color-warning-light)',
        lighter: 'var(--color-warning-lighter)',
        dark: 'var(--color-warning-dark)',
      },
      danger: {
        base: 'var(--color-danger)',
        light: 'var(--color-danger-light)',
        lighter: 'var(--color-danger-lighter)',
        dark: 'var(--color-danger-dark)',
      },
      info: {
        base: 'var(--color-info)',
        light: 'var(--color-info-light)',
        lighter: 'var(--color-info-lighter)',
        dark: 'var(--color-info-dark)',
      },
    },
    gradients: {
      primary: 'var(--gradient-primary)',
      blue: 'var(--gradient-blue)',
      pink: 'var(--gradient-pink)',
      cyan: 'var(--gradient-cyan)',
      green: 'var(--gradient-green)',
      sunset: 'var(--gradient-sunset)',
      ocean: 'var(--gradient-ocean)',
      fire: 'var(--gradient-fire)',
    },
    neutral: {
      0: 'var(--color-neutral-0)',
      50: 'var(--color-neutral-50)',
      100: 'var(--color-neutral-100)',
      200: 'var(--color-neutral-200)',
      300: 'var(--color-neutral-300)',
      400: 'var(--color-neutral-400)',
      500: 'var(--color-neutral-500)',
      600: 'var(--color-neutral-600)',
      700: 'var(--color-neutral-700)',
      800: 'var(--color-neutral-800)',
      900: 'var(--color-neutral-900)',
      950: 'var(--color-neutral-950)',
    },
    background: {
      page: 'var(--bg-color-page)',
      base: 'var(--bg-color)',
      overlay: 'var(--bg-color-overlay)',
      light: 'var(--bg-color-light)',
    },
    text: {
      primary: 'var(--text-color-primary)',
      regular: 'var(--text-color-regular)',
      secondary: 'var(--text-color-secondary)',
      placeholder: 'var(--text-color-placeholder)',
      disabled: 'var(--text-color-disabled)',
    },
    border: {
      base: 'var(--border-color)',
      light: 'var(--border-color-light)',
      lighter: 'var(--border-color-lighter)',
      dark: 'var(--border-color-dark)',
    },
    fill: {
      base: 'var(--fill-color)',
      light: 'var(--fill-color-light)',
      lighter: 'var(--fill-color-lighter)',
      dark: 'var(--fill-color-dark)',
    },
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
    '4xl': '96px',
  },
  fontSize: {
    xs: '12px',
    sm: '13px',
    base: '14px',
    md: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
    '4xl': '36px',
  },
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
  radius: {
    none: '0',
    sm: '4px',
    base: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '32px',
    full: '9999px',
  },
  shadow: {
    xs: 'var(--shadow-xs)',
    sm: 'var(--shadow-sm)',
    base: 'var(--shadow-base)',
    md: 'var(--shadow-md)',
    lg: 'var(--shadow-lg)',
    xl: 'var(--shadow-xl)',
    '2xl': 'var(--shadow-2xl)',
    inner: 'var(--shadow-inner)',
  },
  breakpoint: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  duration: {
    instant: '50ms',
    fast: '100ms',
    normal: '200ms',
    slow: '300ms',
    slower: '500ms',
    slowest: '700ms',
  },
  ease: {
    linear: 'linear',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
    elastic: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    smooth: 'cubic-bezier(0.42, 0, 0.58, 1)',
  },
}

// ============================================================================
// 工具函数
// ============================================================================

/**
 * 获取 CSS 变量值
 * @param varName - CSS 变量名（不包含 -- 前缀）
 * @returns CSS 变量引用
 * 
 * @example
 * getCSSVar('color-primary') // 返回 'var(--color-primary)'
 */
export function getCSSVar(varName: string): string {
  return `var(--${varName})`
}

/**
 * 获取间距值
 * @param size - 间距大小
 * @returns 间距值
 * 
 * @example
 * getSpacing('md') // 返回 '16px'
 */
export function getSpacing(size: SpacingSize): string {
  return tokens.spacing[size]
}

/**
 * 获取字体大小
 * @param size - 字体大小
 * @returns 字体大小值
 * 
 * @example
 * getFontSize('lg') // 返回 '18px'
 */
export function getFontSize(size: FontSize): string {
  return tokens.fontSize[size]
}

/**
 * 获取圆角值
 * @param size - 圆角大小
 * @returns 圆角值
 * 
 * @example
 * getRadius('md') // 返回 '12px'
 */
export function getRadius(size: RadiusSize): string {
  return tokens.radius[size]
}

/**
 * 获取阴影值
 * @param size - 阴影大小
 * @returns 阴影值
 * 
 * @example
 * getShadow('lg') // 返回 'var(--shadow-lg)'
 */
export function getShadow(size: ShadowSize): string {
  return tokens.shadow[size]
}

/**
 * 获取渐变色
 * @param name - 渐变名称
 * @returns 渐变色值
 * 
 * @example
 * getGradient('primary') // 返回 'var(--gradient-primary)'
 */
export function getGradient(name: GradientName): string {
  return tokens.colors.gradients[name]
}

/**
 * 获取主题色
 * @param color - 颜色类型
 * @param shade - 颜色深浅（可选）
 * @returns 颜色值
 * 
 * @example
 * getThemeColor('primary') // 返回 'var(--color-primary)'
 * getThemeColor('success', 'light') // 返回 'var(--color-success-light)'
 */
export function getThemeColor(
  color: ThemeColor | 'primary',
  shade?: 'light' | 'lighter' | 'dark'
): string {
  if (color === 'primary') {
    return tokens.colors.primary.base
  }
  if (shade) {
    return tokens.colors.semantic[color][shade]
  }
  return tokens.colors.semantic[color].base
}

/**
 * 获取中性色
 * @param shade - 色阶
 * @returns 颜色值
 * 
 * @example
 * getNeutralColor('500') // 返回 'var(--color-neutral-500)'
 */
export function getNeutralColor(shade: string): string {
  return tokens.colors.neutral[shade as keyof typeof tokens.colors.neutral]
}

/**
 * 获取断点值
 * @param breakpoint - 断点名称
 * @returns 断点值
 * 
 * @example
 * getBreakpoint('md') // 返回 '768px'
 */
export function getBreakpoint(breakpoint: Breakpoint): string {
  return tokens.breakpoint[breakpoint]
}

/**
 * 获取动画时长
 * @param size - 时长大小
 * @returns 时长值
 * 
 * @example
 * getDuration('slow') // 返回 '300ms'
 */
export function getDuration(size: DurationSize): string {
  return tokens.duration[size]
}

/**
 * 生成内联样式对象
 * @param styles - CSS 属性和值
 * @returns 内联样式对象
 * 
 * @example
 * createStyles({
 *   color: getThemeColor('primary'),
 *   padding: getSpacing('md'),
 *   borderRadius: getRadius('base')
 * })
 */
export function createStyles(
  styles: Record<string, string>
): Record<string, string> {
  return styles
}

/**
 * 检查当前是否为暗色模式
 * @returns 是否为暗色模式
 */
export function isDarkMode(): boolean {
  if (typeof window === 'undefined') return false
  return document.documentElement.classList.contains('dark')
}

/**
 * 切换主题模式
 * @param isDark - 是否切换到暗色模式
 */
export function toggleTheme(isDark?: boolean): void {
  if (typeof window === 'undefined') return
  
  const shouldToggle = isDark ?? !isDarkMode()
  document.documentElement.classList.toggle('dark', shouldToggle)
}

/**
 * 监听主题变化
 * @param callback - 主题变化回调函数
 * @returns 取消监听函数
 */
export function onThemeChange(callback: (isDark: boolean) => void): () => void {
  if (typeof window === 'undefined') return () => {}
  
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'class') {
        callback(isDarkMode())
      }
    })
  })
  
  observer.observe(document.documentElement, { attributes: true })
  return () => observer.disconnect()
}

// ============================================================================
// 导出所有工具函数
// ============================================================================

export default tokens
