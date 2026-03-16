# BioWorkflow Design System

## Design Philosophy

BioWorkflow's design system embraces a **scientific precision** aesthetic that reflects the bioinformatics domain. The visual language combines:

- **Clinical precision**: Clean lines, structured grids, and meticulous spacing
- **Scientific visualization**: Data-forward approach with rich visualizations
- **Modern minimalism**: Restrained color palette with purposeful accent colors
- **Professional sophistication**: Trustworthy and authoritative feel

## Color System

### Primary Palette

```css
/* Primary - Deep Scientific Blue */
--color-primary-50: #EEF4FF;
--color-primary-100: #D9E5FF;
--color-primary-200: #BCD6FF;
--color-primary-300: #8FB5FF;
--color-primary-400: #5A8CF7;
--color-primary-500: #3666E8;  /* Primary */
--color-primary-600: #2649C5;
--color-primary-700: #1E399F;
--color-primary-800: #1D3082;
--color-primary-900: #1D2C6B;

/* Secondary - Data Visualization Teal */
--color-secondary-50: #F0FDFA;
--color-secondary-100: #CCFBF1;
--color-secondary-200: #99F6E4;
--color-secondary-300: #5EEAD4;
--color-secondary-400: #2DD4BF;
--color-secondary-500: #14B8A6;  /* Secondary */
--color-secondary-600: #0D9488;
--color-secondary-700: #0F766E;
--color-secondary-800: #115E59;
--color-secondary-900: #134E4A;
```

### Neutral Palette

```css
/* Gray - Scientific Precision */
--color-gray-0: #FFFFFF;
--color-gray-50: #F8FAFC;
--color-gray-100: #F1F5F9;
--color-gray-200: #E2E8F0;
--color-gray-300: #CBD5E1;
--color-gray-400: #94A3B8;
--color-gray-500: #64748B;
--color-gray-600: #475569;
--color-gray-700: #334155;
--color-gray-800: #1E293B;
--color-gray-900: #0F172A;
--color-gray-950: #020617;
```

### Semantic Colors

```css
/* Success - Growth Green */
--color-success-50: #F0FDF4;
--color-success-500: #22C55E;
--color-success-600: #16A34A;
--color-success-700: #15803D;

/* Warning - Caution Amber */
--color-warning-50: #FFFBEB;
--color-warning-500: #F59E0B;
--color-warning-600: #D97706;
--color-warning-700: #B45309;

/* Error - Alert Red */
--color-error-50: #FEF2F2;
--color-error-500: #EF4444;
--color-error-600: #DC2626;
--color-error-700: #B91C1C;

/* Info - Scientific Blue */
--color-info-50: #EFF6FF;
--color-info-500: #3B82F6;
--color-info-600: #2563EB;
--color-info-700: #1D4ED8;
```

## Typography System

### Font Families

```css
/* Display & Headlines */
--font-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Body & UI */
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Monospace - Code & Data */
--font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Type Scale

```css
/* Display - Hero Headlines */
--text-display-lg: 4.5rem;    /* 72px */
--text-display: 3.75rem;     /* 60px */
--text-display-sm: 3rem;     /* 48px */

/* Headlines */
--text-h1: 2.5rem;           /* 40px */
--text-h2: 2rem;             /* 32px */
--text-h3: 1.75rem;          /* 28px */
--text-h4: 1.5rem;           /* 24px */
--text-h5: 1.25rem;          /* 20px */
--text-h6: 1.125rem;         /* 18px */

/* Body */
--text-lg: 1.125rem;         /* 18px */
--text-base: 1rem;           /* 16px */
--text-sm: 0.875rem;         /* 14px */
--text-xs: 0.75rem;          /* 12px */

/* Line Heights */
--leading-none: 1;
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;

/* Letter Spacing */
--tracking-tighter: -0.05em;
--tracking-tight: -0.025em;
--tracking-normal: 0;
--tracking-wide: 0.025em;
--tracking-wider: 0.05em;
--tracking-widest: 0.1em;
```

## Spacing System

```css
/* 4px base unit scale */
--space-0: 0;
--space-px: 1px;
--space-0-5: 0.125rem;   /* 2px */
--space-1: 0.25rem;      /* 4px */
--space-1-5: 0.375rem;   /* 6px */
--space-2: 0.5rem;       /* 8px */
--space-2-5: 0.625rem;   /* 10px */
--space-3: 0.75rem;      /* 12px */
--space-3-5: 0.875rem;   /* 14px */
--space-4: 1rem;         /* 16px */
--space-5: 1.25rem;      /* 20px */
--space-6: 1.5rem;       /* 24px */
--space-7: 1.75rem;      /* 28px */
--space-8: 2rem;         /* 32px */
--space-9: 2.25rem;      /* 36px */
--space-10: 2.5rem;      /* 40px */
--space-11: 2.75rem;     /* 44px */
--space-12: 3rem;        /* 48px */
--space-14: 3.5rem;      /* 56px */
--space-16: 4rem;        /* 64px */
--space-20: 5rem;        /* 80px */
--space-24: 6rem;        /* 96px */
--space-28: 7rem;        /* 112px */
--space-32: 8rem;        /* 128px */
--space-36: 9rem;        /* 144px */
--space-40: 10rem;       /* 160px */
--space-44: 11rem;       /* 176px */
--space-48: 12rem;       /* 192px */
--space-52: 13rem;       /* 208px */
--space-56: 14rem;       /* 224px */
--space-60: 15rem;       /* 240px */
--space-64: 16rem;       /* 256px */
--space-72: 18rem;       /* 288px */
--space-80: 20rem;       /* 320px */
--space-96: 24rem;       /* 384px */
```

## Border & Radius System

```css
/* Border Width */
--border-0: 0px;
--border-1: 1px;
--border-2: 2px;
--border-4: 4px;
--border-8: 8px;

/* Border Radius */
--radius-none: 0px;
--radius-sm: 0.125rem;   /* 2px */
--radius-base: 0.25rem;  /* 4px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-2xl: 1rem;      /* 16px */
--radius-3xl: 1.5rem;    /* 24px */
--radius-full: 9999px;
```

## Shadow System

```css
/* Box Shadows */
--shadow-none: none;

--shadow-xs: 
  0 1px 2px 0 rgb(0 0 0 / 0.05);

--shadow-sm: 
  0 1px 2px 0 rgb(0 0 0 / 0.05),
  0 1px 3px 0 rgb(0 0 0 / 0.1);

--shadow-base: 
  0 1px 3px 0 rgb(0 0 0 / 0.1),
  0 1px 2px -1px rgb(0 0 0 / 0.1);

--shadow-md: 
  0 4px 6px -1px rgb(0 0 0 / 0.1),
  0 2px 4px -2px rgb(0 0 0 / 0.1);

--shadow-lg: 
  0 10px 15px -3px rgb(0 0 0 / 0.1),
  0 4px 6px -4px rgb(0 0 0 / 0.1);

--shadow-xl: 
  0 20px 25px -5px rgb(0 0 0 / 0.1),
  0 8px 10px -6px rgb(0 0 0 / 0.1);

--shadow-2xl: 
  0 25px 50px -12px rgb(0 0 0 / 0.25);

--shadow-inner: 
  inset 0 2px 4px 0 rgb(0 0 0 / 0.05);

/* Colored Shadows for Status */
--shadow-success: 0 4px 6px -1px rgb(34 197 94 / 0.2);
--shadow-warning: 0 4px 6px -1px rgb(245 158 11 / 0.2);
--shadow-error: 0 4px 6px -1px rgb(239 68 68 / 0.2);
--shadow-info: 0 4px 6px -1px rgb(59 130 246 / 0.2);
```

## Animation & Transition System

```css
/* Duration */
--duration-instant: 0ms;
--duration-fast: 100ms;
--duration-base: 150ms;
--duration-normal: 200ms;
--duration-moderate: 300ms;
--duration-slow: 500ms;
--duration-slower: 700ms;

/* Easing */
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);

/* Common Transitions */
--transition-colors: color, background-color, border-color, text-decoration-color, fill, stroke;
--transition-opacity: opacity;
--transition-shadow: box-shadow;
--transition-transform: transform;

/* Animation Keyframes */
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fade-out {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slide-down {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Breakpoints & Grid

```css
/* Breakpoints */
--breakpoint-xs: 0;
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;

/* Container */
--container-xs: 100%;
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;

/* Grid */
--grid-columns: 12;
--grid-gap: 1.5rem;
```

## Z-Index Scale

```css
--z-negative: -1;
--z-0: 0;
--z-10: 10;
--z-20: 20;
--z-30: 30;
--z-40: 40;
--z-50: 50;
--z-auto: auto;

/* Semantic Z-Index */
--z-base: var(--z-0);
--z-dropdown: var(--z-10);
--z-sticky: var(--z-20);
--z-fixed: var(--z-30);
--z-modal-backdrop: var(--z-40);
--z-modal: var(--z-50);
--z-tooltip: var(--z-50);
--z-toast: var(--z-50);
```

## Usage Examples

### Button Component

```css
.btn {
  /* Base */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  
  /* Typography */
  font-family: var(--font-body);
  font-weight: 500;
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  
  /* Spacing */
  padding: var(--space-2) var(--space-4);
  
  /* Visual */
  background-color: var(--color-primary-500);
  color: white;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  
  /* Shadow */
  box-shadow: var(--shadow-sm);
  
  /* Transition */
  transition: 
    background-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
}

.btn:hover {
  background-color: var(--color-primary-600);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn:active {
  background-color: var(--color-primary-700);
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
```

### Card Component

```css
.card {
  background-color: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-gray-200);
  box-shadow: var(--shadow-base);
  overflow: hidden;
  transition: 
    box-shadow var(--duration-moderate) var(--ease-out),
    transform var(--duration-moderate) var(--ease-out);
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.card-header {
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-gray-200);
}

.card-body {
  padding: var(--space-5);
}

.card-footer {
  padding: var(--space-4) var(--space-5);
  background-color: var(--color-gray-50);
  border-top: 1px solid var(--color-gray-200);
}
```

This design system provides a comprehensive foundation for building consistent, beautiful, and functional interfaces for the BioWorkflow platform.
