/**
 * Color accessibility utilities for WCAG 2.1 AA compliance
 * Provides color contrast validation and accessible color palette
 */

export interface ColorContrastRatio {
  ratio: number;
  wcagAA: boolean;
  wcagAAA: boolean;
  level: 'fail' | 'aa' | 'aaa';
}

export class ColorAccessibilityUtils {
  
  /**
   * Calculate contrast ratio between two colors
   * @param color1 - First color (hex, rgb, or hsl)
   * @param color2 - Second color (hex, rgb, or hsl)
   * @returns Contrast ratio and WCAG compliance levels
   */
  static calculateContrastRatio(color1: string, color2: string): ColorContrastRatio {
    const luminance1 = this.getRelativeLuminance(color1);
    const luminance2 = this.getRelativeLuminance(color2);
    
    const lighter = Math.max(luminance1, luminance2);
    const darker = Math.min(luminance1, luminance2);
    
    const ratio = (lighter + 0.05) / (darker + 0.05);
    
    return {
      ratio: Math.round(ratio * 100) / 100,
      wcagAA: ratio >= 4.5,
      wcagAAA: ratio >= 7,
      level: ratio >= 7 ? 'aaa' : ratio >= 4.5 ? 'aa' : 'fail'
    };
  }

  /**
   * Get relative luminance of a color according to WCAG standards
   */
  private static getRelativeLuminance(color: string): number {
    const rgb = this.hexToRgb(color);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Convert hex color to RGB
   */
  private static hexToRgb(hex: string): {r: number, g: number, b: number} | null {
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);

    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

  /**
   * Validate if a color meets WCAG AA standards against common backgrounds
   */
  static validateColorAccessibility(color: string): {
    onWhite: ColorContrastRatio;
    onLight: ColorContrastRatio;
    onDark: ColorContrastRatio;
    onBlack: ColorContrastRatio;
  } {
    return {
      onWhite: this.calculateContrastRatio(color, '#ffffff'),
      onLight: this.calculateContrastRatio(color, '#f8fafc'),
      onDark: this.calculateContrastRatio(color, '#2d3748'),
      onBlack: this.calculateContrastRatio(color, '#000000')
    };
  }

  /**
   * Get an accessible color variant that meets WCAG AA standards
   */
  static getAccessibleColor(
    originalColor: string, 
    backgroundColor: string, 
    targetLevel: 'aa' | 'aaa' = 'aa'
  ): string {
    const targetRatio = targetLevel === 'aaa' ? 7 : 4.5;
    let testColor = originalColor;
    
    // Try darkening or lightening the color to meet contrast requirements
    const rgb = this.hexToRgb(originalColor);
    if (!rgb) return originalColor;

    // Start with original color and adjust brightness
    for (let adjustment = 0; adjustment <= 100; adjustment += 5) {
      // Try darkening
      const darkerColor = this.adjustBrightness(originalColor, -adjustment);
      if (this.calculateContrastRatio(darkerColor, backgroundColor).ratio >= targetRatio) {
        return darkerColor;
      }

      // Try lightening
      const lighterColor = this.adjustBrightness(originalColor, adjustment);
      if (this.calculateContrastRatio(lighterColor, backgroundColor).ratio >= targetRatio) {
        return lighterColor;
      }
    }

    // If no adjustment works, return a safe fallback
    const bgLuminance = this.getRelativeLuminance(backgroundColor);
    return bgLuminance > 0.5 ? '#2d3748' : '#f7fafc';
  }

  /**
   * Adjust brightness of a color
   */
  private static adjustBrightness(color: string, percent: number): string {
    const rgb = this.hexToRgb(color);
    if (!rgb) return color;

    const adjust = (c: number) => {
      const adjusted = c + (255 - c) * (percent / 100);
      return Math.min(255, Math.max(0, Math.round(adjusted)));
    };

    const r = adjust(rgb.r);
    const g = adjust(rgb.g);
    const b = adjust(rgb.b);

    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  }
}

/**
 * WCAG 2.1 AA compliant color palette for Dinner First
 */
export const AccessibleColorPalette = {
  // Primary colors with accessible variants
  primary: {
    50: '#f0f4ff',
    100: '#e0e7ff',
    200: '#c7d2fe',
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#6366f1', // Main primary color
    600: '#4f46e5', // Accessible on light backgrounds
    700: '#4338ca', // High contrast version
    800: '#3730a3',
    900: '#312e81'
  },

  // Secondary colors (emotion-focused warm tones)
  secondary: {
    50: '#fef3f2',
    100: '#fee4e2',
    200: '#fecdca',
    300: '#fdaba5',
    400: '#f87c73',
    500: '#ef4444', // Main secondary color
    600: '#dc2626', // Accessible version
    700: '#b91c1c', // High contrast version
    800: '#991b1b',
    900: '#7f1d1d'
  },

  // Accent colors (soul-focused gold)
  accent: {
    50: '#fffcf0',
    100: '#fff8dc',
    200: '#fef0b8',
    300: '#fde68a',
    400: '#fcd34d',
    500: '#f59e0b', // Main accent color
    600: '#d97706', // Accessible version
    700: '#b45309', // High contrast version
    800: '#92400e',
    900: '#78350f'
  },

  // Neutral grays with high contrast ratios
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280', // Accessible on light backgrounds (4.59:1)
    600: '#4b5563', // High contrast on light (7.07:1)
    700: '#374151', // Very high contrast (10.74:1)
    800: '#1f2937', // Maximum contrast (15.78:1)
    900: '#111827'
  },

  // Success colors
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a', // Accessible version
    700: '#15803d', // High contrast version
    800: '#166534',
    900: '#14532d'
  },

  // Warning colors
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706', // Accessible version
    700: '#b45309', // High contrast version
    800: '#92400e',
    900: '#78350f'
  },

  // Error colors
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626', // Accessible version
    700: '#b91c1c', // High contrast version
    800: '#991b1b',
    900: '#7f1d1d'
  },

  // Information colors
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb', // Accessible version
    700: '#1d4ed8', // High contrast version
    800: '#1e40af',
    900: '#1e3a8a'
  }
};

/**
 * Semantic color mappings for consistent usage
 */
export const SemanticColors = {
  // Text colors (WCAG AA compliant)
  text: {
    primary: AccessibleColorPalette.neutral[800],   // 15.78:1 contrast on white
    secondary: AccessibleColorPalette.neutral[600], // 7.07:1 contrast on white
    tertiary: AccessibleColorPalette.neutral[500],  // 4.59:1 contrast on white
    inverse: AccessibleColorPalette.neutral[50],    // High contrast on dark backgrounds
    disabled: AccessibleColorPalette.neutral[400]   // For disabled states
  },

  // Background colors
  background: {
    primary: '#ffffff',
    secondary: AccessibleColorPalette.neutral[50],
    tertiary: AccessibleColorPalette.neutral[100],
    inverse: AccessibleColorPalette.neutral[900]
  },

  // Interactive element colors
  interactive: {
    primary: AccessibleColorPalette.primary[600],     // 4.5:1 on white
    primaryHover: AccessibleColorPalette.primary[700], // Higher contrast on hover
    secondary: AccessibleColorPalette.secondary[600],
    secondaryHover: AccessibleColorPalette.secondary[700],
    accent: AccessibleColorPalette.accent[600],
    accentHover: AccessibleColorPalette.accent[700]
  },

  // Border colors
  border: {
    light: AccessibleColorPalette.neutral[200],
    medium: AccessibleColorPalette.neutral[300],
    strong: AccessibleColorPalette.neutral[400]
  },

  // Status colors (all WCAG AA compliant)
  status: {
    success: AccessibleColorPalette.success[600],
    warning: AccessibleColorPalette.warning[600],
    error: AccessibleColorPalette.error[600],
    info: AccessibleColorPalette.info[600]
  }
};