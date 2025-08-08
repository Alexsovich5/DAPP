### Dinner First Frontend UX Roadmap (Suggestions)

This document outlines proposed improvements to increase interactivity, polish, and engagement. It’s organized by phases with concrete tasks, affected files, acceptance criteria, and success metrics.

### Goals
- Elevate perceived quality with tasteful motion and micro-interactions
- Reduce friction in messaging, onboarding, and revelation flows
- Improve mobile-first usability and performance
- Strengthen trust/safety cues and accessibility

### Phase 1: Messaging Experience (Weeks 1-2)
- Optimistic send + retries
  - Affected: shared/components/toast, features/messages/messages.component.ts, src/sw.js
  - Add queued/pending state badges when offline (background sync), auto-retry, and error toasts.
  - Acceptance: Messages sent offline show “Queued” then auto-update to “Sent/Failed”.
- Read receipts and presence
  - Affected: features/messages/messages.component.ts, core/services/chat.service.ts
  - Show delivered/read ticks and last-seen. Update on WS events.
  - Acceptance: Receipts reflect server state; presence updates within 5s.
- Rich composer
  - Affected: features/messages/messages.component.ts, core/services/mobile-features.service.ts
  - Add quick prompts (AI starters), emoji/gif, camera capture, image compress-before-upload.
  - Acceptance: Image send < 1s for 1080px photos on mid devices; prompts insert instantly.

### Phase 2: Progressive Revelation UX (Weeks 2-3)
- 7-day timeline UI + streaks
  - Affected: features/revelations/revelations.component.ts, revelations-empty-state.component.ts
  - Visual progress bar, streak counters, and “what’s next” tips.
  - Acceptance: Progress updates immediately post-action; streak saved across sessions.
- Reveal celebrations
  - Affected: shared/components/match-celebration, shared/components/soul-orb
  - Micro-animations on key unlocks; subtle confetti burst under reduced-motion guard.
  - Acceptance: Animation duration < 800ms; respects reduced-motion setting.

### Phase 3: Discover & Onboarding (Weeks 3-4)
- Card stack with physics + haptics
  - Affected: shared/directives/swipe.directive.ts, features/discover/discover.component.ts
  - Add spring-like feedback, tactile vibrations on decisive actions, smooth undo.
  - Acceptance: Swipe latency < 16ms budget on mid devices; no jitters.
- Interactive onboarding
  - Affected: features/onboarding/*, shared/components/onboarding-*
  - Swipeable questions, live compatibility preview (mini radar), skeleton placeholders.
  - Acceptance: Step transitions < 300ms; autosave without visible layout shift.

### Phase 4: Visual Polish & Motion (Weeks 4-5)
- App-wide motion library
  - Affected: shared/styles/gesture-animations.scss, new shared/animations.ts
  - Provide fade-slide, scale-in, and stagger utilities; apply to lists and modals.
  - Acceptance: No conflicting animations; consistent easing across app.
- Haptic feedback hooks
  - Affected: core/services/haptic-feedback.service.ts, use in like/send/reveal.
  - Acceptance: Haptics fire only on supported devices; configurable in settings.

### Phase 5: Personalization & Theming (Weeks 5-6)
- Mood-driven dynamic theme
  - Affected: shared/components/mood-selector, core/services/theme.service.ts
  - Adjust accent colors, backgrounds; save per user.
  - Acceptance: Theme switch < 150ms; passes contrast checks.
- Accessibility color guardrails
  - Affected: shared/utils/color-accessibility.utils.ts, shared/styles/_accessibility-colors.scss
  - Live contrast validation with fallback palettes.
  - Acceptance: Minimum WCAG AA contrast achieved app-wide.

### Phase 6: Performance & Perceived Speed (Weeks 6-7)
- Virtualize long lists
  - Affected: features/messages/messages.component.ts, features/discover/discover.component.ts
  - Use cdk-virtual-scroll-viewport for chats/matches.
  - Acceptance: Scroll jank eliminated for 1k+ items.
- Smart prefetch & skeletons
  - Affected: route configs, shared skeletons
  - Prefetch next-likely routes; skeletons visible < 100ms after nav.
  - Acceptance: TTI reduction by ≥15% on 3G.
- Image pipeline
  - Affected: uploads and profile photos
  - Client-side compress to responsive sizes; lazy-load with loading="lazy" and srcset.
  - Acceptance: Total bytes on home/profile reduced ≥30%.

### Phase 7: PWA & Mobile UX (Weeks 7-8)
- Pull-to-refresh & bottom sheets
  - Affected: shared/components/mobile-ui, feature lists
  - Native-feel refresh, bottom sheet for quick actions.
  - Acceptance: Smooth gesture; 60fps on modern devices.
- Deep links from push
  - Affected: core/services/pwa.service.ts, router handling
  - Navigate directly to chat/revelation from notification click.
  - Acceptance: Cold start deep-link success rate ≥ 95%.

### Phase 8: Accessibility (Weeks 8-9)
- Focus, live regions, reduced motion
  - Affected: core/services/accessibility.service.ts, components across app
  - Strong focus rings; announce new messages; global reduced-motion toggle.
  - Acceptance: Keyboard-only flows pass; screen reader announces key events.

### Phase 9: Safety & Trust (Weeks 9-10)
- Inline safety nudges
  - Affected: messages.component.ts
  - Gentle hints on potentially risky content (client-only nudge, server still authoritative).
  - Acceptance: CTA to edit/learn more visible, not blocking.
- One-tap report & safety tips
  - Affected: chat header, shared/components/toast
  - Quick report sheet; rotating “Safety Tips” for new users.

### Phase 10: Analytics & Experimentation (Weeks 10-11)
- Analytics directive & event map
  - Affected: shared/directives/analytics.directive.ts
  - Standardize CTA tracking; align to backend analytics schema.
  - Acceptance: 0 console errors; events hydrate ClickHouse.
- A/B hooks
  - Affected: onboarding/revelation UIs
  - Variant toggles via config/feature flags; experiment IDs appended to events.

### Phase 11: Internationalization (Week 12)
- i18n scaffolding
  - Affected: all text-bearing components
  - Externalize strings, language toggle, RTL audit.
  - Acceptance: English + one pilot locale fully translated.

### Cross-cutting acceptance criteria
- Performance: CLS < 0.1, LCP < 2.5s (3G), TTI -15% vs baseline
- Stability: No uncaught errors; error boundary wraps high-risk screens
- A11y: WCAG AA contrast, keyboard navigable, screen-reader annotations for new messages

### Dependencies & Risks
- Backend receipts/presence over WS for richer chat states
- Image CDN or caching strategy for media-heavy views
- A/B and analytics schema agreement with backend

### Metrics to track
- Message send success rate; offline -> delivered conversion
- Onboarding completion rate; revelation day streak retention
- Time-to-first-message; session duration uplift

### Implementation notes (where to start)
- Start with Phase 1 optimistic messaging (low risk, high impact)
- Introduce animation utilities gradually; guard with reduced-motion
- Use feature flags for experimental flows (onboarding, prompts)

### Nice-to-haves (later)
- In-app theme builder with user presets
- Profile video snippets with auto-muted autoplay on hover/tap
- Shared Lottie/JSON animations library for celebrations


