# Keyboard Navigation Guide - Dinner First

**Complete accessibility guide for keyboard and screen reader users**

## 🎯 Overview

Dinner First provides comprehensive keyboard navigation and screen reader support across all components. This guide covers all available keyboard shortcuts and navigation patterns to help you efficiently use the application without a mouse.

## 🔍 Discovery Page Navigation

### Card Navigation
Navigate through soul connection profiles using these keyboard shortcuts:

| Key | Action |
|-----|--------|
| `↑` `↓` `←` `→` | Navigate between discovery cards |
| `Home` | Jump to first card |
| `End` | Jump to last card |
| `Enter` or `Space` | Focus on card action buttons |
| `Esc` | Return to main discovery list |

### Quick Actions (Power User Shortcuts)
Perform actions directly from any card without focusing buttons:

| Key | Action |
|-----|--------|
| `C` | Quick connect with current profile |
| `P` | Quick pass on current profile |

### Action Buttons Within Cards
When focused on a card's action buttons:

| Key | Action |
|-----|--------|
| `←` `→` | Navigate between Pass and Connect buttons |
| `Enter` or `Space` | Activate the focused button |
| `Esc` | Return focus to the card |

## 🎛️ Filter Controls

### Filter Navigation
| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate between different filter controls |
| `←` `→` | Adjust slider values (for compatibility and max results) |
| `Space` | Toggle photo hiding setting |
| `Home` | Jump to first filter control |
| `End` | Jump to last filter control |
| `Esc` | Return to filter toggle button |

### Filter Toggle Button
| Key | Action |
|-----|--------|
| `Enter` or `Space` | Expand/collapse filter section |

## 📄 Empty State Components

### Action Button Navigation
| Key | Action |
|-----|--------|
| `←` `→` `↑` `↓` | Navigate between action buttons |
| `Enter` or `Space` | Activate the focused button |
| `Home` | Focus first action button |
| `End` | Focus last action button |

## 🧭 Main Navigation

### Navigation Menu
| Key | Action |
|-----|--------|
| `Tab` | Move between navigation items |
| `Enter` or `Space` | Activate navigation link |
| `↓` | Open user menu (when focused on user avatar) |
| `Esc` | Close user menu |

### User Menu Dropdown
| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate between menu items |
| `Enter` | Activate menu item |
| `Esc` | Close menu and return to user avatar |
| `Home` | Jump to first menu item |
| `End` | Jump to last menu item |

## 🔊 Screen Reader Announcements

### Automatic Announcements
The application provides real-time announcements for:

- **Loading States**: "Loading soul connections..."
- **Results**: "Found 5 soul connections. Use arrow keys to navigate between profiles."
- **Actions**: "Connecting with Sarah..." / "Passed on Michael's profile"
- **Navigation**: "Card 2 of 5: Emma, 87% compatibility"
- **Filter Changes**: "Minimum compatibility: 75%"
- **Errors**: "Error loading connections: Network timeout"

### Context Information
Each discovery card provides comprehensive descriptions including:
- Name and age
- Location information
- Bio preview
- Shared interests
- Emotional depth score
- Compatibility explanation

## ⚡ Power User Tips

### Efficient Browsing Patterns
1. **Quick Review**: Use `↓` to browse cards, `C` to connect, `P` to pass
2. **Detailed Review**: Use `Enter` on interesting cards to access action buttons
3. **Filter Adjustment**: Use `Tab` to reach filters, adjust with arrow keys
4. **Batch Actions**: Use quick keys `C` and `P` for rapid decision making

### Focus Management
- Focus automatically moves to the next card after passing/connecting
- Returning from action buttons restores focus to the card
- Filter controls auto-focus when expanding filter section
- Error states maintain focus context

## 🎨 Accessibility Features

### Visual Indicators
- **High Contrast Focus Rings**: 2px solid outline with 2px offset
- **Color Contrast**: All text meets WCAG 2.1 AA standards (4.5:1 minimum)
- **Touch Targets**: Minimum 44px for all interactive elements

### Motion Preferences
- Respects `prefers-reduced-motion` setting
- Animations disabled when reduced motion is enabled
- Focus transitions remain smooth regardless of motion preference

### High Contrast Support
- Automatic adaptation to high contrast themes
- Enhanced focus indicators in high contrast mode
- Semantic color usage for status information

## 🛠️ Technical Implementation

### ARIA Standards
- **Live Regions**: `aria-live="polite"` for status updates
- **Landmarks**: Proper `role` attributes for navigation structure
- **Labels**: Comprehensive `aria-label` and `aria-describedby` usage
- **States**: Dynamic `aria-expanded`, `aria-selected` management

### Keyboard Patterns
- **Roving Tabindex**: Efficient focus management in card lists
- **Modal Focus Trapping**: Contained focus in dropdown menus
- **Escape Handling**: Consistent escape key behavior across components
- **Arrow Key Navigation**: Standard directional navigation patterns

## 🔧 Troubleshooting

### Common Issues

**Cards not responding to arrow keys:**
- Ensure a card is focused first (click or tab to a card)
- Check that you're not in a form control (press Esc to exit)

**Screen reader not announcing changes:**
- Ensure your screen reader is compatible (NVDA, JAWS, VoiceOver supported)
- Check that live regions are enabled in your screen reader settings

**Filter controls not accessible:**
- Expand the filter section first (focus filter toggle, press Enter)
- Use arrow keys, not tab, to navigate between filter controls

### Browser Compatibility
- **Chrome**: Full support for all keyboard navigation
- **Firefox**: Full support with enhanced focus indicators
- **Safari**: Full support with VoiceOver optimization
- **Edge**: Full support with high contrast mode support

## 📱 Mobile Considerations

### Touch and Keyboard Hybrid
- External keyboards work with mobile devices
- Switch Control support on iOS
- TalkBack navigation support on Android
- Minimum touch target sizes maintained

### Screen Reader Mobile Apps
- VoiceOver gestures complement keyboard navigation
- TalkBack swipe actions work alongside key commands
- Voice Access integration for hands-free navigation

## 🆕 Updates and Improvements

This navigation system is continuously improved based on user feedback and accessibility standards updates. Key areas of ongoing enhancement:

- **Performance**: Optimizing announcement timing and frequency
- **Personalization**: Customizable keyboard shortcuts
- **Context Awareness**: Smarter focus restoration and prediction
- **Multi-modal**: Better integration with voice and gesture controls

---

**Need Help?** If you encounter any accessibility issues or have suggestions for improvement, please contact our support team. We're committed to providing an excellent experience for all users.

**Last Updated**: July 2025  
**WCAG Compliance**: 2.1 AA Standard