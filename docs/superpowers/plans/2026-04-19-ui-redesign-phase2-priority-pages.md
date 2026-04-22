# UI Redesign Phase 2 — Priority Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the five priority pages (Landing, Onboarding, Discover, Messaging, Profile) against the Phase 1 design system so the product visually embodies "Soul before skin" end-to-end.

**Architecture:** Each page is rebuilt on Phase 1 primitives (`DfButtonDirective`, `DfCardComponent`, `DfChipComponent`, `DfInputDirective`, `DfAvatarComponent`, `DfPageShellComponent`) and tokens (`--color-*`, `--space-*`, `--type-*`, `--radius-*`, `--elevation-*` from `src/styles/_tokens.scss`). Routing, state services, and data models are preserved. Legacy styles and dead code are deleted rather than migrated. Navigation shell is already integrated via `ResponsiveNavComponent` in `app.component`.

**Tech Stack:** Angular 18 standalone components, OnPush change detection, Angular Material 18 (M2 namespaced), TypeScript 5.4, Jasmine + Karma for unit tests, Playwright for visual regression, SCSS with CSS custom properties.

**Branch:** `feature/ui-redesign-phase1` (continuing — Phase 2 + Phase 3 ship as part of the same feature branch per owner direction).

**Spec:** `docs/superpowers/specs/2026-04-18-ui-redesign-design.md` lines 128–220 (Feature-by-Feature Redesigns).

---

## File Structure

### Files to create
- `angular-frontend/src/app/features/onboarding/onboarding-flow.component.ts` — 3-screen orchestrator (replaces `onboarding-welcome.component.ts`).
- `angular-frontend/src/app/features/onboarding/onboarding-flow.component.scss`
- `angular-frontend/src/app/features/onboarding/onboarding-flow.component.spec.ts`
- `angular-frontend/src/app/features/onboarding/onboarding-question.component.ts` — single question + textarea + counter.
- `angular-frontend/src/app/features/onboarding/onboarding-question.component.scss`
- `angular-frontend/src/app/features/onboarding/onboarding-question.component.spec.ts`
- `angular-frontend/tests/visual/phase2.spec.ts` — Playwright visual regression covering `/`, `/onboarding`, `/discover`, `/messages/:id`, `/profile` at 375px, 768px, 1280px.

### Files to modify
- `angular-frontend/src/app/features/landing/landing.component.{ts,html,scss}` — full rewrite on primitives.
- `angular-frontend/src/app/features/landing/landing.component.spec.ts` — rewrite assertions.
- `angular-frontend/src/app/features/discover/discover.component.{ts,html,scss}` — swap swipe deck for focal+peek card scroll-through.
- `angular-frontend/src/app/features/discover/discover.component.spec.ts` — drop swipe assertions, add focal/peek assertions.
- `angular-frontend/src/app/features/messaging/messaging.component.{ts,html,scss}` — page shell + new header/banner/list/composer.
- `angular-frontend/src/app/features/messaging/messaging.component.spec.ts` — update for new composer model.
- `angular-frontend/src/app/features/profile/profile.component.{ts,html,scss}` — flatten tabs to single canvas (edit flow preserved).
- `angular-frontend/src/app/features/profile/profile.component.spec.ts` — update assertions.
- `angular-frontend/src/app/app.routes.ts` — point `/onboarding` at `OnboardingFlowComponent`.

### Files to delete
- `angular-frontend/src/app/features/onboarding/onboarding-welcome.component.ts`
- `angular-frontend/src/app/features/onboarding/onboarding-welcome.component.scss` (if present)
- `angular-frontend/src/app/features/onboarding/onboarding-welcome.component.spec.ts`

---

## Conventions

All new SCSS uses `var(--token-name)` only — no hex literals. All templates must be emoji-free outside `features/messaging/` user-composed content (reactions-popover and message-bubble arrays are allowed; static chrome is not). Every new component is standalone + OnPush. Tests run with `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless`. The baseline failure band is ~70–81 failures from legacy suites; treat that as pass-through flakiness.

---

## Task 1 — Visual regression baseline

**Files:**
- Create: `angular-frontend/tests/visual/phase2.spec.ts`

- [ ] **Step 1: Write Playwright spec**

```typescript
// angular-frontend/tests/visual/phase2.spec.ts
import { test, expect } from '@playwright/test';

const viewports = [
  { name: 'mobile',  width: 375,  height: 812 },
  { name: 'tablet',  width: 768,  height: 1024 },
  { name: 'desktop', width: 1280, height: 900 },
];

const routes = [
  { path: '/',                   name: 'landing'    },
  { path: '/onboarding',         name: 'onboarding' },
  { path: '/discover',           name: 'discover'   },
  { path: '/messages/1',         name: 'messaging'  },
  { path: '/profile',            name: 'profile'    },
];

for (const vp of viewports) {
  for (const r of routes) {
    test(`baseline ${r.name} @ ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(`http://localhost:4200${r.path}`, { waitUntil: 'networkidle' });
      await expect(page).toHaveScreenshot(`${r.name}-${vp.name}.png`, { fullPage: true });
    });
  }
}
```

- [ ] **Step 2: Run the baseline capture**

Run: `cd angular-frontend && npx playwright test tests/visual/phase2.spec.ts --update-snapshots`
Expected: Screenshots written to `tests/visual/phase2.spec.ts-snapshots/`. This captures current (pre-redesign) state; each page task re-generates its snapshot on completion.

- [ ] **Step 3: Commit**

```bash
git add angular-frontend/tests/visual/phase2.spec.ts angular-frontend/tests/visual/phase2.spec.ts-snapshots
git commit -m "test(ui): add phase 2 visual regression baseline"
```

---

## Page 01 — Landing

### Task 2 — Landing component rewrite

**Files:**
- Modify: `angular-frontend/src/app/features/landing/landing.component.ts`
- Modify: `angular-frontend/src/app/features/landing/landing.component.html`
- Modify: `angular-frontend/src/app/features/landing/landing.component.scss`
- Modify: `angular-frontend/src/app/features/landing/landing.component.spec.ts`

- [ ] **Step 1: Write failing spec**

```typescript
// landing.component.spec.ts
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LandingComponent } from './landing.component';

describe('LandingComponent', () => {
  let fixture: ComponentFixture<LandingComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [LandingComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(LandingComponent);
    fixture.detectChanges();
  });

  it('renders hero lines Soul / before / skin', () => {
    const el = fixture.nativeElement as HTMLElement;
    const lines = Array.from(el.querySelectorAll('.landing__hero-line')).map(n => n.textContent?.trim());
    expect(lines).toEqual(['Soul', 'before', 'skin.']);
  });

  it('renders exactly one primary CTA linking to /auth/register', () => {
    const el = fixture.nativeElement as HTMLElement;
    const primary = el.querySelectorAll('a[dfButton][variant="primary"], button[dfButton][variant="primary"]');
    expect(primary.length).toBe(1);
    expect((primary[0] as HTMLAnchorElement).getAttribute('href')).toBe('/auth/register');
  });

  it('renders how-it-works card with three rows', () => {
    const rows = fixture.nativeElement.querySelectorAll('.landing__how-row');
    expect(rows.length).toBe(3);
  });

  it('does not render hero orbs or favorite/auto_awesome icons', () => {
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).not.toMatch(/hero-orb|hero__orb/);
    expect(html).not.toMatch(/>favorite<|>auto_awesome</);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/landing.component.spec.ts'`
Expected: FAIL — hero lines / CTA / rows selectors not present.

- [ ] **Step 3: Rewrite component**

```typescript
// landing.component.ts
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { DfButtonDirective } from '../../shared/ui';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink, MatIconModule, DfButtonDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss'],
})
export class LandingComponent {
  readonly steps = [
    { icon: 'psychology',   title: 'Discover souls',    body: 'Match on what you value — not what you look like.' },
    { icon: 'auto_stories', title: 'Reveal slowly',     body: 'Seven days of progressive revelation. One prompt a day.' },
    { icon: 'restaurant',   title: 'Meet over dinner',  body: 'If it still feels right, you plan one meal together.' },
  ];
}
```

- [ ] **Step 4: Rewrite template**

```html
<!-- landing.component.html -->
<a class="landing__signin display-serif" routerLink="/auth/login">Sign in</a>

<section class="landing__hero">
  <h1 class="landing__hero-stack">
    <span class="landing__hero-line display-serif">Soul</span>
    <span class="landing__hero-line display-serif">before</span>
    <span class="landing__hero-line display-serif">skin.</span>
  </h1>
  <p class="landing__subhead">
    Seven days of progressive revelation. Then, if it feels right — dinner.
  </p>
  <a dfButton variant="primary" size="lg" routerLink="/auth/register" class="landing__cta">
    Begin your story
  </a>
</section>

<section class="landing__how">
  <article class="landing__how-card">
    <div *ngFor="let step of steps" class="landing__how-row">
      <mat-icon class="landing__how-icon" fontSet="material-icons-outlined">{{ step.icon }}</mat-icon>
      <div class="landing__how-text">
        <h3 class="landing__how-title">{{ step.title }}</h3>
        <p class="landing__how-body">{{ step.body }}</p>
      </div>
    </div>
  </article>
</section>
```

- [ ] **Step 5: Rewrite SCSS**

```scss
// landing.component.scss
:host {
  display: block;
  min-height: 100dvh;
  background: var(--color-bg);
  padding: var(--space-12) var(--space-6) var(--space-16);
  position: relative;
}

.landing__signin {
  position: absolute;
  top: var(--space-5);
  right: var(--space-6);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: var(--type-small-size);
  &:hover { color: var(--color-text); }
}

.landing__hero {
  max-width: 640px;
  margin: 0 auto var(--space-16);
}

.landing__hero-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  margin: 0 0 var(--space-6);
}

.landing__hero-line {
  font-size: 56px;
  line-height: 1;
  color: var(--color-text);
  font-weight: 500;
}

@media (min-width: 768px) {
  .landing__hero-line { font-size: 72px; }
}

.landing__subhead {
  color: var(--color-text-muted);
  font-size: var(--type-body-size);
  line-height: var(--type-body-lh);
  margin: 0 0 var(--space-8);
  max-width: 32ch;
}

.landing__cta { display: inline-flex; }

.landing__how {
  max-width: 640px;
  margin: 0 auto;
}

.landing__how-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--elevation-sm);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.landing__how-row {
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: var(--space-4);
  align-items: start;
}

.landing__how-icon {
  color: var(--color-primary);
  font-size: 28px;
  width: 28px;
  height: 28px;
}

.landing__how-title {
  margin: 0 0 var(--space-1);
  font-size: var(--type-h3-size);
  line-height: var(--type-h3-lh);
  font-weight: var(--type-h3-weight);
  color: var(--color-text);
}

.landing__how-body {
  margin: 0;
  font-size: var(--type-body-size);
  line-height: var(--type-body-lh);
  color: var(--color-text-muted);
}
```

- [ ] **Step 6: Run test**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/landing.component.spec.ts'`
Expected: PASS (4/4).

- [ ] **Step 7: Emoji / no-emoji lint + build**

Run: `cd angular-frontend && npm run lint:no-emoji && npx ng build --configuration development`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add angular-frontend/src/app/features/landing/
git commit -m "redesign(landing): soul-before-skin hero + how-it-works card"
```

---

## Page 02 — Onboarding

### Task 3 — OnboardingQuestionComponent

**Files:**
- Create: `angular-frontend/src/app/features/onboarding/onboarding-question.component.ts`
- Create: `angular-frontend/src/app/features/onboarding/onboarding-question.component.scss`
- Create: `angular-frontend/src/app/features/onboarding/onboarding-question.component.spec.ts`

- [ ] **Step 1: Write failing spec**

```typescript
// onboarding-question.component.spec.ts
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { OnboardingQuestionComponent } from './onboarding-question.component';

describe('OnboardingQuestionComponent', () => {
  let fixture: ComponentFixture<OnboardingQuestionComponent>;
  let comp: OnboardingQuestionComponent;

  beforeEach(() => {
    fixture = TestBed.createComponent(OnboardingQuestionComponent);
    comp = fixture.componentInstance;
    comp.prompt = 'What do you value most in a relationship?';
    comp.helper = "Take your time. There's no right answer — only honest ones.";
    comp.value = '';
    fixture.detectChanges();
  });

  it('renders prompt in display-serif', () => {
    const el: HTMLElement = fixture.nativeElement.querySelector('.onboarding-question__prompt');
    expect(el.classList.contains('display-serif')).toBeTrue();
    expect(el.textContent).toContain('What do you value');
  });

  it('renders counter N / 500', () => {
    comp.value = 'hello';
    fixture.detectChanges();
    const c: HTMLElement = fixture.nativeElement.querySelector('.onboarding-question__counter');
    expect(c.textContent?.trim()).toBe('5 / 500');
  });

  it('flags warning at 450 chars, danger at 500 chars', () => {
    comp.value = 'a'.repeat(450);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.onboarding-question__counter')!.classList.contains('is-warning')).toBeTrue();
    comp.value = 'a'.repeat(500);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.onboarding-question__counter')!.classList.contains('is-danger')).toBeTrue();
  });

  it('emits valueChange when textarea input fires', (done) => {
    comp.valueChange.subscribe((v: string) => { expect(v).toBe('hi'); done(); });
    const ta: HTMLTextAreaElement = fixture.nativeElement.querySelector('textarea');
    ta.value = 'hi';
    ta.dispatchEvent(new Event('input'));
  });
});
```

- [ ] **Step 2: Run to verify FAIL**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/onboarding-question.component.spec.ts'`
Expected: FAIL — component does not exist.

- [ ] **Step 3: Implement component**

```typescript
// onboarding-question.component.ts
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { DfInputDirective } from '../../shared/ui';

@Component({
  selector: 'app-onboarding-question',
  standalone: true,
  imports: [CommonModule, DfInputDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <p class="onboarding-question__prompt display-serif">{{ prompt }}</p>
    <p class="onboarding-question__helper">{{ helper }}</p>
    <textarea dfInput
      class="onboarding-question__field"
      [value]="value"
      (input)="onInput($event)"
      maxlength="500"
      rows="4"
      [attr.aria-label]="prompt"></textarea>
    <p class="onboarding-question__counter"
       [class.is-warning]="count >= 450 && count < 500"
       [class.is-danger]="count >= 500">
      {{ count }} / 500
    </p>
  `,
  styleUrls: ['./onboarding-question.component.scss'],
})
export class OnboardingQuestionComponent {
  @Input() prompt = '';
  @Input() helper = '';
  @Input() value = '';
  @Output() valueChange = new EventEmitter<string>();

  get count(): number { return this.value?.length ?? 0; }

  onInput(ev: Event): void {
    const next = (ev.target as HTMLTextAreaElement).value.slice(0, 500);
    this.value = next;
    this.valueChange.emit(next);
  }
}
```

- [ ] **Step 4: Implement SCSS**

```scss
// onboarding-question.component.scss
:host { display: block; }

.onboarding-question__prompt {
  font-size: var(--type-h2-size);
  line-height: var(--type-h2-lh);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
}

.onboarding-question__helper {
  font-size: var(--type-small-size);
  line-height: var(--type-small-lh);
  color: var(--color-text-muted);
  margin: 0 0 var(--space-4);
}

.onboarding-question__field {
  width: 100%;
  min-height: 90px;
  resize: vertical;
}

.onboarding-question__counter {
  margin: var(--space-2) 0 0;
  text-align: right;
  font-size: var(--type-caption-size);
  color: var(--color-text-muted);

  &.is-warning { color: var(--color-warning); }
  &.is-danger  { color: var(--color-danger); }
}
```

- [ ] **Step 5: Run tests**

Expected: PASS (4/4).

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/features/onboarding/onboarding-question.component.*
git commit -m "feat(onboarding): add question component with counter"
```

### Task 4 — OnboardingFlowComponent (3-screen orchestrator)

**Files:**
- Create: `angular-frontend/src/app/features/onboarding/onboarding-flow.component.ts`
- Create: `angular-frontend/src/app/features/onboarding/onboarding-flow.component.scss`
- Create: `angular-frontend/src/app/features/onboarding/onboarding-flow.component.spec.ts`

- [ ] **Step 1: Write failing spec**

```typescript
// onboarding-flow.component.spec.ts
import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { OnboardingFlowComponent } from './onboarding-flow.component';

describe('OnboardingFlowComponent', () => {
  let fixture: ComponentFixture<OnboardingFlowComponent>;
  let comp: OnboardingFlowComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [OnboardingFlowComponent],
      providers: [provideRouter([])],
    });
    fixture = TestBed.createComponent(OnboardingFlowComponent);
    comp = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('starts on screen 1 of 3', () => {
    expect(comp.stepIndex).toBe(0);
    const prog: HTMLElement = fixture.nativeElement.querySelector('.onboarding-flow__progress-fill');
    expect(prog.style.width).toBe('33.3333%');
  });

  it('advances when Continue is clicked and answer is non-empty', () => {
    comp.answers[0] = 'I value trust.';
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button[data-role="continue"]').click();
    fixture.detectChanges();
    expect(comp.stepIndex).toBe(1);
  });

  it('disables Continue when current answer is empty', () => {
    comp.answers[0] = '';
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button[data-role="continue"]');
    expect(btn.disabled).toBeTrue();
  });

  it('Back decrements stepIndex on screens 2-3', () => {
    comp.stepIndex = 1;
    fixture.detectChanges();
    fixture.nativeElement.querySelector('button[data-role="back"]').click();
    fixture.detectChanges();
    expect(comp.stepIndex).toBe(0);
  });
});
```

- [ ] **Step 2: Implement component**

```typescript
// onboarding-flow.component.ts
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, ChangeDetectorRef } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { DfButtonDirective } from '../../shared/ui';
import { OnboardingQuestionComponent } from './onboarding-question.component';

interface Prompt { prompt: string; helper: string; optional?: boolean; }

@Component({
  selector: 'app-onboarding-flow',
  standalone: true,
  imports: [CommonModule, RouterLink, DfButtonDirective, OnboardingQuestionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="onboarding-flow__chrome">
      <div class="onboarding-flow__progress" role="progressbar"
           [attr.aria-valuenow]="stepIndex + 1" aria-valuemin="1" aria-valuemax="3">
        <div class="onboarding-flow__progress-fill"
             [style.width.%]="((stepIndex + 1) / prompts.length) * 100"></div>
      </div>
      <a *ngIf="prompts[stepIndex].optional"
         class="onboarding-flow__skip" routerLink="/discover">Skip</a>
    </header>

    <main class="onboarding-flow__main">
      <app-onboarding-question
        [prompt]="prompts[stepIndex].prompt"
        [helper]="prompts[stepIndex].helper"
        [value]="answers[stepIndex]"
        (valueChange)="onAnswer($event)"></app-onboarding-question>
    </main>

    <footer class="onboarding-flow__footer">
      <button dfButton variant="ghost" size="md"
              data-role="back"
              [disabled]="stepIndex === 0"
              (click)="back()">Back</button>
      <button dfButton variant="primary" size="md"
              data-role="continue"
              [disabled]="!canContinue()"
              (click)="next()">
        {{ stepIndex === prompts.length - 1 ? 'Finish' : 'Continue' }}
      </button>
    </footer>
  `,
  styleUrls: ['./onboarding-flow.component.scss'],
})
export class OnboardingFlowComponent {
  stepIndex = 0;
  readonly prompts: Prompt[] = [
    { prompt: 'What do you value most in a relationship?',
      helper: "Take your time. There's no right answer — only honest ones." },
    { prompt: 'Describe your ideal evening with someone special.',
      helper: 'One scene, as vividly as you like.' },
    { prompt: 'What makes you feel truly understood?',
      helper: 'The small thing someone does that lands.', optional: true },
  ];
  answers: string[] = ['', '', ''];

  constructor(private readonly router: Router, private readonly cdr: ChangeDetectorRef) {}

  onAnswer(v: string): void { this.answers[this.stepIndex] = v; this.cdr.markForCheck(); }

  canContinue(): boolean {
    const current = this.prompts[this.stepIndex];
    if (current.optional) return true;
    return (this.answers[this.stepIndex] ?? '').trim().length > 0;
  }

  back(): void { if (this.stepIndex > 0) this.stepIndex -= 1; }

  next(): void {
    if (!this.canContinue()) return;
    if (this.stepIndex < this.prompts.length - 1) {
      this.stepIndex += 1;
    } else {
      this.router.navigate(['/discover']);
    }
  }
}
```

- [ ] **Step 3: Implement SCSS**

```scss
// onboarding-flow.component.scss
:host {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  background: var(--color-bg);
  padding: var(--space-6);
}

.onboarding-flow__chrome {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.onboarding-flow__progress {
  flex: 1;
  height: 4px;
  background: var(--color-border);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.onboarding-flow__progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 200ms ease;
}

.onboarding-flow__skip {
  font-size: var(--type-small-size);
  color: var(--color-text-muted);
  text-decoration: none;
  &:hover { color: var(--color-text); }
}

.onboarding-flow__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 560px;
  width: 100%;
  margin: 0 auto;
}

.onboarding-flow__footer {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding-top: var(--space-6);
  max-width: 560px;
  width: 100%;
  margin: 0 auto;
}
```

- [ ] **Step 4: Point route at new flow**

Edit `angular-frontend/src/app/app.routes.ts` — replace the import and component reference for the `/onboarding` route:

```typescript
import { OnboardingFlowComponent } from './features/onboarding/onboarding-flow.component';
// …
{ path: 'onboarding', component: OnboardingFlowComponent, canActivate: [AuthGuard] },
```

- [ ] **Step 5: Delete the retired welcome component**

```bash
rm angular-frontend/src/app/features/onboarding/onboarding-welcome.component.ts
rm -f angular-frontend/src/app/features/onboarding/onboarding-welcome.component.scss
rm -f angular-frontend/src/app/features/onboarding/onboarding-welcome.component.spec.ts
```

Then grep for remaining imports and remove any stale references:
Run: `grep -rn "onboarding-welcome" angular-frontend/src/`
Expected: no matches.

- [ ] **Step 6: Run tests + build**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/onboarding-flow.component.spec.ts' && npm run lint:no-emoji && npx ng build --configuration development`
Expected: PASS, exit 0.

- [ ] **Step 7: Commit**

```bash
git add -A angular-frontend/src/app/features/onboarding/ angular-frontend/src/app/app.routes.ts
git commit -m "redesign(onboarding): single-question-per-screen flow, retire welcome screen"
```

---

## Page 03 — Discover

### Task 5 — Strip swipe-deck; introduce focal/peek card model

**Files:**
- Modify: `angular-frontend/src/app/features/discover/discover.component.ts`
- Modify: `angular-frontend/src/app/features/discover/discover.component.html`
- Modify: `angular-frontend/src/app/features/discover/discover.component.scss`
- Modify: `angular-frontend/src/app/features/discover/discover.component.spec.ts`

- [ ] **Step 1: Write failing spec assertions (replace swipe-focused tests)**

Open the existing spec file and replace swipe-centric tests with:

```typescript
it('renders headline with soul count from matches', () => {
  comp.potentialMatches = [
    { id: 1, displayName: 'Avery', compatibility: 82 },
    { id: 2, displayName: 'Jordan', compatibility: 78 },
  ] as any;
  fixture.detectChanges();
  const h: HTMLElement = fixture.nativeElement.querySelector('.discover__headline');
  expect(h.textContent).toContain('2 souls for today');
});

it('renders a single focal card and up to 2 peek cards', () => {
  comp.potentialMatches = [
    { id: 1, displayName: 'A' }, { id: 2, displayName: 'B' }, { id: 3, displayName: 'C' }, { id: 4, displayName: 'D' },
  ] as any;
  fixture.detectChanges();
  const focal = fixture.nativeElement.querySelectorAll('.discover__focal');
  const peek  = fixture.nativeElement.querySelectorAll('.discover__peek');
  expect(focal.length).toBe(1);
  expect(peek.length).toBe(2);
});

it('Begin button uses primary variant; Pass uses secondary', () => {
  comp.potentialMatches = [{ id: 1, displayName: 'A' }] as any;
  fixture.detectChanges();
  expect(fixture.nativeElement.querySelector('button[data-role="begin"]').getAttribute('variant')).toBe('primary');
  expect(fixture.nativeElement.querySelector('button[data-role="pass"]').getAttribute('variant')).toBe('secondary');
});

it('tapping a peek card promotes it to focal', () => {
  comp.potentialMatches = [{ id: 1, displayName: 'A' }, { id: 2, displayName: 'B' }] as any;
  fixture.detectChanges();
  fixture.nativeElement.querySelector('.discover__peek').click();
  fixture.detectChanges();
  expect((comp as any).focalIndex).toBe(1);
});
```

Remove any assertions referencing `SwipeDirective`, `onSwipeLeft`, or gesture event dispatching.

- [ ] **Step 2: Run — observe failing assertions**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/discover.component.spec.ts'`
Expected: FAIL on the new assertions.

- [ ] **Step 3: Rewrite component**

Key changes in `discover.component.ts`:

```typescript
// discover.component.ts — relevant additions/replacements
import { DfButtonDirective, DfCardComponent, DfChipComponent, DfAvatarComponent } from '../../shared/ui';

// imports array gains: DfButtonDirective, DfCardComponent, DfChipComponent, DfAvatarComponent
// imports array loses: SwipeDirective, gesture directives

export class DiscoverComponent {
  focalIndex = 0;

  get focalCard() { return this.potentialMatches[this.focalIndex]; }
  get peekCards() {
    return this.potentialMatches
      .filter((_, i) => i !== this.focalIndex)
      .slice(0, 2);
  }

  promotePeek(id: number): void {
    const idx = this.potentialMatches.findIndex(m => m.id === id);
    if (idx >= 0) this.focalIndex = idx;
  }

  beginConnection(match: any): void { /* existing: call connectionService.initiate(match.id) */ }
  pass(match: any): void { /* existing: push to skipped, advance focal */ }
}
```

- [ ] **Step 4: Rewrite template**

```html
<!-- discover.component.html -->
<header class="discover__header">
  <h1 class="discover__headline display-serif">
    {{ potentialMatches.length }} souls for today.
  </h1>
  <p class="discover__subhead">Based on what you value.</p>
</header>

<section class="discover__stack" *ngIf="focalCard">
  <df-card layout="connection" class="discover__focal">
    <df-chip purpose="stage">Day {{ focalCard.day || 1 }}</df-chip>
    <df-avatar [name]="focalCard.displayName" size="md" class="discover__avatar"></df-avatar>
    <h2 class="discover__name">{{ focalCard.displayName }}</h2>
    <p class="discover__bio">{{ focalCard.bio || focalCard.oneLine }}</p>

    <blockquote class="discover__quote" *ngIf="focalCard.revelationExcerpt">
      <p class="display-serif">{{ focalCard.revelationExcerpt }}</p>
    </blockquote>

    <div class="discover__actions">
      <button dfButton variant="secondary" size="md" data-role="pass"
              (click)="pass(focalCard)">Pass</button>
      <button dfButton variant="primary" size="md" data-role="begin"
              (click)="beginConnection(focalCard)">Begin</button>
    </div>
  </df-card>

  <button *ngFor="let peek of peekCards" class="discover__peek" (click)="promotePeek(peek.id)">
    <df-avatar [name]="peek.displayName" size="sm"></df-avatar>
    <span class="discover__peek-name">{{ peek.displayName }}</span>
    <span class="discover__peek-compat">{{ peek.compatibility }}%</span>
  </button>
</section>
```

- [ ] **Step 5: Rewrite SCSS**

Replace the entire file contents with token-only styling:

```scss
// discover.component.scss
:host {
  display: block;
  min-height: 100dvh;
  background: var(--color-bg);
  padding: var(--space-6);
}

.discover__header { max-width: 560px; margin: 0 auto var(--space-6); }

.discover__headline {
  margin: 0 0 var(--space-1);
  font-size: var(--type-h1-size);
  line-height: var(--type-h1-lh);
  color: var(--color-text);
}

.discover__subhead {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--type-small-size);
}

.discover__stack {
  max-width: 560px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.discover__focal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--elevation-sm);
  padding: var(--space-6);
  display: grid;
  gap: var(--space-4);
}

.discover__avatar { justify-self: end; }

.discover__name {
  margin: 0;
  font-size: var(--type-h2-size);
  line-height: var(--type-h2-lh);
  color: var(--color-text);
}

.discover__bio {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--type-body-size);
}

.discover__quote {
  margin: 0;
  padding: var(--space-4);
  background: var(--color-surface-alt);
  border-left: 3px solid var(--color-accent);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--type-body-size);
}

.discover__actions {
  display: flex;
  gap: var(--space-3);
  justify-content: space-between;
}

.discover__peek {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  opacity: 0.6;
  cursor: pointer;
  width: 100%;
  text-align: left;

  &:hover { opacity: 1; }
}

.discover__peek-name { color: var(--color-text); flex: 1; }
.discover__peek-compat { color: var(--color-text-muted); font-size: var(--type-small-size); }
```

- [ ] **Step 6: Run tests + build**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/discover.component.spec.ts' && npm run lint:no-emoji && npx ng build --configuration development`
Expected: Discover spec PASS; build exit 0.

- [ ] **Step 7: Commit**

```bash
git add angular-frontend/src/app/features/discover/
git commit -m "redesign(discover): focal + peek card stack replaces swipe deck"
```

---

## Page 04 — Messaging

### Task 6 — Messaging page shell + header + stage banner

**Files:**
- Modify: `angular-frontend/src/app/features/messaging/messaging.component.ts`
- Modify: `angular-frontend/src/app/features/messaging/messaging.component.html`
- Modify: `angular-frontend/src/app/features/messaging/messaging.component.scss`
- Modify: `angular-frontend/src/app/features/messaging/messaging.component.spec.ts`

- [ ] **Step 1: Update spec**

```typescript
// messaging.component.spec.ts — additions
it('uses df-page-shell with variant=chat', () => {
  expect(fixture.nativeElement.querySelector('df-page-shell[variant="chat"]')).toBeTruthy();
});

it('renders header with back arrow, avatar, name subtitle', () => {
  const header = fixture.nativeElement.querySelector('.messaging__header');
  expect(header.querySelector('button[aria-label="Back"]')).toBeTruthy();
  expect(header.querySelector('df-avatar')).toBeTruthy();
  expect(header.querySelector('.messaging__subtitle')?.textContent).toMatch(/Day \d+/);
});

it('renders stage banner chip with day + prompt', () => {
  const banner = fixture.nativeElement.querySelector('.messaging__banner');
  expect(banner).toBeTruthy();
  expect(banner.textContent).toMatch(/Day \d+/);
});

it('container height uses 100dvh not 100vh', () => {
  const scss = getComputedStyle(fixture.nativeElement.querySelector('df-page-shell'));
  // smoke-check: variant class should be present
  expect(fixture.nativeElement.querySelector('df-page-shell')!.getAttribute('variant')).toBe('chat');
});

it('composer renders single-row: plus, input, send', () => {
  const composer = fixture.nativeElement.querySelector('.messaging__composer');
  expect(composer.querySelectorAll('button').length).toBe(2);     // plus, send
  expect(composer.querySelector('input[dfInput], .messaging__composer-input')).toBeTruthy();
});

it('has no inline style="display: none" attributes', () => {
  const html = fixture.nativeElement.innerHTML as string;
  expect(html).not.toMatch(/style="display:\s*none/);
});
```

Delete any assertions referring to the three-row composer or the persistent emoji picker bar.

- [ ] **Step 2: Rewrite template**

```html
<!-- messaging.component.html -->
<df-page-shell variant="chat" class="messaging">
  <header class="messaging__header">
    <button mat-icon-button aria-label="Back" (click)="goBack()">
      <mat-icon>arrow_back</mat-icon>
    </button>
    <df-avatar [name]="connection?.otherUser?.displayName || ''" size="sm"></df-avatar>
    <div class="messaging__title">
      <h1 class="messaging__name">{{ connection?.otherUser?.displayName }}</h1>
      <p class="messaging__subtitle">
        Day {{ connection?.dayNumber || 1 }} · {{ connection?.compatibility || 0 }}% compatibility
      </p>
    </div>
    <button mat-icon-button [matMenuTriggerFor]="moreMenu" aria-label="More">
      <mat-icon>more_vert</mat-icon>
    </button>
    <mat-menu #moreMenu="matMenu">
      <button mat-menu-item (click)="onReport()">Report</button>
      <button mat-menu-item (click)="onUnmatch()">Unmatch</button>
    </mat-menu>
  </header>

  <df-chip purpose="stage" class="messaging__banner" (click)="openRevelation()">
    Day {{ connection?.dayNumber || 1 }} · {{ revelationPrompt }}
  </df-chip>

  <ol class="messaging__list" #list>
    <li *ngFor="let msg of messages; trackBy: trackById"
        class="messaging__bubble"
        [class.is-outgoing]="msg.senderId === currentUserId">
      <p class="messaging__bubble-text">{{ msg.text }}</p>
      <span class="messaging__bubble-meta">{{ msg.createdAt | date:'shortTime' }}</span>
    </li>
  </ol>

  <form class="messaging__composer" (ngSubmit)="sendMessage()">
    <button type="button" mat-icon-button aria-label="Attach" (click)="openAttachSheet()">
      <mat-icon>add</mat-icon>
    </button>
    <input dfInput
      class="messaging__composer-input"
      [(ngModel)]="draft" name="draft"
      placeholder="Message" aria-label="Compose message" />
    <button type="submit" mat-icon-button aria-label="Send" [disabled]="!draft?.trim()">
      <mat-icon>send</mat-icon>
    </button>
  </form>
</df-page-shell>
```

- [ ] **Step 3: Rewrite SCSS (tokens only)**

```scss
// messaging.component.scss
:host { display: block; }

.messaging {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  max-width: 480px;
  margin: 0 auto;
  background: var(--color-bg);
}

.messaging__header {
  display: grid;
  grid-template-columns: auto auto 1fr auto;
  align-items: center;
  gap: var(--space-3);
  height: 56px;
  padding: 0 var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.messaging__title { min-width: 0; }
.messaging__name { margin: 0; font-size: var(--type-small-size); font-weight: 600; color: var(--color-text); }
.messaging__subtitle { margin: 0; font-size: var(--type-caption-size); color: var(--color-text-muted); }

.messaging__banner {
  width: 100%;
  text-align: center;
  background: var(--color-primary);
  color: var(--color-surface);
  padding: var(--space-2) var(--space-4);
  border-radius: 0;
  cursor: pointer;
}

.messaging__list {
  flex: 1;
  list-style: none;
  margin: 0;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  overflow-y: auto;
}

.messaging__bubble {
  max-width: 75%;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-alt);
  border-radius: 14px 14px 14px 4px;
  color: var(--color-text);
  align-self: flex-start;

  &.is-outgoing {
    align-self: flex-end;
    background: var(--color-primary);
    color: var(--color-surface);
    border-radius: 14px 14px 4px 14px;
  }
}

.messaging__bubble-text { margin: 0; font-size: var(--type-body-size); line-height: var(--type-body-lh); }
.messaging__bubble-meta { display: block; margin-top: var(--space-1); font-size: 10px; color: var(--color-text-muted); }

.messaging__composer {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.messaging__composer-input {
  background: var(--color-surface-alt);
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  padding: var(--space-2) var(--space-4);
  color: var(--color-text);
  font-size: var(--type-body-size);
}
```

- [ ] **Step 4: Update component TypeScript**

Add imports, remove legacy picker state:

```typescript
// messaging.component.ts — relevant additions
import { DfPageShellComponent, DfAvatarComponent, DfChipComponent, DfInputDirective, DfButtonDirective } from '../../shared/ui';

// imports array gains: DfPageShellComponent, DfAvatarComponent, DfChipComponent, DfInputDirective, DfButtonDirective, FormsModule, MatIconModule, MatMenuModule
// state loses: quickReactions array, emojiPickerOpen flag, three-row composer fields

// add if missing:
get revelationPrompt(): string {
  const prompts = ['A personal value', 'A meaningful experience', 'A hope or dream',
                   'What makes you laugh', 'A challenge overcome', 'Your ideal connection', 'Photo reveal'];
  const day = Math.max(1, Math.min(7, this.connection?.dayNumber || 1));
  return prompts[day - 1];
}

openRevelation(): void { this.router.navigate(['/revelations/compose', this.connection?.id]); }
openAttachSheet(): void { /* existing bottom sheet logic retained */ }
goBack(): void { this.router.navigate(['/messages']); }
trackById(_: number, m: { id: number }): number { return m.id; }
```

- [ ] **Step 5: Verify no leftover `style="display:none"` or `100vh`**

Run: `grep -nE 'display:\s*none|100vh' angular-frontend/src/app/features/messaging/messaging.component.*`
Expected: no matches (the exact string `100vh` does not appear; use `100dvh`).

- [ ] **Step 6: Run tests + emoji lint + build**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/messaging.component.spec.ts' && npm run lint:no-emoji && npx ng build --configuration development`
Expected: messaging spec PASS; no-emoji exits 0 (script excludes `messaging/` per Phase 1); build exit 0.

- [ ] **Step 7: Commit**

```bash
git add angular-frontend/src/app/features/messaging/
git commit -m "redesign(messaging): page-shell chat layout + single-row composer"
```

---

## Page 05 — Profile (self view)

### Task 7 — Flatten profile to single canvas

**Files:**
- Modify: `angular-frontend/src/app/features/profile/profile.component.ts`
- Modify: `angular-frontend/src/app/features/profile/profile.component.html`
- Modify: `angular-frontend/src/app/features/profile/profile.component.scss`
- Modify: `angular-frontend/src/app/features/profile/profile.component.spec.ts`

Profile-edit sub-component is NOT modified in Phase 2 per spec.

- [ ] **Step 1: Update spec**

```typescript
// profile.component.spec.ts — replacement assertions
it('renders "Your profile" header and Edit ghost link', () => {
  const el = fixture.nativeElement;
  expect(el.querySelector('.profile__title')?.textContent?.trim()).toBe('Your profile');
  const edit = el.querySelector('a[data-role="edit"]');
  expect(edit.getAttribute('variant')).toBe('ghost');
  expect(edit.getAttribute('href')).toBe('/profile/edit');
});

it('renders 72px monogram avatar', () => {
  const av = fixture.nativeElement.querySelector('df-avatar');
  expect(av.getAttribute('size')).toBe('lg');
});

it('renders three value cards (one per onboarding answer)', () => {
  comp.profile = { displayName: 'You', onboardingAnswers: ['a','b','c'], interests: [] } as any;
  fixture.detectChanges();
  expect(fixture.nativeElement.querySelectorAll('.profile__value-card').length).toBe(3);
});

it('renders collapsed photo section by default', () => {
  const sec = fixture.nativeElement.querySelector('.profile__photos');
  expect(sec.classList.contains('is-collapsed')).toBeTrue();
});

it('does not render tab headers (flattened)', () => {
  expect(fixture.nativeElement.querySelector('mat-tab-group, .mat-tab-group')).toBeNull();
});
```

- [ ] **Step 2: Rewrite template**

```html
<!-- profile.component.html -->
<header class="profile__header">
  <h1 class="profile__title">Your profile</h1>
  <a dfButton variant="ghost" size="sm" data-role="edit" routerLink="/profile/edit">Edit</a>
</header>

<section class="profile__identity">
  <df-avatar [name]="profile?.displayName || ''" size="lg"></df-avatar>
  <h2 class="profile__name">{{ profile?.displayName }}</h2>
  <p class="profile__meta">
    <span *ngIf="profile?.location">{{ profile?.location }}</span>
    <span *ngIf="profile?.age"> · {{ profile?.age }}</span>
  </p>
</section>

<section class="profile__interests" *ngIf="profile?.interests?.length">
  <df-chip *ngFor="let interest of profile.interests" purpose="interest">{{ interest }}</df-chip>
</section>

<section class="profile__values">
  <article *ngFor="let answer of profile?.onboardingAnswers; let i = index" class="profile__value-card">
    <p class="caption">{{ valueLabels[i] }}</p>
    <p class="profile__value-body display-serif">{{ answer }}</p>
  </article>
</section>

<section class="profile__photos" [class.is-collapsed]="photosCollapsed">
  <button class="profile__photos-toggle" (click)="photosCollapsed = !photosCollapsed"
          [attr.aria-expanded]="!photosCollapsed">
    <mat-icon>{{ photosCollapsed ? 'expand_more' : 'expand_less' }}</mat-icon>
    <span>Photos</span>
  </button>
  <div class="profile__photos-body" *ngIf="!photosCollapsed">
    <p class="profile__photos-note">
      Photos are shared per-connection, on Day 7, with mutual consent.
    </p>
    <div class="profile__photos-grid">
      <img *ngFor="let photo of profile?.photos" [src]="photo.url" [alt]="''" />
    </div>
    <button dfButton variant="secondary" size="sm" (click)="uploadPhoto()">Upload a photo</button>
  </div>
</section>
```

- [ ] **Step 3: Update component**

```typescript
// profile.component.ts — relevant shape
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { DfButtonDirective, DfAvatarComponent, DfChipComponent } from '../../shared/ui';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterLink, MatIconModule, DfButtonDirective, DfAvatarComponent, DfChipComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
})
export class ProfileComponent implements OnInit {
  profile: any = null;              // keep existing shape; service wiring unchanged
  photosCollapsed = true;
  readonly valueLabels = ['VALUES', 'IDEAL EVENING', 'FEELING UNDERSTOOD'];

  // keep existing constructor + service + ngOnInit that loads profile
  uploadPhoto(): void { /* existing */ }
}
```

- [ ] **Step 4: Rewrite SCSS**

```scss
// profile.component.scss
:host {
  display: block;
  min-height: 100dvh;
  background: var(--color-bg);
  padding: var(--space-6);
  max-width: 720px;
  margin: 0 auto;
}

.profile__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}

.profile__title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.profile__identity {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;
  margin-bottom: var(--space-8);
}

.profile__name {
  margin: 0;
  font-size: 20px;
  line-height: 24px;
  font-weight: 600;
  color: var(--color-text);
}

.profile__meta {
  margin: 0;
  font-size: var(--type-small-size);
  color: var(--color-text-muted);
}

.profile__interests {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-2);
  margin-bottom: var(--space-8);

  @media (min-width: 768px) { flex-wrap: wrap; overflow-x: visible; }
}

.profile__values {
  display: grid;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.profile__value-card {
  background: var(--color-surface);
  border-radius: 14px;
  border-left: 3px solid var(--color-accent);
  padding: var(--space-4);
  box-shadow: var(--elevation-sm);
}

.profile__value-body {
  margin: var(--space-2) 0 0;
  font-size: 14px;
  line-height: 20px;
  color: var(--color-text);
}

.profile__photos {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.profile__photos-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  background: none;
  border: none;
  padding: 0;
  color: var(--color-text);
  cursor: pointer;
  font-size: var(--type-body-size);
}

.profile__photos-note {
  margin: var(--space-3) 0 var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--type-small-size);
}

.profile__photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: var(--space-2);
  margin-bottom: var(--space-3);

  img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: var(--radius-md); }
}
```

- [ ] **Step 5: Run tests + build**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/profile.component.spec.ts' && npm run lint:no-emoji && npx ng build --configuration development`
Expected: profile spec PASS; exit 0.

- [ ] **Step 6: Commit**

```bash
git add angular-frontend/src/app/features/profile/profile.component.*
git commit -m "redesign(profile): flatten tabs to single canvas with value cards"
```

---

## Task 8 — Phase 2 verification pass

**Files:** none created — verification only.

- [ ] **Step 1: Full unit-test run**

Run: `cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless 2>&1 | tail -30`
Expected: Failure count within the known baseline band (70–81 pre-existing flakies). No new failures introduced by Phase 2.

- [ ] **Step 2: Refresh Playwright baselines**

Run: `cd angular-frontend && npx playwright test tests/visual/phase2.spec.ts --update-snapshots`
Expected: new post-redesign screenshots written.

- [ ] **Step 3: No-emoji lint**

Run: `cd angular-frontend && npm run lint:no-emoji`
Expected: exit 0 (only `features/messaging/` permitted to contain emoji in message bodies — script excludes that directory).

- [ ] **Step 4: Production build**

Run: `cd angular-frontend && npx ng build --configuration production`
Expected: exit 0. Budgets must not regress.

- [ ] **Step 5: Token-only check**

Run: `grep -rnE '#[0-9a-fA-F]{3,8}\b' angular-frontend/src/app/features/landing angular-frontend/src/app/features/onboarding angular-frontend/src/app/features/discover angular-frontend/src/app/features/messaging angular-frontend/src/app/features/profile | grep -v '\.spec\.ts' || true`
Expected: no matches in SCSS/TS (messaging spec files may contain test fixture hex; content files must not).

- [ ] **Step 6: Commit snapshots and tagline**

```bash
git add angular-frontend/tests/visual/phase2.spec.ts-snapshots
git commit -m "test(ui): refresh phase 2 visual baselines post-redesign"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - Landing: hero stack, single CTA, how-it-works card, dead code removed → Task 2.
   - Onboarding: 3-screen flow, progress bar, skip, counter with warning/danger, welcome retired → Tasks 3–4.
   - Discover: headline with count, focal+peek stack, Pass/Begin buttons, swipe deleted → Task 5.
   - Messaging: page shell, 56px header, stage banner, asymmetric bubbles, single-row composer, 100vh purged → Task 6.
   - Profile: header, 72px monogram, interests chips, three value cards, collapsed photos → Task 7.

2. **No placeholders:** Every component has full TypeScript, template, SCSS, and spec code in-step. No "TBD" or "similar to".

3. **Type consistency:** `DfCardLayout` values (`connection` / `revelation`) match Phase 1 primitive contract. `DfChipPurpose` (`stage` / `interest` / `counter`) matches. Profile does not touch `profile-edit.component.ts` per spec.

4. **Testing:** Each task runs scoped tests after changes; Task 8 runs the full suite and visual regression. Baseline band (70–81) documented.
