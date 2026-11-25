# Design System - My Life AI

## Design Philosophy

**Premium, minimal, memorable** - The calendar is the visual identity. Every interaction should feel deliberate and polished.

### Core Principles
1. **Calendar-first** - The calendar occupies the primary visual space
2. **Strong hierarchy** - Clear visual distinction between today, important dates, upcoming/overdue
3. **Beautiful typography** - Careful font selection, sizing, spacing
4. **Spacious layouts** - Breathing room, not cramped dashboards
5. **Meaningful motion** - Smooth transitions, not decorative animations
6. **Theme parity** - Dark and light are equally polished

## Color System

### Brand Colors
```css
:root {
  /* Primary - Deep indigo for primary actions */
  --color-primary-50: #EEF2FF;
  --color-primary-100: #E0E7FF;
  --color-primary-200: #C7D2FE;
  --color-primary-300: #A5B4FC;
  --color-primary-400: #818CF8;
  --color-primary-500: #6366F1;
  --color-primary-600: #4F46E5;
  --color-primary-700: #4338CA;
  --color-primary-800: #3730A3;
  --color-primary-900: #312E81;
  --color-primary-950: #1E1B4B;

  /* Neutral - Warm gray for UI */
  --color-neutral-50: #FAFAFA;
  --color-neutral-100: #F5F5F5;
  --color-neutral-200: #E5E5E5;
  --color-neutral-300: #D4D4D4;
  --color-neutral-400: #A3A3A3;
  --color-neutral-500: #737373;
  --color-neutral-600: #525252;
  --color-neutral-700: #404040;
  --color-neutral-800: #262626;
  --color-neutral-900: #171717;
  --color-neutral-950: #0A0A0A;

  /* Semantic - Success, Warning, Error */
  --color-success-500: #22C55E;
  --color-warning-500: #F59E0B;
  --color-error-500: #EF4444;
}
```

### Dark Theme Overrides
```css
[data-theme="dark"] {
  --color-bg-primary: var(--color-neutral-950);
  --color-bg-secondary: var(--color-neutral-900);
  --color-bg-tertiary: var(--color-neutral-800);
  --color-bg-hover: var(--color-neutral-800);
  --color-bg-active: var(--color-neutral-700);

  --color-text-primary: var(--color-neutral-50);
  --color-text-secondary: var(--color-neutral-400);
  --color-text-tertiary: var(--color-neutral-500);
  --color-text-inverse: var(--color-neutral-950);

  --color-border-primary: var(--color-neutral-800);
  --color-border-secondary: var(--color-neutral-700);
  --color-border-focus: var(--color-primary-500);

  --color-primary-bg: var(--color-primary-950);
  --color-primary-border: var(--color-primary-800);
  --color-primary-text: var(--color-primary-300);
}
```

### Light Theme (Default)
```css
:root:not([data-theme="dark"]) {
  --color-bg-primary: var(--color-neutral-50);
  --color-bg-secondary: #FFFFFF;
  --color-bg-tertiary: var(--color-neutral-100);
  --color-bg-hover: var(--color-neutral-100);
  --color-bg-active: var(--color-neutral-200);

  --color-text-primary: var(--color-neutral-900);
  --color-text-secondary: var(--color-neutral-600);
  --color-text-tertiary: var(--color-neutral-500);
  --color-text-inverse: #FFFFFF;

  --color-border-primary: var(--color-neutral-200);
  --color-border-secondary: var(--color-neutral-300);
  --color-border-focus: var(--color-primary-500);

  --color-primary-bg: var(--color-primary-50);
  --color-primary-border: var(--color-primary-200);
  --color-primary-text: var(--color-primary-700);
}
```

### Category Colors (Default System Categories)
```css
:root {
  --color-category-family: #E91E63;       /* Pink */
  --color-category-career: #2196F3;        /* Blue */
  --color-category-entertainment: #9C27B0; /* Purple */
  --color-category-reminders: #FF5722;     /* Deep Orange */
  --color-category-personal: #4CAF50;      /* Green */
}
```

## Typography

### Font Stack
```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  --font-display: 'Cal Sans', 'Inter', -apple-system, sans-serif; /* Optional display font */
}
```

### Type Scale
```css
:root {
  /* Display */
  --text-display-xl: clamp(3rem, 5vw, 4.5rem);     /* 48-72px */
  --text-display-lg: clamp(2.25rem, 4vw, 3rem);    /* 36-48px */
  --text-display-md: clamp(1.75rem, 3vw, 2.25rem); /* 28-36px */
  --text-display-sm: clamp(1.5rem, 2.5vw, 1.875rem); /* 24-30px */

  /* Headings */
  --text-h1: clamp(1.875rem, 2.5vw, 2.25rem);  /* 30-36px */
  --text-h2: clamp(1.5rem, 2vw, 1.875rem);      /* 24-30px */
  --text-h3: clamp(1.25rem, 1.5vw, 1.5rem);     /* 20-24px */
  --text-h4: clamp(1.125rem, 1.25vw, 1.25rem);  /* 18-20px */

  /* Body */
  --text-lg: 1.125rem;    /* 18px */
  --text-base: 1rem;      /* 16px */
  --text-sm: 0.875rem;    /* 14px */
  --text-xs: 0.75rem;     /* 12px */

  /* Line Heights */
  --leading-tight: 1.1;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  /* Font Weights */
  --weight-light: 300;
  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
}
```

## Spacing System

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
  --space-24: 6rem;     /* 96px */
}
```

## Border Radius

```css
:root {
  --radius-none: 0;
  --radius-sm: 0.25rem;    /* 4px */
  --radius-md: 0.375rem;   /* 6px */
  --radius-lg: 0.5rem;     /* 8px */
  --radius-xl: 0.75rem;    /* 12px */
  --radius-2xl: 1rem;      /* 16px */
  --radius-full: 9999px;
}
```

## Shadows & Depth

```css
:root {
  --shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);

  /* Colored shadows for primary actions */
  --shadow-primary-sm: 0 1px 3px 0 rgb(99 102 241 / 0.3);
  --shadow-primary-md: 0 4px 6px -1px rgb(99 102 241 / 0.3);
  --shadow-primary-lg: 0 10px 15px -3px rgb(99 102 241 / 0.3);
}
```

## Transitions & Animation

```css
:root {
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 350ms;
  --duration-slower: 500ms;

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

## Component Patterns

### Calendar Grid
- Month view: 7-column grid, minimum 100px per cell on desktop
- Week view: 7 columns, horizontal scroll on mobile
- Day view: Time slots 60px height, all-day section at top
- Year view: 4x3 month miniatures

### Event Visualization
- Color bar on left (3px) matching category color
- Priority indicator: dot (normal), bar (high), double bar (critical)
- Recurring badge: circular arrow icon
- All-day events: Full-width banner at top of day
- Hover: Expand to show time, location, preview

### Cards & Panels
- Consistent padding: `--space-6`
- Border: `--color-border-primary`
- Radius: `--radius-xl`
- Shadow: `--shadow-sm` default, `--shadow-md` on hover

### Buttons
```css
/* Primary */
.btn-primary {
  background: var(--color-primary-600);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast) var(--ease-out);
}
.btn-primary:hover { background: var(--color-primary-700); }
.btn-primary:active { background: var(--color-primary-800); }

/* Secondary */
.btn-secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-primary);
  /* ... same padding/radius */
}

/* Ghost */
.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
  /* ... */
}
.btn-ghost:hover { background: var(--color-bg-hover); color: var(--color-text-primary); }
```

### Form Elements
- Input height: 44px (touch-friendly)
- Focus ring: 2px solid `--color-border-focus`, offset 2px
- Error state: `--color-error-500` border and focus ring
- Label: `--text-sm`, `--weight-medium`, `--color-text-secondary`

## Responsive Breakpoints

```css
:root {
  --bp-sm: 640px;   /* Mobile landscape */
  --bp-md: 768px;   /* Tablet */
  --bp-lg: 1024px;  /* Desktop */
  --bp-xl: 1280px;  /* Large desktop */
  --bp-2xl: 1536px; /* Ultra-wide */
}
```

### Calendar Responsive Behavior
- **< 640px**: Month view stacks weeks vertically, week view horizontal scroll
- **640-1024px**: Month view 7-col, week view 7-col, side panel collapsible
- **> 1024px**: Full layout with persistent side panel

## Icon System

- Use Lucide React or Phosphor Icons (consistent stroke weight 2px)
- Size scale: 16px (sm), 20px (base), 24px (lg), 32px (xl)
- Category icons: Custom SVG set matching brand style

## Accessibility

- WCAG AA minimum contrast (4.5:1 text, 3:1 UI)
- Focus visible on all interactive elements
- Keyboard navigation for all calendar interactions
- ARIA labels for icon-only buttons
- Reduced motion respect: `@media (prefers-reduced-motion)`
- Screen reader announcements for date navigation

## Ant Design Integration

### Theme Customization
```typescript
// theme.ts
import { theme } from 'antd';

export const antdTheme = {
  token: {
    colorPrimary: '#6366F1',
    colorSuccess: '#22C55E',
    colorWarning: '#F59E0B',
    colorError: '#EF4444',
    borderRadius: 8,
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    // ... map design tokens
  },
  components: {
    Button: {
      controlHeight: 44,
      fontWeight: 500,
    },
    Input: {
      controlHeight: 44,
      paddingInline: 12,
    },
    // ... other component overrides
  },
};
```

### Component Usage Guidelines
- Use Ant Design for: Form, Modal, Dropdown, Select, DatePicker, Message, Notification, Spin, Tabs
- Build custom: Calendar grid, Event cards, Category picker, AI chat interface
- Avoid: Ant Design Layout (build custom), Ant Design Calendar (too limited)

## Tailwind CSS Integration

### Config
```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { /* ... */ },
        neutral: { /* ... */ },
        // semantic colors mapped to CSS variables
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: { /* ... map to --space-* */ },
      borderRadius: { /* ... map to --radius-* */ },
      boxShadow: { /* ... map to --shadow-* */ },
      transitionDuration: { /* ... map to --duration-* */ },
      transitionTimingFunction: { /* ... map to --ease-* */ },
    },
  },
  plugins: [],
};
```

### Usage Pattern
```tsx
// Use Tailwind for layout, spacing, responsive utilities
// Use CSS variables for theming (colors, shadows)
// Use custom CSS for complex components (calendar grid)
<div className="flex h-screen bg-[var(--color-bg-primary)]">
  <aside className="w-72 border-r border-[var(--color-border-primary)] bg-[var(--color-bg-secondary)]">
    {/* Sidebar */}
  </aside>
  <main className="flex-1 overflow-auto p-6">
    {/* Calendar */}
  </main>
</div>
```

## Motion Guidelines

### Calendar Navigation
- Month change: 250ms slide + fade
- View switch (month→week): 300ms cross-fade + scale
- Date selection: 150ms scale pulse

### Event Interactions
- Hover expand: 150ms ease-out
- Drag to reschedule: Real-time, no animation
- Drop confirmation: 200ms spring

### Modals/Drawers
- Enter: 250ms scale(0.95)→1 + fade
- Exit: 200ms scale(1)→0.95 + fade
- Backdrop: 200ms fade

### Notifications
- Slide in from top-right: 300ms ease-out
- Auto-dismiss: 500ms fade + slide up
- Hover pause: Pause timer

## Implementation Checklist

- [ ] CSS variables defined in global stylesheet
- [ ] Tailwind config maps to design tokens
- [ ] Ant Design theme configured
- [ ] Theme provider (light/dark/system)
- [ ] Base typography styles
- [ ] Component primitives (Button, Input, Card, Modal)
- [ ] Calendar-specific components
- [ ] Responsive layout components
- [ ] Animation utilities
- [ ] Accessibility audit