# UI/UX Redesign — Design Spec

**Date:** 2026-04-18
**Author:** Alexander Sebhat
**Status:** Approved via brainstorming session

## Context

The previous UI polish initiative (2026-04-16) claimed comprehensive emoji cleanup and styling fixes but was, in practice, partial. Runtime emoji remained buried in CSS pseudo-elements (`gesture-animations.scss`, `swipe-gestures.scss`, `offline.html`), two competing color systems coexisted (`_emotional-colors.scss` at 538 lines + `_accessibility-colors.scss` at 414 lines), mobile viewport bugs remained (`100vh` overlapping soft keyboard in messaging), and `style="display:none"` inline overrides were layered on top of the cascade.

This spec defines a full foundation rebuild plus targeted redesigns for the five highest-traffic pages. The aesthetic direction is **Warm Intimate** — terracotta, sage, and cream, with Fraunces italic display type and Inter for UI — chosen as distinctive from generic dating-app conventions and aligned with the "Soul Before Skin / Dinner First" brand premise.

## Goals

1. Replace the two competing color systems with a single, ~80-line `_tokens.scss`.
2. Establish a consistent type scale (Fraunces display + Inter UI) with exactly six size steps.
3. Define four button variants × three sizes, one input style, two card layouts, and a unified chip system as reusable primitives.
4. Split the current conflated `navigation.component` into a mobile tab bar and a desktop top nav, each with one clear responsibility.
5. Redesign the five highest-traffic pages (Landing, Onboarding, Discover, Messaging, Profile) against the new foundation.
6. Eliminate every unintentional emoji in CSS pseudo-elements, component templates, and runtime data arrays. Preserve intentional emoji (message reactions) as a contextual feature, not persistent chrome.
7. Fix the messaging composer / soft-keyboard overlap by replacing `100vh` with `100dvh` and removing inline `display:none` overrides.

## Non-Goals

- No backend schema changes.
- No new features beyond the photo-consent-on-day-7 flow already shipped.
- No internationalization work (English-only copy for now).
- No A/B testing infrastructure for the redesign — ship the new design; measure after.
- No migration to Tailwind or a non-Material component library.
- No redesign of secondary pages (Connections list, Revelations timeline, Notifications, Settings, Dinner planning, Match celebration, Auth screens) beyond a "consistency pass" where they inherit tokens and base components. Bespoke redesigns for those pages are out of scope.

## Scope Decision

Approach: **Hybrid — foundation first, then top pages.**

Phase 1 rebuilds the design system (tokens, type, spacing, primitives, navigation). Phase 2 redesigns the five highest-traffic pages on top of Phase 1. Phase 3 is a consistency pass over remaining pages — they inherit the new tokens and primitives but receive no bespoke redesign.

## Architecture

### Token layer

Single source of truth: `angular-frontend/src/styles/_tokens.scss`.

- 12 named CSS custom properties for colors (see Color Palette below).
- 10 named custom properties for spacing (4, 8, 12, 16, 20, 24, 32, 40, 48, 64px — exposed as `--space-1` through `--space-16`).
- 5 radius values (`--radius-sm` 4, `--radius-md` 8, `--radius-lg` 12, `--radius-xl` 20, `--radius-pill` 999).
- 3 elevation shadows (`--elevation-sm`, `--elevation-md`, `--elevation-lg`).
- Six typography size tokens (see Type Scale).

Dark mode is a second palette expressed as the same custom-property names under a `[data-theme='dark']` selector. No additional tokens required.

**Deleted:** `_emotional-colors.scss` (538 lines) and `_accessibility-colors.scss` (414 lines). All downstream imports updated.

### Material theme integration

`angular-frontend/src/styles/_material-theme.scss` overrides Angular Material 19's M3 theme using the token values above:

- Primary palette generated from `--color-primary` (#D17B5A).
- Secondary palette generated from `--color-accent` (#9BAE8A).
- Neutral palette generated from `--color-text` (#2F2420) with warmth preserved.
- Typography config points to Inter for body + heading; Fraunces is opt-in via a utility class `.display-serif`.
- Density: default (0) for forms and lists; comfortable (+1) for dialogs.
- Shape: radii driven by our token scale, not Material's default.

### Component primitives

Six primitives live in `angular-frontend/src/app/shared/ui/`:

- `DfButtonDirective` — applies our variant/size classes to native `<button>` and `<a>`. Variants: `primary`, `secondary`, `ghost`, `danger`. Sizes: `sm`, `md`, `lg`. Replaces ad-hoc `<button type="button" class="custom-class">` usage throughout.
- `DfCardComponent` — two layouts: `connection` (elevated, white surface) and `revelation` (flat, cream surface with sage border).
- `DfChipComponent` — three purposes: stage (filled with tonal tint), interest (neutral), counter (outline).
- `DfInputDirective` — applies the unified visible-border outlined style to Material's `matFormField` and raw inputs, replacing the four-style drift.
- `DfAvatarComponent` — monogram-first (no photo placeholder); opt-in photo URL.
- `DfPageShellComponent` — provides the responsive container with correct max-widths (480 chat, 720 reading, 1120 grid) and padding (16/24/32).

### Navigation

`NavigationComponent` is deleted. Two replacements:

- `MobileTabBarComponent` — fixed bottom, 5 tabs, `env(safe-area-inset-bottom)` padding, `100dvh`-aware. Shown only below the 768px breakpoint.
- `DesktopTopNavComponent` — 64px top bar, logo + 4 primary tabs + notification bell + avatar dropdown. Profile lives in the avatar dropdown on desktop (not a tab); on mobile, Profile is the 5th tab.

### Page redesigns

Each Phase-2 page gets its own directory under `angular-frontend/src/app/features/` with a `*.component.ts` rewritten to use the new shell, primitives, and tokens. Page-specific details below in Feature-by-Feature section.

## Color Palette

| Token                   | Value     | Purpose                                            |
|-------------------------|-----------|----------------------------------------------------|
| `--color-bg`            | `#FBF3EC` | Page background (warm cream)                       |
| `--color-surface`       | `#FFFFFF` | Cards, dialogs, composer                           |
| `--color-surface-alt`   | `#F5EDE4` | Inactive tab bg, chip bg, incoming message bubble  |
| `--color-border`        | `#E8DDD0` | Hairline dividers, input borders                   |
| `--color-primary`       | `#D17B5A` | Primary CTAs, outgoing bubble, active tab tint     |
| `--color-primary-hover` | `#B8684A` | Hover state for primary                            |
| `--color-accent`        | `#9BAE8A` | Sage — success, compatibility, revelation accent   |
| `--color-accent-soft`   | `#E8B9A0` | Blush — highlights, avatar gradients               |
| `--color-text`          | `#2F2420` | Primary text (warm near-black)                     |
| `--color-text-muted`    | `#8A6E5F` | Secondary text, helper copy                        |
| `--color-danger`        | `#C4564B` | Destructive actions, error states                  |
| `--color-warning`       | `#E0A060` | Warning banners, pending states                    |

Dark mode values are deferred to Phase 1 implementation — same names, different values — and are out of scope for this spec's detailed list.

## Type Scale

Two typefaces:

- **Fraunces** (500 italic + 500 regular) — display only. Google Fonts.
- **Inter** (400, 500, 600, 700) — everything else. Google Fonts.

Six size tokens:

| Token           | Size/line-height | Weight | Usage                             |
|-----------------|------------------|--------|-----------------------------------|
| `--type-h1`     | 32 / 36          | 600    | Page headlines                    |
| `--type-h2`     | 24 / 30          | 600    | Section headings                  |
| `--type-h3`     | 18 / 24          | 600    | Card headers                      |
| `--type-body`   | 16 / 24          | 400    | Default body copy                 |
| `--type-small`  | 14 / 20          | 400    | Secondary body, helper text       |
| `--type-caption`| 12 / 16          | 500    | Labels, uppercase tags, timestamps|

Display serif is applied via a utility class `.display-serif` on opt-in elements (landing hero, onboarding question headlines, quoted revelation copy on cards and profile).

Caption usage uses `letter-spacing: 0.08em` and `text-transform: uppercase`.

## Feature-by-Feature Redesigns

### Page 01 — Landing

**Route:** `/` (unauthenticated)
**File:** `angular-frontend/src/app/features/landing/landing.component.{ts,html,scss}`

**Hero:** Three-line stacked "Soul / before / skin." in Fraunces italic, left-aligned, 56px on mobile / 72px on desktop. Subhead below in Inter 400, muted text color, 14-16px: "Seven days of progressive revelation. Then, if it feels right — dinner."

**How-it-works card:** White surface, elevation-sm, three rows with outlined Material Icons in terracotta (`psychology`, `auto_stories`, `restaurant`). Each row is 20-24px body text. This section replaces both the current hero-orb animation and the "Why Dinner First?" section (merged into one card).

**Single primary CTA:** "Begin your story" (df-btn-primary df-btn-lg). Sign-in as a ghost link top-right of the page.

**What dies:**
- Hero "orbs" with emoji (`favorite`, `auto_awesome`).
- `filter: drop-shadow()` on the hero headline.
- Separate "Why Dinner First?" section.
- Landing-page testimonials block (not yet populated).
- `landing.component.scss` gradient backgrounds on feature tiles.

### Page 02 — Onboarding (Emotional questions)

**Route:** `/onboarding`
**File:** `angular-frontend/src/app/features/onboarding/` — `onboarding-welcome.component.ts` retired; replaced by `onboarding-flow.component.ts` + `onboarding-question.component.ts`.

One question per screen across three screens. Thin top progress bar (`--color-primary` fill on `--color-border` track, 4px tall). "Back" / "Continue" buttons at the bottom; "Skip" ghost link top-right for optional questions.

**Question rendering:** Fraunces italic, 24/30, `--color-text`. Helper microcopy below in Inter 400 `--color-text-muted`: "Take your time. There's no right answer — only honest ones."

**Textarea:** df-input with visible border, 90px min-height, 500-char hard cap. Character counter (`127 / 500`) shown below the field, right-aligned. Counter color goes warning at 450 and danger at 500; the field stops accepting input and the Continue button disables if somehow at 500.

**What dies:**
- The current "welcome" marketing screen with bulleted benefits (~14 emoji currently).
- Multi-question-per-page form. Three screens, three questions.

### Page 03 — Discover

**Route:** `/discover`
**File:** `angular-frontend/src/app/features/discover/discover.component.{ts,html,scss}`

**Headline:** Fraunces italic "N souls for today." where N is the actual count (1–3 per day by algorithm). Subhead Inter 400 muted: "Based on what you value."

**Card stack:** Not a swipe deck. Top card is the focal connection card (white surface, elevation-sm, 20px radius). Below it, up to two peek cards at 60% opacity showing only avatar + name + compatibility. Tapping a peek card scrolls it to focal position. No swipe-to-dismiss gesture.

**Focal card contents:** Stage chip (top-left), avatar monogram (top-right), display name, one-line bio, quote preview in cream `--color-surface-alt` container with sage left border containing a single-line revelation excerpt, "Pass" (df-btn-secondary) + "Begin" (df-btn-primary) buttons side-by-side.

**What dies:**
- `gesture-animations.scss` (14KB, 5 emoji pseudo-elements).
- `swipe-gestures.scss` (2 emoji pseudo-elements).
- Swipe-deck interaction model (replaced by scroll-through focal card).
- The word "Match" in CTAs — replaced by "Begin" (reinforces 7-day journey framing).

### Page 04 — Messaging / Chat

**Route:** `/messages/:connectionId`
**File:** `angular-frontend/src/app/features/messaging/messaging.component.{ts,html,scss}`

**Page shell:** `DfPageShellComponent` with `variant="chat"` — max-width 480px on desktop (centered), `height: 100dvh` on mobile. Body is a flex column: header, stage banner, messages, composer.

**Header (56px):** Back arrow, avatar monogram, name + "Day N · M% compatibility" subtitle, overflow menu. No shadow; hairline border-bottom.

**Stage banner:** Terracotta chip stretched full width under header, showing current day + prompt ("Day 3 · A meaningful experience"). Always visible; taps the revelation composer modal.

**Message list:** Incoming bubbles `--color-surface-alt` on left with 14/14/14/4 radius. Outgoing bubbles `--color-primary` on right with 14/14/4/14 radius. Asymmetric radii provide direction without tails. Timestamp + read receipt below each bubble in 10px `--color-text-muted`.

**Composer (one row, ~48px):** Plus icon (opens attachment sheet: revelation, photo-if-unlocked), single-pill input field (`--color-surface-alt`, `--radius-pill`), send icon. The composer is a flex child of the shell — soft keyboard pushes content naturally because of `100dvh`, not `100vh`.

**Emoji reactions:** Preserved. Long-press on a message opens a contextual popover with 6 default reactions. Picker is NOT persistent chrome. Emoji within typed messages comes from the user's OS keyboard — no in-app emoji picker for composition.

**What dies:**
- All `style="display: none;"` inline overrides (lines 237, 242, 247, 254, 267, 274 of current template).
- The three-row composer with persistent emoji picker (11 emoji in the quick-reaction bar).
- `100vh` on the messaging container.
- Custom `<button type="button">` classes on attachments — replaced by icon buttons with proper `aria-label`s.

### Page 05 — Profile (self view)

**Route:** `/profile`
**File:** `angular-frontend/src/app/features/profile/profile.component.{ts,html,scss}` — edit flow remains in `profile-edit.component.ts`.

**Header:** "Your profile" (Inter 600 13px) left, "Edit" ghost link right.

**Identity block:** 72px monogram avatar (gradient accent-soft → primary). Below: display name (20/24 Inter 600), location + age (small muted).

**Interests chips row:** Horizontal scrolling chips with overflow fade on mobile; wrap on desktop.

**Value cards:** Each of the three onboarding answers rendered as its own card — white surface, 14px radius, sage left border. Card label in caption uppercase sage; answer body in Fraunces italic 14/20 dark text.

**Photo section (collapsed by default):** Card with message: "Photos are shared per-connection, on Day 7, with mutual consent." Expands to show photos the user has uploaded (not yet shared); upload button inside.

**What dies:**
- Multi-tab profile (interests / values / prompts / photos). Flattened to one canvas.
- Photo grid as the profile's first surface.

## Phase 3 (Consistency Pass)

These pages inherit tokens + primitives + navigation shell but do not receive bespoke redesigns in this spec. Scope is limited to:

- Replace old color custom properties with `--color-*` tokens.
- Swap old buttons/inputs/chips for primitives.
- Remove any remaining emoji from templates, CSS pseudo-elements, and data arrays.
- Fix any obvious layout breakage introduced by the token/primitive swap.

Affected pages: Connections list, Revelations timeline, Notifications, Settings, Dinner planning, Match celebration, Auth (login/register). Exact fix list per page is deferred to the implementation plan.

## Testing Strategy

- **Visual regression:** Baseline screenshots (Playwright) for the 5 Phase-2 pages at 375px, 768px, 1280px after Phase 1 ships. Any Phase-3 change must not break these baselines unintentionally.
- **Unit tests:** Each new primitive (`DfButtonDirective`, `DfCardComponent`, etc.) gets a spec file exercising its variants and a11y attributes.
- **Navigation tests:** `MobileTabBarComponent` and `DesktopTopNavComponent` each have routing tests covering active-tab highlighting for all 5 destinations.
- **Accessibility:** Contrast ratios for all token pairs verified at spec-implementation time (targets: WCAG AA for body text, AAA for critical copy). Focus visible on every interactive element.
- **No new emoji:** CI check — grep for emoji Unicode ranges in `angular-frontend/src/**/*.{ts,html,scss}` excluding `messaging` feature. Non-zero count fails the build.

## Rollout Plan

Three phases, each landing as its own PR:

1. **Phase 1 — Foundation.** Tokens, type, Material theme override, primitives, navigation split. No user-visible page changes yet; navigation shell may look slightly different.
2. **Phase 2 — Priority pages.** Five pages redesigned against Phase 1. Shipped as one PR to avoid mid-transition inconsistency.
3. **Phase 3 — Consistency pass.** Remaining pages get token/primitive swap + emoji purge.

## Success Criteria

- Zero unintentional emoji in code (grep yields only `angular-frontend/src/app/features/messaging/` matches).
- One and only one color-token file (`_tokens.scss`) imported across the frontend.
- One and only one form-field style in use.
- Messaging composer never overlaps the tab bar or gets obscured by soft keyboard across iOS Safari, Android Chrome, and desktop Chrome/Firefox/Safari.
- All five redesigned pages score ≥ 95 on Lighthouse accessibility.
- No page regresses in Lighthouse performance vs the current baseline.

## Open Questions

None at spec-approval time. Implementation plan will surface any additional decisions (e.g., exact shadow values, exact dark-mode palette) as the work unfolds.
