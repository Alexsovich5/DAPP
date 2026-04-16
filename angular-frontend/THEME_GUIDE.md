# Dinner First - Theme & Styling Guide

## Overview

This guide documents the unified theming system for the Dinner First application. **All components MUST use CSS variables** - no hardcoded colors allowed.

## Theme Architecture

### Theme Service
- Location: `src/app/core/services/theme.service.ts`
- Applies `.light-theme` or `.dark-theme` class to `<body>` and `<html>`
- Persists theme choice in localStorage
- Automatically detects system preference

### Color System Files
1. **`_accessibility-colors.scss`** - WCAG 2.1 AA compliant color system
2. **`_emotional-colors.scss`** - Psychology-based dating app colors
3. **`_icon-standards.scss`** - Consistent icon sizing and behavior
4. **`gesture-animations.scss`** - Material Design animation system

---

## Color Variables Reference

### Text Colors
```scss
--text-primary       // Main text (gray-800 light / gray-50 dark)
--text-secondary     // Secondary text (gray-600 light / gray-200 dark)
--text-tertiary      // Muted text (gray-500 light / gray-300 dark)
--text-inverse       // Inverse text (gray-50 light / gray-900 dark)
--text-disabled      // Disabled state (gray-400 light / gray-600 dark)
```

### Background Colors
```scss
--background-primary     // Main background (#ffffff light / gray-900 dark)
--background-secondary   // Secondary background (gray-50 light / gray-800 dark)
--background-tertiary    // Tertiary background (gray-100 light / gray-700 dark)
--background-inverse     // Inverse background (gray-900 light / #ffffff dark)
```

### Border Colors
```scss
--border-light     // Light borders (gray-200 light / gray-700 dark)
--border-medium    // Medium borders (gray-300 light / gray-600 dark)
--border-strong    // Strong borders (gray-400 light / gray-500 dark)
```

### Interactive Colors
```scss
--interactive-primary         // Primary actions (indigo-600 light / indigo-400 dark)
--interactive-primary-hover   // Primary hover (indigo-700 light / indigo-300 dark)
--interactive-secondary       // Secondary actions (red-600 light / red-400 dark)
--interactive-secondary-hover // Secondary hover (red-700 light / red-300 dark)
--interactive-accent          // Accent actions (amber-600 light / amber-400 dark)
--interactive-accent-hover    // Accent hover (amber-700 light / amber-300 dark)
```

### Status Colors
```scss
--status-success   // Success states (green-600 light / green-500 dark)
--status-warning   // Warning states (amber-600 light / amber-500 dark)
--status-error     // Error states (red-600 light / red-500 dark)
--status-info      // Info states (blue-600 light / blue-500 dark)
```

### Focus Ring Colors
```scss
--focus-ring-primary     // Primary focus rings
--focus-ring-secondary   // Secondary focus rings
--focus-ring-accent      // Accent focus rings
--focus-ring-neutral     // Neutral focus rings
```

### Shadow & Effects
```scss
--shadow-color   // Box shadows (rgba(0,0,0,0.1) light / rgba(0,0,0,0.3) dark)
```

---

## Usage Guidelines

### ✅ DO - Use CSS Variables
```scss
.my-component {
  background-color: var(--background-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

### ❌ DON'T - Use Hardcoded Colors
```scss
.my-component {
  background-color: #ffffff;  // ❌ WRONG
  color: #333333;             // ❌ WRONG
  border: 1px solid #e5e7eb;  // ❌ WRONG
}
```

### ✅ DO - Add Smooth Transitions
Always add transitions for theme-aware properties:
```scss
.element {
  background-color: var(--background-primary);
  color: var(--text-primary);
  border-color: var(--border-medium);

  // Smooth theme transitions
  transition: background-color 0.3s ease,
              color 0.3s ease,
              border-color 0.3s ease;
}
```

---

## Icon Standards

### Icon Sizes
```scss
--icon-size-sm: 18px;  // Small icons
--icon-size-md: 24px;  // Default icons
--icon-size-lg: 32px;  // Large icons
--icon-size-xl: 48px;  // Extra large icons
```

### Usage
```html
<!-- Default size (24px) -->
<mat-icon>home</mat-icon>

<!-- Custom sizes -->
<mat-icon class="icon-sm">settings</mat-icon>
<mat-icon class="icon-lg">account_circle</mat-icon>
```

### Icon Color Utilities
```html
<mat-icon class="icon-primary">favorite</mat-icon>
<mat-icon class="icon-success">check_circle</mat-icon>
<mat-icon class="icon-error">error</mat-icon>
<mat-icon class="icon-muted">info</mat-icon>
```

---

## Animation System

### Easing Curves (Material Design)
```scss
--motion-ease:          cubic-bezier(0.4, 0, 0.2, 1);  // Standard
--motion-ease-out:      cubic-bezier(0, 0, 0.2, 1);    // Deceleration
--motion-ease-in:       cubic-bezier(0.4, 0, 1, 1);    // Acceleration
--motion-ease-in-out:   cubic-bezier(0.4, 0, 0.6, 1);  // Sharp
--motion-spring:        cubic-bezier(0.175, 0.885, 0.32, 1.275);  // Bounce
```

### Animation Duration
```scss
--gesture-duration:        0.3s;   // Standard animations
--gesture-bounce-duration: 0.5s;   // Bounce animations
--motion-stagger-step:     50ms;   // Cascading delays
```

### Utility Classes
```html
<div class="fade-in">Fades in from below</div>
<div class="scale-in">Scales up</div>
<div class="slide-up">Slides up</div>
<div class="stagger">
  <div>Item 1</div>  <!-- delay: 0ms -->
  <div>Item 2</div>  <!-- delay: 50ms -->
  <div>Item 3</div>  <!-- delay: 100ms -->
</div>
```

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance
- Text contrast: minimum 4.5:1
- Large text contrast: minimum 3:1
- UI components: minimum 3:1

### Focus Indicators
```scss
*:focus {
  outline: 2px solid var(--focus-ring-primary);
  outline-offset: 2px;
  border-radius: 4px;
}
```

### Touch Targets
Minimum 44x44px for interactive elements:
```scss
button, a, input, select {
  min-height: 44px;
  min-width: 44px;
}
```

### Reduced Motion
```scss
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Component Examples

### Card Component
```scss
.my-card {
  background-color: var(--background-primary);
  border: 1px solid var(--border-light);
  box-shadow: 0 2px 4px var(--shadow-color);
  border-radius: 8px;
  padding: 1rem;
  transition: background-color 0.3s ease,
              border-color 0.3s ease,
              box-shadow 0.3s ease;

  &:hover {
    border-color: var(--border-medium);
    box-shadow: 0 4px 8px var(--shadow-color);
  }
}
```

### Button Component
```scss
.primary-button {
  background-color: var(--interactive-primary);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  transition: background-color 0.2s ease, transform 0.2s ease;

  &:hover {
    background-color: var(--interactive-primary-hover);
    transform: translateY(-2px);
  }

  &:active {
    transform: translateY(0);
  }

  &:focus {
    outline: 2px solid var(--focus-ring-primary);
    outline-offset: 2px;
  }
}
```

### Form Input
```scss
.input-field {
  background-color: var(--background-primary);
  border: 1px solid var(--border-medium);
  color: var(--text-primary);
  padding: 0.75rem;
  border-radius: 4px;
  transition: border-color 0.3s ease, background-color 0.3s ease;

  &:focus {
    border-color: var(--interactive-primary);
    outline: 2px solid var(--focus-ring-primary);
    outline-offset: 2px;
  }

  &::placeholder {
    color: var(--text-tertiary);
  }
}
```

---

## Dark Theme Specific Adjustments

### When to Use Dark Theme Classes
Use `.dark-theme` selector for component-specific dark mode overrides:

```scss
.notification {
  box-shadow: 0 2px 8px var(--shadow-color);
}

.dark-theme .notification {
  // Stronger shadow for dark mode
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}
```

### Priority Backgrounds
For urgent/error states in dark mode:
```scss
.priority-urgent {
  background: var(--color-error-50);  // Light mode
}

.dark-theme .priority-urgent {
  background: rgba(239, 68, 68, 0.1);  // Dark mode (more subtle)
}
```

---

## Testing Checklist

When adding new components, verify:

- [ ] No hardcoded colors (search for `#`, `rgb`, `rgba` in styles)
- [ ] All themed properties have transitions
- [ ] Component works in both light and dark modes
- [ ] Focus indicators are visible
- [ ] Touch targets are minimum 44x44px
- [ ] Reduced motion preference respected
- [ ] WCAG 2.1 AA contrast ratios met

---

## Common Patterns

### Error States
```scss
.error-message {
  background-color: var(--error-background);
  border: 1px solid var(--error-border);
  color: var(--error-text);
  padding: 1rem;
  border-radius: 4px;
}
```

### Loading States
```scss
.loading-overlay {
  background-color: var(--background-primary);
  opacity: 0.9;
  backdrop-filter: blur(4px);
}
```

### Disabled States
```scss
.disabled-element {
  color: var(--text-disabled);
  cursor: not-allowed;
  opacity: 0.6;
}
```

---

## Migration from Hardcoded Colors

If you find hardcoded colors, replace them:

| Hardcoded Color | CSS Variable |
|----------------|--------------|
| `#ffffff` (background) | `var(--background-primary)` |
| `#f5f5f5` | `var(--background-tertiary)` |
| `#333333`, `#1f2937` | `var(--text-primary)` |
| `#666666`, `#6b7280` | `var(--text-secondary)` |
| `#999999`, `#9ca3af` | `var(--text-tertiary)` |
| `#e5e7eb` | `var(--border-light)` |
| `#2196f3`, `#4f46e5` | `var(--interactive-primary)` |
| `#f44336`, `#dc2626` | `var(--status-error)` |
| `#4caf50`, `#16a34a` | `var(--status-success)` |

---

## Support

For questions about theming:
- Review `_accessibility-colors.scss` for all available variables
- Check existing components for implementation examples
- Ensure all changes maintain WCAG 2.1 AA compliance

**Last Updated**: 2025-10-23
**Maintained By**: Dinner First Development Team
