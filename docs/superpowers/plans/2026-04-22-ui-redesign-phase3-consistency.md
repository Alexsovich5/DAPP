# UI Redesign Phase 3 — Consistency Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Swap legacy color literals and Material primitives for Phase 1 tokens and `df-*` primitives across the 7 non-priority feature areas, fix broken routes, and keep the suite green.

**Architecture:** Pure consistency pass — no new features, no bespoke redesigns. Each task targets one feature area; tasks are independent and can be done in parallel in principle, though we'll do them sequentially for coherent commits.

**Tech Stack:** Angular 18 standalone + OnPush, Phase 1 primitives (`DfButtonDirective`, `DfInputDirective`, `DfCardComponent`, `DfChipComponent`, `DfAvatarComponent`, `DfPageShellComponent`), CSS custom-property tokens in `angular-frontend/src/styles/_tokens.scss`.

**Branch:** Continue on `feature/ui-redesign-phase1` per user directive to bundle all phases into one PR.

---

## File Structure

Phase 3 modifies existing files only — no new components, no new tests except where removing Material imports forces a spec update. The pages touched:

| Feature | Files touched |
|---------|---------------|
| app routing | `angular-frontend/src/app/app.routes.ts` |
| connections | `features/connections/connection-management.component.*`, `features/connections/connection-card.component.*` |
| notifications | `features/notifications/notifications.component.ts` (inline template/styles) |
| settings | `features/settings/settings.component.ts` (inline template/styles) |
| dinner-planning | `features/dinner-planning/dinner-planning.component.{ts,html,scss}`, spec |
| matches (celebration) | Delete — unreachable and replaced by conversations list. If later re-surfaced, rebuild from tokens. |
| messages (conversations list) | `features/messages/messages.component.ts` |
| revelations | `features/revelations/revelations.component.ts`, `features/revelations/revelation-timeline.component.ts` |
| auth | `features/auth/login/login.component.*`, `features/auth/register/register.component.*`, `features/auth/forgot-password/forgot-password.component.*` |
| preferences | `features/preferences/preferences.component.*` |

## Token Mapping Reference

All literal hex in Phase 3 scope must go through this map. If a literal hex doesn't match, pick the closest token rather than introducing a new color.

| Purpose | Token | Hex (light) |
|---------|-------|-------------|
| Page background | `--color-bg` | `#FBF3EC` |
| Card/surface | `--color-surface` | `#FFFFFF` |
| Alt surface (muted bg) | `--color-surface-alt` | `#F5EDE4` |
| Hairline border | `--color-border` | `#E8DDD0` |
| Primary (CTA, terracotta) | `--color-primary` | `#D17B5A` |
| Primary hover | `--color-primary-hover` | `#B8684A` |
| Sage accent | `--color-accent` | `#9BAE8A` |
| Blush accent | `--color-accent-soft` | `#E8B9A0` |
| Body text | `--color-text` | `#2F2420` |
| Muted text | `--color-text-muted` | `#8A6E5F` |
| Danger/error | `--color-danger` | `#C4564B` |
| Warning | `--color-warning` | `#E0A060` |

Common greyscale literals (`#fff`, `#ffffff`, `#000`) → keep as `var(--color-surface)` or `var(--color-text)` when they represent fg/bg respectively; drop when they were decoration.

---

## Task 1 — Fix broken routes

**Files:**
- Modify: `angular-frontend/src/app/app.routes.ts`

- [ ] **Step 1: Audit and fix routes**

Broken/missing routes identified by survey:
- `/dashboard` — navigated from `register.component.ts`, no route. Redirect to `/discover`.
- `/auth/login`, `/auth/register` — landing page uses these paths. Add redirects to `/login` and `/register`.
- `/revelations/compose/:id` — navigated from messaging. Add route (lazy-load revelations component which already handles compose).
- `matches` — unreachable; already redirected to `conversations`. Leave as-is.

Add to `app.routes.ts` before the `**` wildcard:

```typescript
{ path: 'dashboard', redirectTo: 'discover', pathMatch: 'full' },
{ path: 'auth/login', redirectTo: 'login', pathMatch: 'full' },
{ path: 'auth/register', redirectTo: 'register', pathMatch: 'full' },
{
  path: 'revelations/compose/:connectionId',
  loadComponent: () =>
    import('./features/revelations/revelations.component').then(m => m.RevelationsComponent),
  canActivate: [AuthGuard],
},
```

- [ ] **Step 2: Commit**

```bash
git add angular-frontend/src/app/app.routes.ts
git commit -m "fix(routing): add dashboard, auth/*, and revelation compose redirects"
```

---

## Task 2 — Connections consistency

**Files:**
- Modify: `features/connections/connection-management.component.ts` (+template+scss if separated)
- Modify: `features/connections/connection-card.component.ts`

- [ ] **Step 1: Swap 2 mat-*-buttons for `[dfButton]`**

Map:
- Primary actions → `<button dfButton variant="primary">`
- Secondary/outline → `<button dfButton variant="secondary">`
- Text/ghost → `<button dfButton variant="ghost">`

- [ ] **Step 2: Replace 3 literal hex with tokens per map.**

- [ ] **Step 3: Run scoped tests + commit**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless --include='**/connections/**/*.spec.ts'
```
Expected: unchanged pass count, no new failures.

```bash
git add angular-frontend/src/app/features/connections/
git commit -m "consistency(connections): adopt dfButton and color tokens"
```

---

## Task 3 — Notifications consistency

**Files:**
- Modify: `features/notifications/notifications.component.ts` (inline template + styles)

- [ ] **Step 1: Token swap**

Replace all 43 literal hex in the `styles: [...]` block with tokens per map.

- [ ] **Step 2: Add `[dfButton]` on any visible action buttons** if present in the template.

- [ ] **Step 3: Run scoped test + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/notifications.component.spec.ts'
git add angular-frontend/src/app/features/notifications/
git commit -m "consistency(notifications): swap literal colors for tokens"
```

---

## Task 4 — Settings consistency

**Files:**
- Modify: `features/settings/settings.component.ts` (inline template + styles)

- [ ] **Step 1: Token swap**

Replace all 41 literal hex with tokens.

- [ ] **Step 2: Swap any `<button class="...">` to `[dfButton]`** where the class is acting as a button style.

- [ ] **Step 3: Run scoped test + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/settings.component.spec.ts'
git add angular-frontend/src/app/features/settings/
git commit -m "consistency(settings): swap literal colors for tokens"
```

---

## Task 5 — Dinner-planning consistency

**Files:**
- Modify: `features/dinner-planning/dinner-planning.component.{ts,html,scss}`
- Modify: spec if Material imports change

- [ ] **Step 1: Replace 4 `mat-form-field` with `<input dfInput>` pattern**

Example replacement:
```html
<!-- Before -->
<mat-form-field appearance="fill">
  <mat-label>Restaurant</mat-label>
  <input matInput formControlName="restaurant" />
</mat-form-field>

<!-- After -->
<label class="dinner__field">
  <span class="dinner__field-label">Restaurant</span>
  <input dfInput formControlName="restaurant" />
</label>
```

- [ ] **Step 2: Swap 2 `mat-*-button` for `[dfButton]`.**

- [ ] **Step 3: Remove `MatFormFieldModule`, `MatInputModule`, `MatButtonModule` imports if nothing else uses them.** Add `DfButtonDirective`, `DfInputDirective`.

- [ ] **Step 4: Run scoped test + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/dinner-planning.component.spec.ts'
git add angular-frontend/src/app/features/dinner-planning/
git commit -m "consistency(dinner-planning): adopt dfInput/dfButton primitives"
```

---

## Task 6 — Delete unreachable matches celebration

**Files:**
- Delete: `features/matches/matches.component.ts` (and `.html/.scss/.spec.ts` if present)

- [ ] **Step 1: Verify no reachable route or template references**

Current `/matches` route is a redirect to `/conversations`. Navigation calls like `router.navigate(['/matches'])` land on conversations list via redirect. No other consumer renders `MatchesComponent`.

Run:
```bash
grep -rn "MatchesComponent\|matches/matches.component" angular-frontend/src/
```
Expected: only the file's own self-references. If any consumer exists, STOP and fold into this task — but spec survey shows none.

- [ ] **Step 2: Delete component files and any tests**

```bash
rm -rf angular-frontend/src/app/features/matches/
```

- [ ] **Step 3: Commit**

```bash
git add -A angular-frontend/src/app/features/matches/
git commit -m "chore(matches): remove unreachable legacy celebration component"
```

---

## Task 7 — Messages list consistency

**Files:**
- Modify: `features/messages/messages.component.ts` (inline template + styles)

- [ ] **Step 1: Token swap**

Replace all 45 literal hex with tokens.

- [ ] **Step 2: Promote list rows to tokens + proper `df-avatar` if monogram is drawn manually.**

- [ ] **Step 3: Run scoped test + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/messages.component.spec.ts'
git add angular-frontend/src/app/features/messages/
git commit -m "consistency(messages): swap literal colors for tokens"
```

---

## Task 8 — Revelations consistency

**Files:**
- Modify: `features/revelations/revelations.component.ts` (1454 LOC; focus on styles)
- Modify: `features/revelations/revelation-timeline.component.ts` (950 LOC)

This task is the biggest: 121 hex literals, two large files, a `←` glyph.

- [ ] **Step 1: Sweep token swaps in both files**

Use a systematic grep/replace:
```bash
grep -nE '#[0-9a-fA-F]{3,8}\b' angular-frontend/src/app/features/revelations/
```
For each hit, apply the token map. Pay special attention to gradient backgrounds — keep gradients, swap stops for tokens.

- [ ] **Step 2: Replace `←` with `<mat-icon>arrow_back</mat-icon>` or `arrow_back_ios_new`**

Rationale: the ascii arrow is inconsistent with the Material icon set used elsewhere for navigation.

- [ ] **Step 3: Swap any `<button class="...">` intended as buttons for `[dfButton]`.**

- [ ] **Step 4: Run scoped tests + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/revelations/**/*.spec.ts'
git add angular-frontend/src/app/features/revelations/
git commit -m "consistency(revelations): swap literals for tokens and material back arrow"
```

---

## Task 9 — Auth forms (login / register / forgot-password)

**Files:**
- Modify: `features/auth/login/login.component.{ts,html,scss}`
- Modify: `features/auth/register/register.component.{ts,html,scss}`
- Modify: `features/auth/forgot-password/forgot-password.component.{ts,html,scss}`
- Modify: each `.spec.ts` if Material imports change

Biggest primitive-swap job: 33 `mat-form-field` + 21 `mat-*-button` across three forms.

- [ ] **Step 1: For each form, convert each `mat-form-field` block to the `dfInput` pattern**

Before:
```html
<mat-form-field appearance="fill">
  <mat-label>Email</mat-label>
  <input matInput type="email" formControlName="email" />
  <mat-error *ngIf="form.get('email')?.invalid">Valid email required.</mat-error>
</mat-form-field>
```

After:
```html
<label class="auth__field">
  <span class="auth__field-label">Email</span>
  <input dfInput type="email" formControlName="email" />
  <span class="auth__field-error" *ngIf="form.get('email')?.invalid && form.get('email')?.touched">
    Valid email required.
  </span>
</label>
```

- [ ] **Step 2: Swap mat-raised/stroked/flat buttons for `[dfButton]`**

- [ ] **Step 3: Replace 6 literal hex with tokens across the three SCSS files**

- [ ] **Step 4: Remove Material form/button imports**

Remove `MatFormFieldModule`, `MatInputModule`, `MatButtonModule` from each `@Component` imports array. Keep `MatIconModule` if icons are used.

- [ ] **Step 5: Update specs — replace mat-form-field DOM assertions with `input[dfInput]` assertions**

- [ ] **Step 6: Run scoped tests + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/auth/**/*.spec.ts'
git add angular-frontend/src/app/features/auth/
git commit -m "consistency(auth): swap Material forms for dfInput/dfButton primitives"
```

---

## Task 10 — Preferences consistency

**Files:**
- Modify: `features/preferences/preferences.component.{ts,html,scss}`

- [ ] **Step 1: Replace 23 `mat-form-field` with `dfInput` pattern** per Task 9's example.

- [ ] **Step 2: Swap 2 buttons for `[dfButton]`.**

- [ ] **Step 3: Replace 4 hex with tokens.**

- [ ] **Step 4: Remove Material form/button imports, update spec.**

- [ ] **Step 5: Run scoped test + commit**

```bash
npx ng test --watch=false --browsers=ChromeHeadless --include='**/preferences.component.spec.ts'
git add angular-frontend/src/app/features/preferences/
git commit -m "consistency(preferences): swap Material forms for dfInput/dfButton"
```

---

## Task 11 — Final verification pass

**Files:** none created — verification only.

- [ ] **Step 1: Full unit-test run**

```bash
cd angular-frontend && npx ng test --watch=false --browsers=ChromeHeadless
```
Expected: failure count ≤ 81 (baseline band). No new failures attributable to Phase 3. If a Phase 3 commit broke a test, fix the test inline in the offending task's commit.

- [ ] **Step 2: No-emoji lint**

```bash
bash angular-frontend/scripts/check-no-emoji.sh
```
Expected: exit 0.

- [ ] **Step 3: Token-only check across all features touched**

```bash
grep -rnE '#[0-9a-fA-F]{3,8}\b' \
  angular-frontend/src/app/features/connections \
  angular-frontend/src/app/features/notifications \
  angular-frontend/src/app/features/settings \
  angular-frontend/src/app/features/dinner-planning \
  angular-frontend/src/app/features/messages \
  angular-frontend/src/app/features/revelations \
  angular-frontend/src/app/features/auth \
  angular-frontend/src/app/features/preferences \
  --include='*.scss' --include='*.ts' | grep -v '\.spec\.ts' || echo "clean"
```
Expected: "clean" (no matches in non-spec files).

- [ ] **Step 4: Development build**

```bash
npx ng build --configuration=development
```
Expected: exit 0.

- [ ] **Step 5: Production build budget check**

```bash
npx ng build --configuration=production 2>&1 | grep -E "initial total|Initial total"
```
Expected: initial bundle ≤ Phase 2 baseline (1.06 MB). Does not need to pass the configured 1.05 MB budget — that's pre-existing tech debt. Phase 3 must not grow it.

---

## Self-Review Checklist

1. **Spec coverage**
   - Token swap in all 7 Phase 3 areas → Tasks 2–10.
   - Primitive swap in areas that had Material buttons/forms → Tasks 2, 5, 9, 10.
   - Emoji removal → no emoji present (survey confirmed); `←` glyph handled in Task 8.
   - Broken routes fixed → Task 1 (not in spec scope but blocks user paths; include as safety net).

2. **No placeholders** — every task has explicit file paths, concrete before/after snippets for non-obvious swaps, and commit message text.

3. **Type consistency** — all `df-*` primitives match Phase 1 contract: `DfButtonDirective` variants `primary | secondary | ghost | danger`; `DfInputDirective` attribute-only; `DfChipComponent` purposes `stage | interest | counter`.

4. **Testing** — each task runs scoped tests after changes; Task 11 runs the full suite. Baseline band (≤81 failures) documented.

5. **Rollout** — tasks commit independently; the whole Phase 3 bundle lands on `feature/ui-redesign-phase1` alongside Phase 1+2 per user directive. PR only after Phase 3 verification passes.
