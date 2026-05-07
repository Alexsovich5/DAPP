# Frontend P1 Migration Plan — Adopt `df-page-shell` + `df-button` + `df-input`

**Status:** Draft (open for review on `feature/frontend-layout-assessment`)
**Source:** P1 of `docs/frontend-layout-assessment.md`
**Target:** Bring the 11 unmigrated feature pages onto the design-system primitives.

---

## What this plan turns into

A sequence of **11 small, mechanical PRs** — one per page — each landing on `main` independently and getting auto-deployed by `./scripts/deploy-demo.sh`. The whole sequence should take 1-2 sprints depending on review cadence.

The benefit of one-page-per-PR is that any visual regression is bisectable to a single page, and reviewers can mentally swap into one feature at a time instead of holding all 11 at once.

---

## Migration recipe (applies to every PR)

For each page, these mechanical edits:

### Step 1 — Wrap the template in `df-page-shell`

Before:
```html
<div class="some-page-container">
  <header class="page-header">…</header>
  <section class="page-content">…</section>
</div>
```

After:
```html
<df-page-shell title="Page Title" [showBack]="true">
  <ng-container slot="actions">…</ng-container>
  …
</df-page-shell>
```

(Confirm exact slot names from `shared/ui/page-shell/df-page-shell.component.ts`.)

Delete the page's outer container styles — the shell owns max-width, padding, and background now.

### Step 2 — Replace `<mat-button>` with the `df-button` directive

Before:
```html
<button mat-raised-button color="primary" (click)="submit()">Continue</button>
```

After:
```html
<button df-button variant="primary" (click)="submit()">Continue</button>
```

(Confirm directive selector and inputs from `shared/ui/button/df-button.directive.ts`.)

### Step 3 — Replace `<mat-form-field>` + `matInput` with `df-input`

Before:
```html
<mat-form-field>
  <mat-label>Email</mat-label>
  <input matInput type="email" formControlName="email">
  <mat-error *ngIf="email.errors?.required">Required</mat-error>
</mat-form-field>
```

After:
```html
<df-input
  label="Email"
  type="email"
  formControlName="email"
  [error]="email.errors?.required ? 'Required' : null">
</df-input>
```

(Confirm `df-input` API from `shared/ui/input/df-input.directive.ts`.)

### Step 4 — Drop now-unused imports

Open the component's TypeScript and remove `MatButtonModule` / `MatFormFieldModule` / `MatInputModule` from the `imports:` array. Add the `Df*` directives or components.

### Step 5 — Verify

- `npx ng build --configuration=demo` succeeds
- The page still mounts at its existing route
- Visual inspection in a browser (until we add screenshot diffing)

### Step 6 — Open PR

PR title: `feat(frontend): migrate <page> to df-* primitives`
PR body should include before/after screenshots once the dynamic-audit follow-up adds them.

---

## Sequence (11 PRs)

The order is deliberate: smallest risk and highest visibility first, so we catch primitive-level bugs early and fix them once.

| # | Page | Why this position | Files touched (estimate) | Risk |
|---|------|-------------------|--------------------------|------|
| 1 | `auth/login` | Smallest auth page. First touch — we'll learn what's missing in `df-input`. | `login.component.{ts,html,scss}` | Low |
| 2 | `auth/forgot-password` | Same shape as login but simpler. Confirms the recipe. | `forgot-password.component.{ts,html,scss}` | Low |
| 3 | `auth/register` | Larger form (the `register.component.html` is 364 LOC) — first real test of `df-input` across many fields. | `register.component.{ts,html,scss}` | Medium |
| 4 | `landing` | Highest-traffic public page. Migrate after auth so we can chain the journey login → register → discover with consistent shell. | `landing.component.{ts,html,scss}` | Medium |
| 5 | `discover` | Core authenticated flow. Has its own card layout — may need `df-card` confirmation. | `discover.component.{ts,html,scss}` | Medium |
| 6 | `profile` (overview) | First of the profile cluster. | `profile.component.{ts,html,scss}` | Medium |
| 7 | `profile/profile-view` | Same area; do as a follow-on. | `profile-view.component.{ts,html,scss}` | Low |
| 8 | `profile/profile-edit` | The form-heavy profile page. Stress-test `df-input`. | `profile-edit.component.{ts,html,scss}` | Medium |
| 9 | `chat` | Custom layout (message list); `df-page-shell` may not be a clean fit. May need a shell variant. | `chat.component.{ts,html,scss}` | High |
| 10 | `messaging` | Same caveat — and may be a duplicate of `messages` (see issue below). | `messaging.component.{ts,html,scss}` | High (blocked) |
| 11 | `preferences` | Settings-style. | `preferences.component.{ts,html,scss}` | Low |

**Blocking issue for #10:** the duplication between `features/messages/` and `features/messaging/` (assessment §5) needs resolving first. Don't migrate either until the team picks one as canonical.

---

## What each PR's diff looks like (rough)

A typical page migration is **~80-150 lines net deletion** (mat-form-field is verbose), or **~30-80 lines net change** if the page has a lot of bespoke HTML structure. Total LOC delta across all 11: probably 600-1200 lines deleted, 200-400 lines added.

If a single PR's diff is over 300 lines, that's a signal the page has more than just primitive substitution — split it into "step 1: wrap in shell" PR and "step 2: swap inputs/buttons" PR.

---

## Pre-flight checks before sprint starts

Each of these should return a clean answer before kickoff. They're 5-min checks, not blockers — but better to do them once than per-PR.

1. **`df-page-shell` API is stable.** Open `shared/ui/page-shell/df-page-shell.component.ts` and document its inputs (title, showBack, slots) at the top of this plan. If it's still in flux, freeze it first.

2. **`df-button` and `df-input` work outside `onboarding`.** Pages 1-2 (auth/login, forgot-password) will hit any latent assumption that primitives only run inside the onboarding shell. Treat PR #1 (`auth/login`) as a discovery exercise — if anything weird happens, fix the primitive, not the page.

3. **No global styles depend on Material's default DOM.** Search `src/styles/_material-theme.scss` for anything that targets `.mat-form-field-*` or `.mdc-button-*` selectors. If those exist, removing `mat-form-field` will cascade — surface that risk before swapping.

4. **Storybook or visual reference.** If there's no Storybook, set up a temporary route like `/dev/df-showcase` (modeled on `phase3-showcase`) so reviewers can compare primitive vs. mat versions side-by-side. Without this, every PR review requires running the page locally.

---

## Out of scope for this migration sprint

These are referenced by the assessment but should NOT be bundled into the P1 migration:

- **Breakpoint canonicalization (P2).** Keep existing `@media` rules in each page. Don't invent new breakpoints during a primitive swap — that's a separate concern.
- **Splitting >1000-LOC components (P3).** Don't break revelations.component.ts apart while migrating its template — that's a different PR.
- **`messages` ↔ `messaging` deduplication (P4).** Decide separately, before #10.
- **`phase3-showcase` removal (P5).** Independent.
- **Visual polish / spacing tweaks.** If a primitive's defaults look wrong on a migrated page, file a primitive bug — don't paper over it in the page CSS.

The discipline matters: a 250-line PR is reviewable in 15 minutes. A 600-line PR that mixes concerns will sit in the queue for days.

---

## Verification gates per PR

Before merging each migration PR:

1. `npx ng build --configuration=demo` — must succeed
2. The page renders without runtime console errors at viewports 360px / 768px / 1280px
3. Forms still submit — `(submit)` and `(click)` handlers preserved
4. Tab order is preserved (a11y)
5. Reviewer compares to `main` deployed at `https://date.batcomputer.waynetower.de` for the equivalent page

After merge: `./scripts/deploy-demo.sh` will roll the change into the live demo within ~60 seconds.

---

## What "done" looks like

After all 11 PRs land:

- `grep -rl df-page-shell angular-frontend/src/app/features/` → 13 of 17 (all primary pages; admin/examples/dashboard out of scope unless promoted to P1)
- `grep -rl "mat-button\|mat-form-field" angular-frontend/src/app/features/` → 0 (or only inside the dropped pages)
- Visual consistency between login → register → discover → profile, all using the same shell, padding, max-width, and background

That's the visible outcome. The invisible outcome is that future layout fixes touch one file (the primitive) instead of 11.

---

## Open questions before starting

These need stakeholder input. Auto-listed from §8 of the assessment, narrowed to what blocks P1:

1. **Slot naming convention in `df-page-shell`.** Does it use `<ng-content>` projection, named slots via `select=`, or input properties for header content? PR #1 will set the pattern for the rest.
2. **Should `auth/login` keep its current centered-card layout** (different from app-shell pages) or move to the standard shell with auth as a content variation?
3. **Mobile-first vs desktop-first** for new component CSS. Pick one and document it in `_tokens.scss` as a comment.
