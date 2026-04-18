# UI Redesign Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Angular frontend's design foundation — tokens, typography, Material theme, six UI primitives, and a responsive navigation split — without user-visible page changes beyond navigation chrome.

**Architecture:** A single SCSS token file drives one Angular Material 18 theme override plus six standalone primitive directives/components under `src/app/shared/ui/`. The existing monolithic `NavigationComponent` is replaced by `MobileTabBarComponent` + `DesktopTopNavComponent`, wrapped in a `ResponsiveNavComponent` that picks the right one at the 768px breakpoint. Legacy files (`_emotional-colors.scss`, `_accessibility-colors.scss`, gesture/icon SCSS, old navigation) are deleted. A temporary legacy-alias block inside `_tokens.scss` keeps unmigrated files building during the migration, then is removed at the end of Phase 1.

**Tech Stack:** Angular 18 (standalone components), Angular Material 18 with M3 theming, TypeScript 5.4, SCSS `@use`, Jasmine + Karma, Google Fonts (Fraunces + Inter + Material Icons Outlined).

**Reference spec:** `docs/superpowers/specs/2026-04-18-ui-redesign-design.md`

**Branch assumption:** Work happens on a `feature/ui-redesign-phase1` branch off `development`, created before Task 1.

---

## File Structure

**Created:**
- `angular-frontend/src/styles/_tokens.scss` — color/spacing/radius/elevation/type tokens (light + dark), plus a temporary legacy-alias block.
- `angular-frontend/src/styles/_material-theme.scss` — Angular Material 18 theme config.
- `angular-frontend/src/app/shared/ui/index.ts` — barrel export.
- `angular-frontend/src/app/shared/ui/button/df-button.directive.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/ui/chip/df-chip.component.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/ui/card/df-card.component.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/ui/input/df-input.directive.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/ui/avatar/df-avatar.component.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/ui/page-shell/df-page-shell.component.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/navigation/mobile-tab-bar.component.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.{ts,spec.ts,scss}`
- `angular-frontend/src/app/shared/navigation/responsive-nav.component.{ts,spec.ts,scss}`
- `angular-frontend/scripts/check-no-emoji.sh` — CI emoji check.
- `angular-frontend/scripts/migrate-tokens.sh` — one-shot sed migration.

**Modified:**
- `angular-frontend/src/index.html` — swap Roboto → Fraunces + Inter + Material Icons Outlined.
- `angular-frontend/src/styles.scss` — rewritten to ~30 lines: `@use` tokens + material theme, minimal resets.
- `angular-frontend/src/app/app.component.ts` — swap `NavigationComponent` import for `ResponsiveNavComponent`.
- `angular-frontend/src/app/app.component.html` — use `<app-responsive-nav>` selector.
- ~15 feature SCSS/TS files — legacy token name → new `--color-*` name (via migration script).
- `angular-frontend/package.json` — add `lint:no-emoji` script wired to `check-no-emoji.sh`.

**Deleted:**
- `angular-frontend/src/app/shared/styles/_emotional-colors.scss`
- `angular-frontend/src/app/shared/styles/_accessibility-colors.scss`
- `angular-frontend/src/app/shared/styles/_icon-standards.scss`
- `angular-frontend/src/app/shared/styles/_swipe-gestures.scss`
- `angular-frontend/src/app/shared/styles/gesture-animations.scss`
- `angular-frontend/src/app/shared/components/navigation/navigation.component.ts`
- `angular-frontend/src/app/shared/components/navigation/navigation-demo.component.ts`
- Legacy alias block inside `_tokens.scss` (removed in Task 20 after migration completes).

---

## Task 1: Font Loading Swap

**Files:**
- Modify: `angular-frontend/src/index.html`

- [ ] **Step 1: Replace the Roboto font link with Fraunces + Inter + Material Icons Outlined**

Replace lines 9-10 of `angular-frontend/src/index.html`:

```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;1,9..144,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">
```

- [ ] **Step 2: Start the dev stack and verify fonts load**

Run: `./start-app.sh` (from repo root), wait for frontend to be ready, then open `http://localhost:4200`.
Expected: DevTools Network tab shows successful requests to `fonts.googleapis.com` for Fraunces, Inter, and Material Icons Outlined. Existing page still renders (unstyled body text may now fall back to sans-serif — that's fine; styling arrives in later tasks).

- [ ] **Step 3: Commit**

```bash
git add angular-frontend/src/index.html
git commit -m "chore(frontend): swap font stack to Fraunces + Inter + Material Icons Outlined"
```

---

## Task 2: Create `_tokens.scss`

**Files:**
- Create: `angular-frontend/src/styles/_tokens.scss`

- [ ] **Step 1: Write the full token file**

Create `angular-frontend/src/styles/_tokens.scss` with this exact content:

```scss
// Design tokens — single source of truth for UI redesign Phase 1.
// Spec: docs/superpowers/specs/2026-04-18-ui-redesign-design.md

:root {
  // Color — light (default)
  --color-bg: #FBF3EC;
  --color-surface: #FFFFFF;
  --color-surface-alt: #F5EDE4;
  --color-border: #E8DDD0;
  --color-primary: #D17B5A;
  --color-primary-hover: #B8684A;
  --color-accent: #9BAE8A;
  --color-accent-soft: #E8B9A0;
  --color-text: #2F2420;
  --color-text-muted: #8A6E5F;
  --color-danger: #C4564B;
  --color-warning: #E0A060;

  // Spacing (pixel values exposed as rem-equivalent literals)
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  // Radii
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 20px;
  --radius-pill: 999px;

  // Elevation
  --elevation-sm: 0 1px 2px rgba(47, 36, 32, 0.06), 0 1px 3px rgba(47, 36, 32, 0.04);
  --elevation-md: 0 4px 8px rgba(47, 36, 32, 0.08), 0 2px 4px rgba(47, 36, 32, 0.04);
  --elevation-lg: 0 12px 24px rgba(47, 36, 32, 0.12), 0 4px 8px rgba(47, 36, 32, 0.06);

  // Typography — size / line-height pairs + weights
  --type-h1-size: 32px;    --type-h1-lh: 36px;    --type-h1-weight: 600;
  --type-h2-size: 24px;    --type-h2-lh: 30px;    --type-h2-weight: 600;
  --type-h3-size: 18px;    --type-h3-lh: 24px;    --type-h3-weight: 600;
  --type-body-size: 16px;  --type-body-lh: 24px;  --type-body-weight: 400;
  --type-small-size: 14px; --type-small-lh: 20px; --type-small-weight: 400;
  --type-caption-size: 12px; --type-caption-lh: 16px; --type-caption-weight: 500;

  // Font families
  --font-display: 'Fraunces', Georgia, serif;
  --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  // -----------------------------------------------------------------
  // LEGACY ALIASES — REMOVE IN TASK 20.
  // Keep pre-migration files building during the SCSS migration run.
  // -----------------------------------------------------------------
  --emotional-primary: var(--color-primary);
  --emotional-primary-hover: var(--color-primary-hover);
  --emotional-accent: var(--color-accent);
  --emotional-accent-soft: var(--color-accent-soft);
  --emotional-danger: var(--color-danger);
  --emotional-warning: var(--color-warning);
  --df-primary: var(--color-primary);
  --df-accent: var(--color-accent);
  --df-bg: var(--color-bg);
  --df-surface: var(--color-surface);
  --df-text: var(--color-text);
  --df-text-muted: var(--color-text-muted);
  --text-primary: var(--color-text);
  --text-secondary: var(--color-text-muted);
  --surface-primary: var(--color-surface);
  --surface-secondary: var(--color-surface-alt);
}

[data-theme='dark'] {
  --color-bg: #1A1512;
  --color-surface: #241D18;
  --color-surface-alt: #2E261F;
  --color-border: #3D332A;
  --color-primary: #E08F6E;
  --color-primary-hover: #F0A07F;
  --color-accent: #B5C9A1;
  --color-accent-soft: #F0C8B0;
  --color-text: #F5EDE4;
  --color-text-muted: #B59E8A;
  --color-danger: #E06A5F;
  --color-warning: #F0B478;

  --elevation-sm: 0 1px 2px rgba(0, 0, 0, 0.32), 0 1px 3px rgba(0, 0, 0, 0.24);
  --elevation-md: 0 4px 8px rgba(0, 0, 0, 0.40), 0 2px 4px rgba(0, 0, 0, 0.24);
  --elevation-lg: 0 12px 24px rgba(0, 0, 0, 0.48), 0 4px 8px rgba(0, 0, 0, 0.32);
}

// Display-serif utility — opt-in Fraunces italic on hero/question/quote copy.
.display-serif {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 500;
}

// Caption utility — uppercase tags/labels.
.caption {
  font-family: var(--font-ui);
  font-size: var(--type-caption-size);
  line-height: var(--type-caption-lh);
  font-weight: var(--type-caption-weight);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
```

- [ ] **Step 2: Commit**

```bash
git add angular-frontend/src/styles/_tokens.scss
git commit -m "feat(frontend): add design tokens file with light/dark palettes and legacy aliases"
```

---

## Task 3: Create `_material-theme.scss`

**Files:**
- Create: `angular-frontend/src/styles/_material-theme.scss`

- [ ] **Step 1: Write the Material theme override**

Create `angular-frontend/src/styles/_material-theme.scss`:

```scss
@use '@angular/material' as mat;

@include mat.core();

// Warm terracotta primary palette (approximated from --color-primary #D17B5A).
$warm-primary: (
  50: #FBF0EA,
  100: #F5D9CA,
  200: #EEBFA7,
  300: #E6A484,
  400: #DD8F6C,
  500: #D17B5A,
  600: #B8684A,
  700: #9C553B,
  800: #7F432D,
  900: #5C2F1F,
  contrast: (
    50: #2F2420,
    100: #2F2420,
    200: #2F2420,
    300: #2F2420,
    400: #2F2420,
    500: #FFFFFF,
    600: #FFFFFF,
    700: #FFFFFF,
    800: #FFFFFF,
    900: #FFFFFF,
  )
);

// Sage accent palette (approximated from --color-accent #9BAE8A).
$sage-accent: (
  50: #F1F4EE,
  100: #DCE3D4,
  200: #C4D0B8,
  300: #ACBC9C,
  400: #9BAE8A,
  500: #87A075,
  600: #6F8860,
  700: #58704C,
  800: #425839,
  900: #2C3D26,
  contrast: (
    50: #2F2420,
    100: #2F2420,
    200: #2F2420,
    300: #2F2420,
    400: #2F2420,
    500: #FFFFFF,
    600: #FFFFFF,
    700: #FFFFFF,
    800: #FFFFFF,
    900: #FFFFFF,
  )
);

// Danger / warn palette (approximated from --color-danger #C4564B).
$warn-palette: (
  50: #FAE9E7,
  100: #F2C7C2,
  200: #E8A29A,
  300: #DE7D73,
  400: #D46559,
  500: #C4564B,
  600: #AA483E,
  700: #8C3A32,
  800: #6E2C26,
  900: #4F1F1B,
  contrast: (
    50: #2F2420,
    100: #2F2420,
    200: #2F2420,
    300: #2F2420,
    400: #2F2420,
    500: #FFFFFF,
    600: #FFFFFF,
    700: #FFFFFF,
    800: #FFFFFF,
    900: #FFFFFF,
  )
);

$df-primary: mat.define-palette($warm-primary, 500, 300, 700);
$df-accent:  mat.define-palette($sage-accent, 400, 200, 700);
$df-warn:    mat.define-palette($warn-palette, 500, 300, 700);

$df-typography: mat.define-typography-config(
  $font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  $headline-1: mat.define-typography-level(32px, 36px, 600),
  $headline-2: mat.define-typography-level(24px, 30px, 600),
  $headline-3: mat.define-typography-level(18px, 24px, 600),
  $body-1:     mat.define-typography-level(16px, 24px, 400),
  $body-2:     mat.define-typography-level(14px, 20px, 400),
  $caption:    mat.define-typography-level(12px, 16px, 500),
);

$df-light-theme: mat.define-light-theme((
  color: (primary: $df-primary, accent: $df-accent, warn: $df-warn),
  typography: $df-typography,
  density: 0,
));

$df-dark-theme: mat.define-dark-theme((
  color: (primary: $df-primary, accent: $df-accent, warn: $df-warn),
  typography: $df-typography,
  density: 0,
));

@include mat.all-component-themes($df-light-theme);
@include mat.all-component-typographies($df-typography);

[data-theme='dark'] {
  @include mat.all-component-colors($df-dark-theme);
}
```

- [ ] **Step 2: Commit**

```bash
git add angular-frontend/src/styles/_material-theme.scss
git commit -m "feat(frontend): add Angular Material 18 theme config with warm primary + sage accent"
```

---

## Task 4: Rewrite `styles.scss`

**Files:**
- Modify: `angular-frontend/src/styles.scss` (full rewrite — from 519 lines to ~40)

- [ ] **Step 1: Replace the entire contents of `angular-frontend/src/styles.scss`**

```scss
@use 'styles/tokens';
@use 'styles/material-theme';

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-ui);
  font-size: var(--type-body-size);
  line-height: var(--type-body-lh);
  font-weight: var(--type-body-weight);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

*, *::before, *::after {
  box-sizing: border-box;
}

a {
  color: var(--color-primary);
  text-decoration: none;
  &:hover { color: var(--color-primary-hover); }
}

button {
  font-family: inherit;
  font-size: inherit;
}

:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

// Material Icons Outlined — default to outlined variant app-wide.
.mat-icon,
.material-icons,
.material-icons-outlined {
  font-family: 'Material Icons Outlined', 'Material Icons', sans-serif;
  font-feature-settings: 'liga';
}
```

- [ ] **Step 2: Rebuild the frontend and verify it compiles**

Run: `docker compose -f docker-compose.dev.yml logs -f frontend` in one terminal, then touch any component file to trigger rebuild.
Expected: Angular dev server recompiles with no SCSS errors. Some features may look partially unstyled (expected — they're still using legacy tokens that resolve via the alias block).

- [ ] **Step 3: Commit**

```bash
git add angular-frontend/src/styles.scss
git commit -m "refactor(frontend): collapse styles.scss to token-driven minimal globals"
```

---

## Task 5: Migration Script for Legacy Tokens

**Files:**
- Create: `angular-frontend/scripts/migrate-tokens.sh`

- [ ] **Step 1: Write the migration script**

Create `angular-frontend/scripts/migrate-tokens.sh`:

```bash
#!/usr/bin/env bash
# One-shot migration: rename legacy CSS custom properties to new --color-* tokens.
# Run from repo root: bash angular-frontend/scripts/migrate-tokens.sh

set -euo pipefail

ROOT="angular-frontend/src"

FILES=$(grep -rl --include='*.scss' --include='*.ts' --include='*.html' \
  -e '--emotional-primary' \
  -e '--emotional-accent' \
  -e '--emotional-danger' \
  -e '--emotional-warning' \
  -e '--df-primary' \
  -e '--df-accent' \
  -e '--df-bg' \
  -e '--df-surface' \
  -e '--df-text' \
  -e '--text-primary' \
  -e '--text-secondary' \
  -e '--surface-primary' \
  -e '--surface-secondary' \
  "$ROOT" || true)

if [ -z "$FILES" ]; then
  echo "No files to migrate."
  exit 0
fi

echo "Migrating:"
echo "$FILES"

for f in $FILES; do
  # Order matters: longer names first so prefixes don't swallow suffixes.
  sed -i.bak \
    -e 's/--emotional-primary-hover/--color-primary-hover/g' \
    -e 's/--emotional-primary/--color-primary/g' \
    -e 's/--emotional-accent-soft/--color-accent-soft/g' \
    -e 's/--emotional-accent/--color-accent/g' \
    -e 's/--emotional-danger/--color-danger/g' \
    -e 's/--emotional-warning/--color-warning/g' \
    -e 's/--df-primary/--color-primary/g' \
    -e 's/--df-accent/--color-accent/g' \
    -e 's/--df-bg/--color-bg/g' \
    -e 's/--df-surface/--color-surface/g' \
    -e 's/--df-text-muted/--color-text-muted/g' \
    -e 's/--df-text/--color-text/g' \
    -e 's/--text-primary/--color-text/g' \
    -e 's/--text-secondary/--color-text-muted/g' \
    -e 's/--surface-primary/--color-surface/g' \
    -e 's/--surface-secondary/--color-surface-alt/g' \
    "$f"
  rm -f "${f}.bak"
done

echo "Done. Review with: git diff"
```

- [ ] **Step 2: Make executable and run it**

```bash
chmod +x angular-frontend/scripts/migrate-tokens.sh
bash angular-frontend/scripts/migrate-tokens.sh
```

Expected: Prints a list of ~15 files touched. No errors.

- [ ] **Step 3: Verify build still compiles**

Watch `docker compose -f docker-compose.dev.yml logs -f frontend`. Touch a file if needed to trigger rebuild.
Expected: No SCSS errors. Pages render with same colors (since legacy aliases still resolve, and migrated files now directly reference `--color-*`).

- [ ] **Step 4: Commit**

```bash
git add angular-frontend/scripts/migrate-tokens.sh angular-frontend/src
git commit -m "refactor(frontend): migrate legacy custom properties to --color-* tokens"
```

---

## Task 6: Verify Foundation Build

**Files:** None (verification only).

- [ ] **Step 1: Full rebuild with clean cache**

```bash
docker compose -f docker-compose.dev.yml restart frontend
docker compose -f docker-compose.dev.yml logs -f frontend
```

Expected: Frontend compiles with no errors and no warnings related to missing SCSS modules or undefined custom properties.

- [ ] **Step 2: Open the app in a browser**

Visit `http://localhost:4200`. Click through Landing, Login, Register.
Expected: Pages render. Colors may differ subtly from before (warm cream background replacing previous grey). Typography shows Inter; no serif anywhere yet (intentional — `.display-serif` is opt-in).

- [ ] **Step 3: Run existing unit tests as a regression check**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

Expected: Whatever test count was passing before Phase 1 still passes. If a test asserts against a legacy token name in the DOM, fix the assertion (don't regress the migration).

- [ ] **Step 4: Commit any test fixes**

```bash
git add angular-frontend
git commit -m "test(frontend): align existing specs with migrated token names"
```

(Skip the commit if no fixes were needed.)

---

## Task 7: `DfButtonDirective`

**Files:**
- Create: `angular-frontend/src/app/shared/ui/button/df-button.directive.ts`
- Create: `angular-frontend/src/app/shared/ui/button/df-button.directive.spec.ts`
- Create: `angular-frontend/src/app/shared/ui/button/df-button.directive.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/ui/button/df-button.directive.spec.ts`:

```typescript
import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfButtonDirective } from './df-button.directive';

@Component({
  standalone: true,
  imports: [DfButtonDirective],
  template: `
    <button dfButton>default</button>
    <button dfButton variant="primary" size="md">primary md</button>
    <button dfButton variant="secondary" size="sm">secondary sm</button>
    <button dfButton variant="ghost" size="lg">ghost lg</button>
    <button dfButton variant="danger">danger default size</button>
    <a dfButton variant="primary" href="/x">link</a>
  `,
})
class HostComponent {}

describe('DfButtonDirective', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('applies base class to every host element', () => {
    const hosts = fixture.debugElement.queryAll(By.directive(DfButtonDirective));
    expect(hosts.length).toBe(6);
    hosts.forEach(h => expect(h.nativeElement.classList).toContain('df-btn'));
  });

  it('defaults to primary variant and md size', () => {
    const el = fixture.debugElement.queryAll(By.directive(DfButtonDirective))[0].nativeElement;
    expect(el.classList).toContain('df-btn--primary');
    expect(el.classList).toContain('df-btn--md');
  });

  it('applies variant classes for primary/secondary/ghost/danger', () => {
    const els = fixture.debugElement
      .queryAll(By.directive(DfButtonDirective))
      .map(d => d.nativeElement as HTMLElement);
    expect(els[1].classList).toContain('df-btn--primary');
    expect(els[2].classList).toContain('df-btn--secondary');
    expect(els[3].classList).toContain('df-btn--ghost');
    expect(els[4].classList).toContain('df-btn--danger');
  });

  it('applies size classes sm/md/lg', () => {
    const els = fixture.debugElement
      .queryAll(By.directive(DfButtonDirective))
      .map(d => d.nativeElement as HTMLElement);
    expect(els[1].classList).toContain('df-btn--md');
    expect(els[2].classList).toContain('df-btn--sm');
    expect(els[3].classList).toContain('df-btn--lg');
  });

  it('works on anchor elements too', () => {
    const anchor = fixture.debugElement.queryAll(By.directive(DfButtonDirective))[5].nativeElement;
    expect(anchor.tagName).toBe('A');
    expect(anchor.classList).toContain('df-btn');
    expect(anchor.classList).toContain('df-btn--primary');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/df-button.directive.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL — cannot find module `./df-button.directive`.

- [ ] **Step 3: Implement the directive**

Create `angular-frontend/src/app/shared/ui/button/df-button.directive.ts`:

```typescript
import { Directive, HostBinding, Input } from '@angular/core';

export type DfButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type DfButtonSize = 'sm' | 'md' | 'lg';

@Directive({
  selector: 'button[dfButton], a[dfButton]',
  standalone: true,
})
export class DfButtonDirective {
  @Input() variant: DfButtonVariant = 'primary';
  @Input() size: DfButtonSize = 'md';

  @HostBinding('class.df-btn') readonly baseClass = true;

  @HostBinding('class')
  get hostClasses(): string {
    return `df-btn df-btn--${this.variant} df-btn--${this.size}`;
  }
}
```

- [ ] **Step 4: Write the button SCSS**

Create `angular-frontend/src/app/shared/ui/button/df-button.directive.scss`:

```scss
.df-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-ui);
  font-weight: 600;
  letter-spacing: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 120ms ease, color 120ms ease, border-color 120ms ease,
    box-shadow 120ms ease, transform 120ms ease;

  &:disabled,
  &[aria-disabled='true'] {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:active:not(:disabled) {
    transform: translateY(1px);
  }

  // Sizes
  &--sm { padding: 6px var(--space-3); font-size: var(--type-small-size); line-height: var(--type-small-lh); }
  &--md { padding: 10px var(--space-4); font-size: var(--type-body-size); line-height: var(--type-body-lh); }
  &--lg { padding: 14px var(--space-5); font-size: var(--type-h3-size); line-height: var(--type-h3-lh); }

  // Variants
  &--primary {
    background: var(--color-primary);
    color: #FFFFFF;
    &:hover:not(:disabled) { background: var(--color-primary-hover); }
  }
  &--secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border-color: var(--color-border);
    &:hover:not(:disabled) { background: var(--color-surface-alt); }
  }
  &--ghost {
    background: transparent;
    color: var(--color-primary);
    &:hover:not(:disabled) { background: var(--color-surface-alt); }
  }
  &--danger {
    background: var(--color-danger);
    color: #FFFFFF;
    &:hover:not(:disabled) { filter: brightness(0.92); }
  }
}
```

The SCSS is consumed globally. Add an `@use` of this file to `styles.scss` so it ships once. Append to `angular-frontend/src/styles.scss`:

```scss
@use 'app/shared/ui/button/df-button.directive' as df-button;
```

If `@use` fails because the file isn't a partial, rename it to `_df-button.scss` in the ui/button directory and update the `@use`:

```bash
mv angular-frontend/src/app/shared/ui/button/df-button.directive.scss \
   angular-frontend/src/app/shared/ui/button/_df-button.scss
```

Then `@use 'app/shared/ui/button/df-button' as df-button;` in `styles.scss`.

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/df-button.directive.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 5/5 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/ui/button angular-frontend/src/styles.scss
git commit -m "feat(frontend): add DfButtonDirective with variants (primary/secondary/ghost/danger) and sizes (sm/md/lg)"
```

---

## Task 8: `DfChipComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/ui/chip/df-chip.component.ts`
- Create: `angular-frontend/src/app/shared/ui/chip/df-chip.component.spec.ts`
- Create: `angular-frontend/src/app/shared/ui/chip/_df-chip.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/ui/chip/df-chip.component.spec.ts`:

```typescript
import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfChipComponent } from './df-chip.component';

@Component({
  standalone: true,
  imports: [DfChipComponent],
  template: `
    <df-chip purpose="stage">Day 3</df-chip>
    <df-chip purpose="interest">Hiking</df-chip>
    <df-chip purpose="counter">127/500</df-chip>
  `,
})
class HostComponent {}

describe('DfChipComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('renders three chips with distinct purpose classes', () => {
    const chips = fixture.debugElement.queryAll(By.directive(DfChipComponent))
      .map(d => d.nativeElement as HTMLElement);
    expect(chips.length).toBe(3);
    expect(chips[0].classList).toContain('df-chip');
    expect(chips[0].classList).toContain('df-chip--stage');
    expect(chips[1].classList).toContain('df-chip--interest');
    expect(chips[2].classList).toContain('df-chip--counter');
  });

  it('projects content', () => {
    const chip = fixture.debugElement.query(By.directive(DfChipComponent)).nativeElement as HTMLElement;
    expect(chip.textContent?.trim()).toBe('Day 3');
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/df-chip.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL — cannot find module.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/ui/chip/df-chip.component.ts`:

```typescript
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfChipPurpose = 'stage' | 'interest' | 'counter';

@Component({
  selector: 'df-chip',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ng-content></ng-content>`,
})
export class DfChipComponent {
  @Input() purpose: DfChipPurpose = 'interest';

  @HostBinding('class')
  get hostClasses(): string {
    return `df-chip df-chip--${this.purpose}`;
  }
}
```

- [ ] **Step 4: Write the chip SCSS**

Create `angular-frontend/src/app/shared/ui/chip/_df-chip.scss`:

```scss
.df-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 4px var(--space-3);
  border-radius: var(--radius-pill);
  font-family: var(--font-ui);
  font-size: var(--type-small-size);
  line-height: var(--type-small-lh);
  font-weight: 500;

  &--stage {
    background: color-mix(in srgb, var(--color-primary) 18%, transparent);
    color: var(--color-primary);
  }
  &--interest {
    background: var(--color-surface-alt);
    color: var(--color-text);
  }
  &--counter {
    background: transparent;
    color: var(--color-text-muted);
    border: 1px solid var(--color-border);
    font-variant-numeric: tabular-nums;
  }
}
```

Append to `angular-frontend/src/styles.scss`:

```scss
@use 'app/shared/ui/chip/df-chip' as df-chip;
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/df-chip.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 2/2 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/ui/chip angular-frontend/src/styles.scss
git commit -m "feat(frontend): add DfChipComponent with stage/interest/counter purposes"
```

---

## Task 9: `DfCardComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/ui/card/df-card.component.ts`
- Create: `angular-frontend/src/app/shared/ui/card/df-card.component.spec.ts`
- Create: `angular-frontend/src/app/shared/ui/card/_df-card.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/ui/card/df-card.component.spec.ts`:

```typescript
import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfCardComponent } from './df-card.component';

@Component({
  standalone: true,
  imports: [DfCardComponent],
  template: `
    <df-card>default connection card</df-card>
    <df-card layout="connection">explicit connection</df-card>
    <df-card layout="revelation">revelation card</df-card>
  `,
})
class HostComponent {}

describe('DfCardComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('defaults to connection layout', () => {
    const card = fixture.debugElement.queryAll(By.directive(DfCardComponent))[0].nativeElement as HTMLElement;
    expect(card.classList).toContain('df-card');
    expect(card.classList).toContain('df-card--connection');
  });

  it('applies layout classes', () => {
    const cards = fixture.debugElement.queryAll(By.directive(DfCardComponent))
      .map(d => d.nativeElement as HTMLElement);
    expect(cards[1].classList).toContain('df-card--connection');
    expect(cards[2].classList).toContain('df-card--revelation');
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/df-card.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/ui/card/df-card.component.ts`:

```typescript
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfCardLayout = 'connection' | 'revelation';

@Component({
  selector: 'df-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ng-content></ng-content>`,
})
export class DfCardComponent {
  @Input() layout: DfCardLayout = 'connection';

  @HostBinding('class')
  get hostClasses(): string {
    return `df-card df-card--${this.layout}`;
  }
}
```

- [ ] **Step 4: Write the card SCSS**

Create `angular-frontend/src/app/shared/ui/card/_df-card.scss`:

```scss
.df-card {
  display: block;
  padding: var(--space-5);
  border-radius: var(--radius-xl);

  &--connection {
    background: var(--color-surface);
    box-shadow: var(--elevation-sm);
  }

  &--revelation {
    background: var(--color-surface-alt);
    border-left: 3px solid var(--color-accent);
    border-radius: var(--radius-lg);
    padding: var(--space-4) var(--space-5);
  }
}
```

Append to `angular-frontend/src/styles.scss`:

```scss
@use 'app/shared/ui/card/df-card' as df-card;
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/df-card.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 2/2 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/ui/card angular-frontend/src/styles.scss
git commit -m "feat(frontend): add DfCardComponent with connection (elevated) and revelation (sage border) layouts"
```

---

## Task 10: `DfInputDirective`

**Files:**
- Create: `angular-frontend/src/app/shared/ui/input/df-input.directive.ts`
- Create: `angular-frontend/src/app/shared/ui/input/df-input.directive.spec.ts`
- Create: `angular-frontend/src/app/shared/ui/input/_df-input.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/ui/input/df-input.directive.spec.ts`:

```typescript
import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfInputDirective } from './df-input.directive';

@Component({
  standalone: true,
  imports: [DfInputDirective],
  template: `
    <input dfInput type="text" />
    <textarea dfInput rows="3"></textarea>
  `,
})
class HostComponent {}

describe('DfInputDirective', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('applies df-input class to input and textarea', () => {
    const hosts = fixture.debugElement.queryAll(By.directive(DfInputDirective))
      .map(d => d.nativeElement as HTMLElement);
    expect(hosts.length).toBe(2);
    hosts.forEach(el => expect(el.classList).toContain('df-input'));
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/df-input.directive.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the directive**

Create `angular-frontend/src/app/shared/ui/input/df-input.directive.ts`:

```typescript
import { Directive, HostBinding } from '@angular/core';

@Directive({
  selector: 'input[dfInput], textarea[dfInput]',
  standalone: true,
})
export class DfInputDirective {
  @HostBinding('class.df-input') readonly baseClass = true;
}
```

- [ ] **Step 4: Write the input SCSS**

Create `angular-frontend/src/app/shared/ui/input/_df-input.scss`:

```scss
.df-input {
  width: 100%;
  padding: 10px var(--space-3);
  font-family: var(--font-ui);
  font-size: var(--type-body-size);
  line-height: var(--type-body-lh);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color 120ms ease, box-shadow 120ms ease;

  &::placeholder { color: var(--color-text-muted); }

  &:hover:not(:disabled) { border-color: color-mix(in srgb, var(--color-border) 50%, var(--color-text) 50%); }

  &:focus-visible {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 20%, transparent);
  }

  &:disabled {
    background: var(--color-surface-alt);
    color: var(--color-text-muted);
    cursor: not-allowed;
  }

  &[aria-invalid='true'] {
    border-color: var(--color-danger);
    &:focus-visible { box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-danger) 22%, transparent); }
  }
}

textarea.df-input {
  min-height: 90px;
  resize: vertical;
}
```

Append to `angular-frontend/src/styles.scss`:

```scss
@use 'app/shared/ui/input/df-input' as df-input;
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/df-input.directive.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 1/1 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/ui/input angular-frontend/src/styles.scss
git commit -m "feat(frontend): add DfInputDirective for unified visible-border text fields"
```

---

## Task 11: `DfAvatarComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/ui/avatar/df-avatar.component.ts`
- Create: `angular-frontend/src/app/shared/ui/avatar/df-avatar.component.spec.ts`
- Create: `angular-frontend/src/app/shared/ui/avatar/_df-avatar.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/ui/avatar/df-avatar.component.spec.ts`:

```typescript
import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfAvatarComponent } from './df-avatar.component';

@Component({
  standalone: true,
  imports: [DfAvatarComponent],
  template: `
    <df-avatar name="Alexander Sebhat"></df-avatar>
    <df-avatar name="Maya"></df-avatar>
    <df-avatar name="Maya" size="sm"></df-avatar>
    <df-avatar name="Maya" size="lg"></df-avatar>
    <df-avatar name="Maya" photoUrl="/x.jpg"></df-avatar>
  `,
})
class HostComponent {}

describe('DfAvatarComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  function hosts(): HTMLElement[] {
    return fixture.debugElement.queryAll(By.directive(DfAvatarComponent))
      .map(d => d.nativeElement as HTMLElement);
  }

  it('renders monogram from first letters of each word, max 2, uppercase', () => {
    const els = hosts();
    expect(els[0].textContent?.trim()).toBe('AS');
    expect(els[1].textContent?.trim()).toBe('M');
  });

  it('applies size classes (md default)', () => {
    const els = hosts();
    expect(els[0].classList).toContain('df-avatar--md');
    expect(els[2].classList).toContain('df-avatar--sm');
    expect(els[3].classList).toContain('df-avatar--lg');
  });

  it('renders img when photoUrl provided and no monogram text', () => {
    const el = hosts()[4];
    const img = el.querySelector('img');
    expect(img).toBeTruthy();
    expect(img!.getAttribute('src')).toBe('/x.jpg');
    expect(img!.getAttribute('alt')).toBe('Maya');
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/df-avatar.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/ui/avatar/df-avatar.component.ts`:

```typescript
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfAvatarSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'df-avatar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-container *ngIf="photoUrl; else monogramTpl">
      <img [src]="photoUrl" [alt]="name" />
    </ng-container>
    <ng-template #monogramTpl>
      <span class="df-avatar__monogram">{{ monogram }}</span>
    </ng-template>
  `,
  imports: [],
  standalone: true,
})
export class DfAvatarComponent {
  @Input() name = '';
  @Input() size: DfAvatarSize = 'md';
  @Input() photoUrl?: string;

  @HostBinding('class')
  get hostClasses(): string {
    return `df-avatar df-avatar--${this.size}`;
  }

  get monogram(): string {
    const parts = (this.name || '').trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return '?';
    const letters = parts.slice(0, 2).map(p => p[0]).join('');
    return letters.toUpperCase();
  }
}
```

Note: The template above uses `*ngIf`. Since the component is standalone, import `CommonModule`:

```typescript
import { CommonModule } from '@angular/common';
// and add to the @Component decorator:
// imports: [CommonModule],
```

Final `df-avatar.component.ts`:

```typescript
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfAvatarSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'df-avatar',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-container *ngIf="photoUrl; else monogramTpl">
      <img [src]="photoUrl" [alt]="name" />
    </ng-container>
    <ng-template #monogramTpl>
      <span class="df-avatar__monogram">{{ monogram }}</span>
    </ng-template>
  `,
})
export class DfAvatarComponent {
  @Input() name = '';
  @Input() size: DfAvatarSize = 'md';
  @Input() photoUrl?: string;

  @HostBinding('class')
  get hostClasses(): string {
    return `df-avatar df-avatar--${this.size}`;
  }

  get monogram(): string {
    const parts = (this.name || '').trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return '?';
    return parts.slice(0, 2).map(p => p[0]).join('').toUpperCase();
  }
}
```

- [ ] **Step 4: Write the avatar SCSS**

Create `angular-frontend/src/app/shared/ui/avatar/_df-avatar.scss`:

```scss
.df-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  background: linear-gradient(135deg, var(--color-accent-soft), var(--color-primary));
  color: #FFFFFF;
  font-family: var(--font-ui);
  font-weight: 600;
  overflow: hidden;
  user-select: none;

  &--sm { width: 32px; height: 32px; font-size: var(--type-small-size); }
  &--md { width: 48px; height: 48px; font-size: var(--type-h3-size); }
  &--lg { width: 72px; height: 72px; font-size: var(--type-h2-size); }

  img { width: 100%; height: 100%; object-fit: cover; }

  &__monogram { letter-spacing: 0.02em; }
}
```

Append to `angular-frontend/src/styles.scss`:

```scss
@use 'app/shared/ui/avatar/df-avatar' as df-avatar;
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/df-avatar.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 3/3 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/ui/avatar angular-frontend/src/styles.scss
git commit -m "feat(frontend): add DfAvatarComponent (monogram-first with optional photoUrl)"
```

---

## Task 12: `DfPageShellComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/ui/page-shell/df-page-shell.component.ts`
- Create: `angular-frontend/src/app/shared/ui/page-shell/df-page-shell.component.spec.ts`
- Create: `angular-frontend/src/app/shared/ui/page-shell/_df-page-shell.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/ui/page-shell/df-page-shell.component.spec.ts`:

```typescript
import { Component } from '@angular/core';
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DfPageShellComponent } from './df-page-shell.component';

@Component({
  standalone: true,
  imports: [DfPageShellComponent],
  template: `
    <df-page-shell>default</df-page-shell>
    <df-page-shell variant="reading">reading</df-page-shell>
    <df-page-shell variant="chat">chat</df-page-shell>
    <df-page-shell variant="grid">grid</df-page-shell>
  `,
})
class HostComponent {}

describe('DfPageShellComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('defaults to grid variant', () => {
    const host = fixture.debugElement.queryAll(By.directive(DfPageShellComponent))[0].nativeElement as HTMLElement;
    expect(host.classList).toContain('df-page-shell');
    expect(host.classList).toContain('df-page-shell--grid');
  });

  it('applies variant classes', () => {
    const hosts = fixture.debugElement.queryAll(By.directive(DfPageShellComponent))
      .map(d => d.nativeElement as HTMLElement);
    expect(hosts[1].classList).toContain('df-page-shell--reading');
    expect(hosts[2].classList).toContain('df-page-shell--chat');
    expect(hosts[3].classList).toContain('df-page-shell--grid');
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/df-page-shell.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/ui/page-shell/df-page-shell.component.ts`:

```typescript
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfPageShellVariant = 'chat' | 'reading' | 'grid';

@Component({
  selector: 'df-page-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ng-content></ng-content>`,
})
export class DfPageShellComponent {
  @Input() variant: DfPageShellVariant = 'grid';

  @HostBinding('class')
  get hostClasses(): string {
    return `df-page-shell df-page-shell--${this.variant}`;
  }
}
```

- [ ] **Step 4: Write the page-shell SCSS**

Create `angular-frontend/src/app/shared/ui/page-shell/_df-page-shell.scss`:

```scss
.df-page-shell {
  display: block;
  margin: 0 auto;
  padding: var(--space-4);

  @media (min-width: 768px) { padding: var(--space-6); }
  @media (min-width: 1280px) { padding: var(--space-8); }

  &--reading { max-width: 720px; }
  &--grid    { max-width: 1120px; }

  &--chat {
    max-width: 480px;
    height: 100dvh;
    padding: 0;
    display: flex;
    flex-direction: column;
  }
}
```

Append to `angular-frontend/src/styles.scss`:

```scss
@use 'app/shared/ui/page-shell/df-page-shell' as df-page-shell;
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/df-page-shell.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 2/2 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/ui/page-shell angular-frontend/src/styles.scss
git commit -m "feat(frontend): add DfPageShellComponent with chat/reading/grid variants (100dvh-aware)"
```

---

## Task 13: UI Barrel Export

**Files:**
- Create: `angular-frontend/src/app/shared/ui/index.ts`

- [ ] **Step 1: Write the barrel file**

Create `angular-frontend/src/app/shared/ui/index.ts`:

```typescript
export { DfButtonDirective } from './button/df-button.directive';
export type { DfButtonVariant, DfButtonSize } from './button/df-button.directive';

export { DfChipComponent } from './chip/df-chip.component';
export type { DfChipPurpose } from './chip/df-chip.component';

export { DfCardComponent } from './card/df-card.component';
export type { DfCardLayout } from './card/df-card.component';

export { DfInputDirective } from './input/df-input.directive';

export { DfAvatarComponent } from './avatar/df-avatar.component';
export type { DfAvatarSize } from './avatar/df-avatar.component';

export { DfPageShellComponent } from './page-shell/df-page-shell.component';
export type { DfPageShellVariant } from './page-shell/df-page-shell.component';
```

- [ ] **Step 2: Commit**

```bash
git add angular-frontend/src/app/shared/ui/index.ts
git commit -m "feat(frontend): add UI primitives barrel export"
```

---

## Task 14: `MobileTabBarComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/navigation/mobile-tab-bar.component.ts`
- Create: `angular-frontend/src/app/shared/navigation/mobile-tab-bar.component.spec.ts`
- Create: `angular-frontend/src/app/shared/navigation/_mobile-tab-bar.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/navigation/mobile-tab-bar.component.spec.ts`:

```typescript
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MobileTabBarComponent } from './mobile-tab-bar.component';

describe('MobileTabBarComponent', () => {
  let fixture: ComponentFixture<MobileTabBarComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [MobileTabBarComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(MobileTabBarComponent);
    fixture.detectChanges();
  });

  it('renders exactly 5 tab links', () => {
    const anchors = fixture.nativeElement.querySelectorAll('a.mobile-tab-bar__tab');
    expect(anchors.length).toBe(5);
  });

  it('tabs point to /discover, /connections, /messages, /revelations, /profile in order', () => {
    const anchors: HTMLAnchorElement[] = Array.from(
      fixture.nativeElement.querySelectorAll('a.mobile-tab-bar__tab')
    );
    expect(anchors.map(a => a.getAttribute('href'))).toEqual([
      '/discover', '/connections', '/messages', '/revelations', '/profile',
    ]);
  });

  it('each tab has aria-label for screen readers', () => {
    const anchors: HTMLAnchorElement[] = Array.from(
      fixture.nativeElement.querySelectorAll('a.mobile-tab-bar__tab')
    );
    anchors.forEach(a => expect(a.getAttribute('aria-label')).toBeTruthy());
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/mobile-tab-bar.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/navigation/mobile-tab-bar.component.ts`:

```typescript
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';

interface Tab {
  route: string;
  icon: string;
  label: string;
}

@Component({
  selector: 'app-mobile-tab-bar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <nav class="mobile-tab-bar" aria-label="Primary">
      <a *ngFor="let tab of tabs"
         class="mobile-tab-bar__tab"
         [routerLink]="tab.route"
         routerLinkActive="is-active"
         [attr.aria-label]="tab.label">
        <mat-icon class="mobile-tab-bar__icon">{{ tab.icon }}</mat-icon>
        <span class="mobile-tab-bar__label">{{ tab.label }}</span>
      </a>
    </nav>
  `,
  styleUrls: ['./_mobile-tab-bar.scss'],
})
export class MobileTabBarComponent {
  readonly tabs: Tab[] = [
    { route: '/discover',    icon: 'explore',    label: 'Discover' },
    { route: '/connections', icon: 'group',      label: 'Connections' },
    { route: '/messages',    icon: 'forum',      label: 'Messages' },
    { route: '/revelations', icon: 'auto_stories', label: 'Revelations' },
    { route: '/profile',     icon: 'person',     label: 'Profile' },
  ];
}
```

Note: Angular CLI does not allow SCSS partials via `styleUrls` in all configs. If the build complains, rename the file to `mobile-tab-bar.component.scss` (without the leading underscore) and update `styleUrls`. Repeat the same rename convention for every navigation component in Tasks 15-16 if needed.

- [ ] **Step 4: Write the tab bar SCSS**

Create `angular-frontend/src/app/shared/navigation/mobile-tab-bar.component.scss`:

```scss
:host { display: contents; }

.mobile-tab-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding-bottom: env(safe-area-inset-bottom);

  &__tab {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    padding: 8px 4px;
    color: var(--color-text-muted);
    text-decoration: none;
    font-size: var(--type-caption-size);
    line-height: var(--type-caption-lh);

    &.is-active {
      color: var(--color-primary);
      background: color-mix(in srgb, var(--color-primary) 10%, transparent);
    }
  }

  &__icon {
    width: 22px;
    height: 22px;
    font-size: 22px;
  }

  &__label { font-weight: 500; }
}
```

Update the component to reference the non-partial filename:

```typescript
styleUrls: ['./mobile-tab-bar.component.scss'],
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/mobile-tab-bar.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 3/3 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/navigation
git commit -m "feat(frontend): add MobileTabBarComponent (5 tabs, safe-area-inset aware)"
```

---

## Task 15: `DesktopTopNavComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.ts`
- Create: `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.spec.ts`
- Create: `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.scss`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.spec.ts`:

```typescript
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DesktopTopNavComponent } from './desktop-top-nav.component';

describe('DesktopTopNavComponent', () => {
  let fixture: ComponentFixture<DesktopTopNavComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [DesktopTopNavComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(DesktopTopNavComponent);
    fixture.detectChanges();
  });

  it('renders 4 primary nav links (not Profile)', () => {
    const anchors = fixture.nativeElement.querySelectorAll('a.desktop-top-nav__tab');
    expect(anchors.length).toBe(4);
  });

  it('renders logo link pointing to root', () => {
    const logo = fixture.nativeElement.querySelector('a.desktop-top-nav__logo');
    expect(logo).toBeTruthy();
    expect(logo.getAttribute('href')).toBe('/');
  });

  it('renders notification bell and avatar dropdown trigger', () => {
    const bell = fixture.nativeElement.querySelector('.desktop-top-nav__bell');
    const avatar = fixture.nativeElement.querySelector('.desktop-top-nav__avatar-trigger');
    expect(bell).toBeTruthy();
    expect(avatar).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/desktop-top-nav.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.ts`:

```typescript
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { DfAvatarComponent } from '../ui/avatar/df-avatar.component';

interface Tab { route: string; label: string; }

@Component({
  selector: 'app-desktop-top-nav',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, MatIconModule, MatMenuModule, DfAvatarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="desktop-top-nav" role="banner">
      <a class="desktop-top-nav__logo" routerLink="/" aria-label="Dinner First home">
        <span class="display-serif">Dinner First</span>
      </a>
      <nav class="desktop-top-nav__tabs" aria-label="Primary">
        <a *ngFor="let tab of tabs"
           class="desktop-top-nav__tab"
           [routerLink]="tab.route"
           routerLinkActive="is-active">{{ tab.label }}</a>
      </nav>
      <div class="desktop-top-nav__actions">
        <button class="desktop-top-nav__bell" mat-icon-button aria-label="Notifications">
          <mat-icon>notifications</mat-icon>
        </button>
        <button class="desktop-top-nav__avatar-trigger"
                [matMenuTriggerFor]="avatarMenu"
                aria-label="Account menu">
          <df-avatar name="You" size="sm"></df-avatar>
        </button>
        <mat-menu #avatarMenu="matMenu">
          <a mat-menu-item routerLink="/profile">Profile</a>
          <a mat-menu-item routerLink="/settings">Settings</a>
          <a mat-menu-item routerLink="/auth/logout">Sign out</a>
        </mat-menu>
      </div>
    </header>
  `,
  styleUrls: ['./desktop-top-nav.component.scss'],
})
export class DesktopTopNavComponent {
  readonly tabs: Tab[] = [
    { route: '/discover',    label: 'Discover' },
    { route: '/connections', label: 'Connections' },
    { route: '/messages',    label: 'Messages' },
    { route: '/revelations', label: 'Revelations' },
  ];
}
```

- [ ] **Step 4: Write the top-nav SCSS**

Create `angular-frontend/src/app/shared/navigation/desktop-top-nav.component.scss`:

```scss
:host { display: block; }

.desktop-top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--space-6);
  height: 64px;
  padding: 0 var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);

  &__logo {
    color: var(--color-text);
    font-size: var(--type-h3-size);
    text-decoration: none;
  }

  &__tabs {
    display: flex;
    gap: var(--space-5);
    flex: 1;
  }

  &__tab {
    color: var(--color-text-muted);
    text-decoration: none;
    font-weight: 500;
    padding: var(--space-2) 0;
    border-bottom: 2px solid transparent;

    &.is-active {
      color: var(--color-text);
      border-bottom-color: var(--color-primary);
    }

    &:hover { color: var(--color-text); }
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  &__bell { color: var(--color-text-muted); }

  &__avatar-trigger {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
  }
}
```

- [ ] **Step 5: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/desktop-top-nav.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 3/3 PASS.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/shared/navigation
git commit -m "feat(frontend): add DesktopTopNavComponent (logo + 4 tabs + bell + avatar dropdown)"
```

---

## Task 16: `ResponsiveNavComponent`

**Files:**
- Create: `angular-frontend/src/app/shared/navigation/responsive-nav.component.ts`
- Create: `angular-frontend/src/app/shared/navigation/responsive-nav.component.spec.ts`

- [ ] **Step 1: Write the failing test**

Create `angular-frontend/src/app/shared/navigation/responsive-nav.component.spec.ts`:

```typescript
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of, BehaviorSubject } from 'rxjs';
import { ResponsiveNavComponent } from './responsive-nav.component';

describe('ResponsiveNavComponent', () => {
  let fixture: ComponentFixture<ResponsiveNavComponent>;
  let observer: jasmine.SpyObj<BreakpointObserver>;
  let matches$: BehaviorSubject<{ matches: boolean; breakpoints: {} }>;

  beforeEach(() => {
    matches$ = new BehaviorSubject<{ matches: boolean; breakpoints: {} }>({ matches: false, breakpoints: {} });
    observer = jasmine.createSpyObj('BreakpointObserver', ['observe']);
    observer.observe.and.returnValue(matches$.asObservable());

    TestBed.configureTestingModule({
      imports: [ResponsiveNavComponent],
      providers: [
        provideRouter([]),
        { provide: BreakpointObserver, useValue: observer },
      ],
    });
    fixture = TestBed.createComponent(ResponsiveNavComponent);
    fixture.detectChanges();
  });

  it('renders desktop nav when viewport is >= 768px', () => {
    matches$.next({ matches: true, breakpoints: {} });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-desktop-top-nav')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-mobile-tab-bar')).toBeFalsy();
  });

  it('renders mobile tab bar when viewport is < 768px', () => {
    matches$.next({ matches: false, breakpoints: {} });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('app-mobile-tab-bar')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-desktop-top-nav')).toBeFalsy();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd angular-frontend && npx ng test --include='**/responsive-nav.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: FAIL.

- [ ] **Step 3: Implement the component**

Create `angular-frontend/src/app/shared/navigation/responsive-nav.component.ts`:

```typescript
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { BreakpointObserver } from '@angular/cdk/layout';
import { Observable, map } from 'rxjs';
import { DesktopTopNavComponent } from './desktop-top-nav.component';
import { MobileTabBarComponent } from './mobile-tab-bar.component';

@Component({
  selector: 'app-responsive-nav',
  standalone: true,
  imports: [CommonModule, DesktopTopNavComponent, MobileTabBarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-container *ngIf="isDesktop$ | async; else mobileTpl">
      <app-desktop-top-nav></app-desktop-top-nav>
    </ng-container>
    <ng-template #mobileTpl>
      <app-mobile-tab-bar></app-mobile-tab-bar>
    </ng-template>
  `,
})
export class ResponsiveNavComponent {
  readonly isDesktop$: Observable<boolean>;

  constructor(breakpoints: BreakpointObserver) {
    this.isDesktop$ = breakpoints.observe('(min-width: 768px)').pipe(map(s => s.matches));
  }
}
```

- [ ] **Step 4: Run tests and verify pass**

```bash
cd angular-frontend && npx ng test --include='**/responsive-nav.component.spec.ts' --watch=false --browsers=ChromeHeadless
```

Expected: 2/2 PASS.

- [ ] **Step 5: Commit**

```bash
git add angular-frontend/src/app/shared/navigation/responsive-nav.component.ts angular-frontend/src/app/shared/navigation/responsive-nav.component.spec.ts
git commit -m "feat(frontend): add ResponsiveNavComponent switching at 768px breakpoint"
```

---

## Task 17: Swap `app.component` to Use `ResponsiveNavComponent`

**Files:**
- Modify: `angular-frontend/src/app/app.component.ts`
- Modify: `angular-frontend/src/app/app.component.html`

- [ ] **Step 1: Read the current `app.component.html` to locate the nav usage**

```bash
cat angular-frontend/src/app/app.component.html
```

Note the current `<app-navigation>` (or similar) selector and its placement.

- [ ] **Step 2: Update `app.component.ts` imports**

In `angular-frontend/src/app/app.component.ts`:

- Replace this line:
  ```typescript
  import { NavigationComponent } from './shared/components/navigation/navigation.component';
  ```
  with:
  ```typescript
  import { ResponsiveNavComponent } from './shared/navigation/responsive-nav.component';
  ```

- In the `imports:` array of `@Component`, replace `NavigationComponent` with `ResponsiveNavComponent`.

- [ ] **Step 3: Update `app.component.html`**

Replace any `<app-navigation>` tag with `<app-responsive-nav>`. Keep attributes and structural siblings (router-outlet, toast, offline-status, onboarding-manager) exactly as-is.

- [ ] **Step 4: Rebuild and verify in browser**

Watch frontend logs. Open `http://localhost:4200` at both a narrow (mobile) viewport (<768px via DevTools device mode) and a wide viewport.
Expected:
- Narrow: bottom tab bar with 5 tabs visible, nothing else.
- Wide: top nav with 4 tabs + bell + avatar button.

- [ ] **Step 5: Run all frontend tests as regression check**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

Expected: All previously-passing tests still pass plus the new nav specs.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/app.component.ts angular-frontend/src/app/app.component.html
git commit -m "refactor(frontend): swap monolithic NavigationComponent for ResponsiveNavComponent"
```

---

## Task 18: Delete Legacy Navigation Component

**Files:**
- Delete: `angular-frontend/src/app/shared/components/navigation/navigation.component.ts`
- Delete: `angular-frontend/src/app/shared/components/navigation/navigation-demo.component.ts`

- [ ] **Step 1: Search for remaining imports of the old component**

```bash
grep -rn "shared/components/navigation/navigation" angular-frontend/src || echo "no matches"
```

Expected: Only the two files above themselves. If any other file imports them, delete the import (it was dead code).

- [ ] **Step 2: Delete the files**

```bash
rm angular-frontend/src/app/shared/components/navigation/navigation.component.ts
rm angular-frontend/src/app/shared/components/navigation/navigation-demo.component.ts
rmdir angular-frontend/src/app/shared/components/navigation 2>/dev/null || true
```

- [ ] **Step 3: Rebuild and run all tests**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

Expected: Build succeeds. All tests pass.

- [ ] **Step 4: Commit**

```bash
git add angular-frontend/src
git commit -m "chore(frontend): delete retired NavigationComponent and navigation-demo"
```

---

## Task 19: Delete Legacy SCSS Files and Drop Aliases

**Files:**
- Delete: `angular-frontend/src/app/shared/styles/_emotional-colors.scss`
- Delete: `angular-frontend/src/app/shared/styles/_accessibility-colors.scss`
- Delete: `angular-frontend/src/app/shared/styles/_icon-standards.scss`
- Delete: `angular-frontend/src/app/shared/styles/_swipe-gestures.scss`
- Delete: `angular-frontend/src/app/shared/styles/gesture-animations.scss`
- Modify: `angular-frontend/src/styles/_tokens.scss` (remove legacy alias block)

- [ ] **Step 1: Re-run migration verification — zero legacy tokens should remain in non-token files**

```bash
grep -rn --include='*.scss' --include='*.ts' --include='*.html' \
  -e '--emotional-primary' \
  -e '--emotional-accent' \
  -e '--emotional-danger' \
  -e '--emotional-warning' \
  -e '--df-primary' \
  -e '--df-accent' \
  -e '--df-bg' \
  -e '--df-surface' \
  -e '--df-text' \
  -e '--text-primary' \
  -e '--text-secondary' \
  -e '--surface-primary' \
  -e '--surface-secondary' \
  angular-frontend/src \
  | grep -v '_tokens.scss' || echo "clean"
```

Expected: `clean`. If anything matches, manually fix each file by hand (the sed script may have missed edge cases like multi-line declarations).

- [ ] **Step 2: Remove the legacy alias block from `_tokens.scss`**

Open `angular-frontend/src/styles/_tokens.scss` and delete everything between (and including) the two marker comment lines:

```scss
  // -----------------------------------------------------------------
  // LEGACY ALIASES — REMOVE IN TASK 20.
  // ...
  // -----------------------------------------------------------------
  --emotional-primary: var(--color-primary);
  ...
  --surface-secondary: var(--color-surface-alt);
```

Remove all 16 alias lines and the three comment lines.

- [ ] **Step 3: Delete legacy SCSS files**

```bash
rm angular-frontend/src/app/shared/styles/_emotional-colors.scss
rm angular-frontend/src/app/shared/styles/_accessibility-colors.scss
rm angular-frontend/src/app/shared/styles/_icon-standards.scss
rm angular-frontend/src/app/shared/styles/_swipe-gestures.scss
rm angular-frontend/src/app/shared/styles/gesture-animations.scss
rmdir angular-frontend/src/app/shared/styles 2>/dev/null || true
```

- [ ] **Step 4: Check for remaining `@import` / `@use` references to deleted files**

```bash
grep -rn --include='*.scss' \
  -e 'emotional-colors' \
  -e 'accessibility-colors' \
  -e 'icon-standards' \
  -e 'swipe-gestures' \
  -e 'gesture-animations' \
  angular-frontend/src || echo "clean"
```

Expected: `clean`. If anything still references them, delete those imports.

- [ ] **Step 5: Rebuild and run all tests**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

Expected: Build succeeds with no SCSS errors. All tests pass.

- [ ] **Step 6: Visual regression spot-check**

Load these routes in the browser at mobile and desktop viewports: `/`, `/onboarding`, `/discover`, `/messages`, `/profile`.
Expected: No console errors, no visibly broken layouts (colors should all resolve via `--color-*` tokens now that aliases are gone).

- [ ] **Step 7: Commit**

```bash
git add angular-frontend/src
git commit -m "chore(frontend): remove legacy SCSS files and token aliases"
```

---

## Task 20: CI Emoji Check and Final Verification

**Files:**
- Create: `angular-frontend/scripts/check-no-emoji.sh`
- Modify: `angular-frontend/package.json`

- [ ] **Step 1: Write the emoji check script**

Create `angular-frontend/scripts/check-no-emoji.sh`:

```bash
#!/usr/bin/env bash
# Fails the build if emoji characters appear in non-messaging source files.
# Spec success criterion: "Zero unintentional emoji in code
# (grep yields only angular-frontend/src/app/features/messaging/ matches)."

set -euo pipefail

# Emoji Unicode ranges covered by this pattern (PCRE):
#   U+1F300-U+1FAFF supplementary symbols
#   U+2600-U+27BF  misc symbols + dingbats
#   U+FE0F         variation selector
PATTERN='[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{FE0F}]'

# Search the frontend sources, excluding the messaging feature (reactions are intentional).
MATCHES=$(grep -rnP \
  --include='*.ts' \
  --include='*.html' \
  --include='*.scss' \
  --exclude-dir='messaging' \
  "$PATTERN" \
  angular-frontend/src || true)

if [ -n "$MATCHES" ]; then
  echo "ERROR: Emoji found outside messaging feature:"
  echo "$MATCHES"
  exit 1
fi

echo "OK: no emoji outside messaging feature."
```

Make it executable:

```bash
chmod +x angular-frontend/scripts/check-no-emoji.sh
```

- [ ] **Step 2: Wire into package.json**

Open `angular-frontend/package.json`. In the `"scripts"` object, add:

```json
"lint:no-emoji": "bash scripts/check-no-emoji.sh"
```

- [ ] **Step 3: Run the check and fix any remaining matches**

```bash
bash angular-frontend/scripts/check-no-emoji.sh
```

If the check fails, open each flagged file and:
- For emoji in CSS pseudo-elements (`content: "⭐"`) — delete the pseudo-element or replace with a Material Icon.
- For emoji in TypeScript data arrays — delete the field or replace with an icon name string consumed by `<mat-icon>`.
- For emoji in HTML templates — replace with `<mat-icon>{{iconName}}</mat-icon>`.

Re-run the check until it prints `OK: no emoji outside messaging feature.`

- [ ] **Step 4: Run full test suite one final time**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

Expected: All tests pass, including the 6 new primitive specs (button, chip, card, input, avatar, page-shell) and 3 navigation specs (mobile-tab-bar, desktop-top-nav, responsive-nav) — totaling at least 22 new tests.

- [ ] **Step 5: Full-app smoke test in the browser**

Start fresh (`./start-app.sh reset` if needed). Walk through:
- Landing `/`
- Register `/auth/register`
- Onboarding `/onboarding`
- Discover `/discover`
- A connection's messaging page `/messages/<id>`
- Profile `/profile`

At each page, at mobile and desktop viewports, verify: no console errors, nav chrome renders (mobile tab bar or desktop top nav as appropriate), all text is Inter, no stray emoji outside of the messaging reactions popover (which isn't even open here).

- [ ] **Step 6: Verify SCSS files list is cleaner than before**

```bash
find angular-frontend/src -name '*.scss' -type f | wc -l
```

Record the number. (No strict target — just confirm it went down from before Phase 1.)

- [ ] **Step 7: Commit**

```bash
git add angular-frontend/scripts/check-no-emoji.sh angular-frontend/package.json angular-frontend/src
git commit -m "feat(frontend): add no-emoji CI check and complete Phase 1 foundation"
```

- [ ] **Step 8: Push the branch and open a PR**

```bash
git push -u origin feature/ui-redesign-phase1
gh pr create --base development --title "UI Redesign Phase 1: Foundation" --body "$(cat <<'EOF'
## Summary
- Replaces the two-file legacy color system with a single _tokens.scss (light + dark).
- Introduces Angular Material 18 theme override (warm terracotta primary, sage accent).
- Adds six UI primitives: DfButton, DfCard, DfChip, DfInput, DfAvatar, DfPageShell (all TDD-covered).
- Splits monolithic NavigationComponent into MobileTabBarComponent + DesktopTopNavComponent, wrapped by ResponsiveNavComponent at the 768px breakpoint.
- Adds lint:no-emoji CI check to guard future regressions.

No user-visible page redesigns in this PR — those land in Phase 2.

## Test Plan
- [ ] ng test passes (new primitive and nav specs + existing regression suite)
- [ ] bash angular-frontend/scripts/check-no-emoji.sh prints OK
- [ ] Manual smoke at 375px and 1280px: all major routes render, nav switches correctly at 768px
- [ ] No console errors on Landing, Onboarding, Discover, Messaging, Profile
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** Every requirement in `docs/superpowers/specs/2026-04-18-ui-redesign-design.md` under sections "Architecture → Token layer", "Material theme integration", "Component primitives", "Navigation", "Color Palette", and "Type Scale" is addressed by Tasks 1-20. Page redesigns (Feature-by-Feature section) are explicitly out of scope for Phase 1 and land in Phase 2.
- **Placeholder scan:** No TBD/TODO language. Every code block is complete; every bash command is runnable; every test has real assertions. The one soft point is Task 17 Step 1 which asks the engineer to read the current `app.component.html` — acceptable because the exact selector depends on repo state at execution time, not plan-time.
- **Type consistency:** Variant/size type names match between directives and specs. `DfPageShellVariant` uses `chat | reading | grid` consistently (spec Section: Architecture → Component primitives: "variant=\"chat\""). `DfButtonVariant` uses `primary | secondary | ghost | danger`; `DfButtonSize` uses `sm | md | lg`. `DfChipPurpose` uses `stage | interest | counter` (matches spec Section: Color Palette → stage chip). `DfAvatarSize` uses `sm | md | lg`. `DfCardLayout` uses `connection | revelation` (matches spec Section: Discover focal card and Profile value cards).
- **Material version:** Plan uses Angular Material 18 syntax (`mat.define-palette`, `mat.define-light-theme`, `mat.define-dark-theme`) confirmed against `package.json`. Spec section "Material theme integration" mentions "Angular Material 19" — this is a spec typo; the implementation correctly targets the installed v18.
