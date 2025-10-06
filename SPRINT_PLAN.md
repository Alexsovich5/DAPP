# Sprint Plan - Dinner First App

**Sprint Period**: Current Sprint
**Created**: 2025-10-06
**Status**: Active
**Focus**: CI/CD Pipeline Stabilization & Code Quality

---

## Sprint Overview

### Sprint Goal
**Stabilize the CI/CD pipeline and improve code quality to enable confident deployments**

Primary objectives:
1. ✅ Fix critical CI/CD blocking issues (COMPLETED)
2. 🔄 Address remaining test failures (IN PROGRESS)
3. 📋 Establish foundation for incremental linting fixes (PLANNED)

---

## Current Project State

### Recent Accomplishments ✅

#### Phase 1-3: CI/CD Fixes (COMPLETED)
- ✅ Fixed 4 Python syntax errors (unterminated f-strings)
- ✅ Fixed database migration CASCADE dependency issue
- ✅ Fixed missing module imports (`app.models.soul_connection`)
- ✅ Fixed test database port configuration (5433 → 5432)
- ✅ Fixed safety command syntax (deprecated `--output` flag)
- ✅ Updated CodeQL Action (v2 → v3)
- ✅ Created missing frontend stub files (websocket.service, components)
- ✅ Fixed frontend test syntax errors

#### Phase 4: Linting Foundation (IN PROGRESS - 2.5% complete)
- ✅ Created comprehensive linting fix plan (18-24 hour roadmap)
- ✅ Established shared type definitions (`soul-types.ts`)
- ✅ Fixed 8 linting errors in `soul-connection.component.ts`
- ✅ Reduced total errors: 325 → 317

### Current CI/CD Status ❌

**Pipeline**: Still failing (3 main jobs failing)

#### Job 1: Frontend Tests & Coverage ❌
- **Status**: Failing on linting step
- **Error**: 317 ESLint errors
- **Impact**: Blocks frontend test execution
- **Priority**: Medium (non-blocking for backend work)

#### Job 2: Backend Tests & Coverage ❌
- **Status**: Failing on test execution
- **Error**: Test imports/setup issues
- **Impact**: Blocks backend test verification
- **Priority**: HIGH (critical for backend changes)

#### Job 3: Security & Vulnerability Tests ❌
- **Status**: Failing on security headers tests
- **Error**: Database connection refused (no postgres service in security job)
- **Impact**: Blocks security verification
- **Priority**: HIGH (security-critical)

---

## Sprint Backlog

### Epic 1: Fix Backend Test Failures 🔴 HIGH PRIORITY

**Goal**: Get backend tests passing in CI/CD

#### Story 1.1: Fix Security Test Database Connection
**Status**: 🔴 TODO
**Estimate**: 1 hour
**Priority**: P0 (Critical)

**Problem**: Security headers tests try to connect to postgres but the job doesn't have a postgres service container.

**Solution Options**:
1. Add postgres service to security test job (like backend job has)
2. Mock database for security tests (they don't need real DB)
3. Move security headers tests to backend test job

**Tasks**:
- [ ] Review test_security_headers.py dependencies
- [ ] Decide on approach (mock vs service container)
- [ ] Update `.github/workflows/test-coverage.yml`
- [ ] Verify tests pass locally
- [ ] Commit and verify in CI/CD

**Acceptance Criteria**:
- Security headers tests run without database errors
- Tests pass in CI/CD pipeline

---

#### Story 1.2: Fix Backend Test Import/Setup Issues
**Status**: 🔴 TODO
**Estimate**: 2 hours
**Priority**: P0 (Critical)

**Problem**: Backend tests failing with import or setup errors (need to examine logs further)

**Tasks**:
- [ ] Get detailed failure logs from backend test job
- [ ] Identify specific test failures
- [ ] Fix import issues
- [ ] Fix test setup/teardown issues
- [ ] Verify migrations run correctly
- [ ] Run full test suite locally
- [ ] Commit and verify in CI/CD

**Acceptance Criteria**:
- All backend tests pass locally
- All backend tests pass in CI/CD
- Test coverage reports generated

---

### Epic 2: Frontend Linting Incremental Fixes 🟡 MEDIUM PRIORITY

**Goal**: Systematically reduce linting errors to zero over multiple sessions

**Total Errors**: 317 (down from 325)
**Completion**: 2.5%
**Estimated Effort**: 18-24 hours across 2-3 weeks

*Full detailed plan in `Linting fix plan.md`*

#### Story 2.1: Quick Wins - Unused Variables (Session 1)
**Status**: 📋 PLANNED
**Estimate**: 2-3 hours
**Priority**: P2

**Errors to Fix**: 54 unused variable/import errors

**Tasks**:
- [ ] Remove unused imports (auto-fixable) - 30 errors
- [ ] Prefix unused parameters with _ - 20 errors
- [ ] Clean up unused variables - 5 errors
- [ ] Run tests to verify no regressions
- [ ] Commit progress

**Acceptance Criteria**:
- Errors reduced from 317 to ~263 (54 fixed)
- All tests still passing
- No functionality broken

---

#### Story 2.2: Case Declarations + Style Violations (Session 2)
**Status**: 📋 PLANNED
**Estimate**: 1-1.5 hours
**Priority**: P2

**Errors to Fix**: 20 errors (9 case declarations + 11 style violations)

**Tasks**:
- [ ] Fix 9 switch statement case declarations
- [ ] Fix 4 empty lifecycle methods
- [ ] Fix 2 directive selectors
- [ ] Fix 3 input/output naming issues
- [ ] Fix 3 Object type errors
- [ ] Fix 1 lifecycle interface
- [ ] Run tests to verify
- [ ] Commit progress

**Acceptance Criteria**:
- Errors reduced from ~263 to ~243 (20 fixed)
- All tests still passing

---

#### Story 2.3: Template Accessibility (Session 3)
**Status**: 📋 PLANNED
**Estimate**: 3-4 hours
**Priority**: P2

**Errors to Fix**: 40 template accessibility errors

**Tasks**:
- [ ] Audit all click handlers in templates
- [ ] Add keyboard event handlers (enter/space)
- [ ] Add tabindex for focusability
- [ ] Use semantic HTML where appropriate
- [ ] Test keyboard navigation manually
- [ ] Commit progress

**Acceptance Criteria**:
- Errors reduced from ~243 to ~203 (40 fixed)
- Keyboard navigation works
- All interactive elements accessible

---

#### Story 2.4: Shared Components `any` Types (Sessions 4-6)
**Status**: 📋 PLANNED
**Estimate**: 6-8 hours
**Priority**: P2

**Errors to Fix**: ~100 `any` type errors in shared components

**Tasks**:
- [ ] Create additional type definitions (component-types.ts, service-types.ts)
- [ ] Fix soul-orb.component.ts (~15 errors)
- [ ] Fix typing-indicator components (~10 errors)
- [ ] Fix navigation components (~15 errors)
- [ ] Fix other shared components (~60 errors)
- [ ] Update tests as needed
- [ ] Commit progress incrementally

**Acceptance Criteria**:
- Errors reduced from ~203 to ~103 (100 fixed)
- Type safety improved
- No regressions

---

#### Story 2.5: Services & Directives `any` Types (Sessions 7-8)
**Status**: 📋 PLANNED
**Estimate**: 4-6 hours
**Priority**: P2

**Errors to Fix**: ~70 `any` type errors in services/directives

**Tasks**:
- [ ] Fix ui-personalization.service.ts (~21 errors)
- [ ] Fix analytics.directive.ts (~4 errors)
- [ ] Fix ab-test.directive.ts (~4 errors)
- [ ] Fix gestures.directive.ts (~2 errors)
- [ ] Fix loading-state.directive.ts (~3 errors)
- [ ] Fix other services/directives (~36 errors)
- [ ] Commit progress

**Acceptance Criteria**:
- Errors reduced from ~103 to ~33 (70 fixed)
- Services properly typed

---

#### Story 2.6: Spec Files & Final Cleanup (Session 9)
**Status**: 📋 PLANNED
**Estimate**: 2-3 hours
**Priority**: P2

**Errors to Fix**: ~33 remaining errors

**Tasks**:
- [ ] Fix spec file type errors (~20 errors)
- [ ] Fix remaining miscellaneous errors (~13 errors)
- [ ] Final linting check
- [ ] Full test suite run
- [ ] Production build verification
- [ ] Commit final fixes

**Acceptance Criteria**:
- ✅ `npx nx lint --maxWarnings 0` passes
- ✅ All tests pass
- ✅ Production build succeeds
- ✅ CI/CD pipeline passes

---

### Epic 3: Backend Code Quality 🟢 LOW PRIORITY

**Goal**: Improve backend code quality and test coverage

#### Story 3.1: Increase Backend Test Coverage
**Status**: 📋 BACKLOG
**Estimate**: TBD
**Priority**: P3

**Current Coverage**: Unknown (need to check once tests pass)

**Tasks**:
- [ ] Measure current coverage
- [ ] Identify uncovered critical paths
- [ ] Write tests for uncovered code
- [ ] Aim for 80%+ coverage

---

#### Story 3.2: Backend Type Hints Enhancement
**Status**: 📋 BACKLOG
**Estimate**: TBD
**Priority**: P3

**Tasks**:
- [ ] Run mypy static type checker
- [ ] Add type hints to untyped functions
- [ ] Fix type inconsistencies

---

### Epic 4: Documentation & Developer Experience 🟢 LOW PRIORITY

#### Story 4.1: Update Development Setup Guide
**Status**: 📋 BACKLOG
**Estimate**: 2 hours
**Priority**: P3

**Tasks**:
- [ ] Document local development setup
- [ ] Document testing procedures
- [ ] Document CI/CD pipeline
- [ ] Update README.md

---

#### Story 4.2: Add Code Review Checklist
**Status**: 📋 BACKLOG
**Estimate**: 1 hour
**Priority**: P3

**Tasks**:
- [ ] Create PR template
- [ ] Define code review checklist
- [ ] Document branching strategy

---

## Sprint Timeline

### Week 1: Critical Fixes
**Days 1-2: Backend Test Fixes** (HIGH PRIORITY)
- Fix security test database connection
- Fix backend test import/setup issues
- **Goal**: Green backend tests in CI/CD

**Days 3-5: Frontend Quick Wins** (MEDIUM PRIORITY)
- Session 1: Fix unused variables (54 errors)
- Session 2: Fix case declarations + style violations (20 errors)
- **Goal**: Reduce linting errors by 74 (23% reduction)

### Week 2: Frontend Core Fixes
**Days 1-3: Shared Components**
- Session 3: Template accessibility (40 errors)
- Session 4-5: Shared component `any` types (50 errors)
- **Goal**: Reduce linting errors by 90 (28% reduction)

**Days 4-5: Services & Directives**
- Session 6-7: Services/directives `any` types (70 errors)
- **Goal**: Reduce linting errors by 70 (22% reduction)

### Week 3: Final Push
**Days 1-2: Cleanup**
- Session 8: Remaining shared components (50 errors)
- Session 9: Spec files + final cleanup (33 errors)
- **Goal**: Zero linting errors, green CI/CD

**Days 3-5: Verification & Polish**
- Full regression testing
- Documentation updates
- Sprint retrospective

---

## Definition of Done

### For Backend Stories
- [ ] Code follows Python PEP 8 standards
- [ ] All tests pass locally
- [ ] All tests pass in CI/CD
- [ ] No new flake8 or black violations
- [ ] Code reviewed (if applicable)

### For Frontend Stories
- [ ] Code follows Angular style guide
- [ ] Linting errors reduced as planned
- [ ] All existing tests still pass
- [ ] No new TypeScript compilation errors
- [ ] Manual testing completed
- [ ] Code reviewed (if applicable)

### For Sprint Completion
- [ ] All P0 (Critical) stories completed
- [ ] At least 75% of P1 (High) stories completed
- [ ] CI/CD pipeline fully green
- [ ] No blocking issues remain
- [ ] Sprint retrospective completed
- [ ] Next sprint planned

---

## Risks & Mitigation

### Risk 1: Frontend Linting Taking Longer Than Expected
**Likelihood**: High
**Impact**: Medium
**Mitigation**:
- Prioritize backend fixes first (higher impact)
- Frontend linting can continue in parallel
- Use --max-warnings flag temporarily if needed

### Risk 2: New Bugs Introduced During Fixes
**Likelihood**: Medium
**Impact**: High
**Mitigation**:
- Run full test suite after each session
- Manual testing of affected components
- Incremental commits for easy rollback

### Risk 3: Database/CI Configuration Issues
**Likelihood**: Low
**Impact**: High
**Mitigation**:
- Test configuration changes locally first
- Use postgres service pattern from backend job
- Document all CI/CD configuration changes

---

## Success Metrics

### Primary Metrics (Sprint Goal)
- **CI/CD Pipeline Status**: ❌ → ✅ (Target: All jobs passing)
- **Backend Tests**: ❌ → ✅ (Target: 100% passing)
- **Security Tests**: ❌ → ✅ (Target: 100% passing)

### Secondary Metrics (Code Quality)
- **Frontend Linting Errors**: 317 → <150 (Target: 50% reduction minimum)
- **Type Safety**: 199 `any` types → <100 (Target: 50% reduction minimum)
- **Test Coverage**: Unknown → Measured (Target: Establish baseline)

### Stretch Goals
- **Frontend Linting**: 317 → 0 (Complete cleanup)
- **Backend Coverage**: →80%+ (Improved coverage)
- **Documentation**: README updated, PR template created

---

## Daily Standups (Async Updates)

### Format
**Yesterday**: What was accomplished
**Today**: What will be worked on
**Blockers**: Any impediments

### Day 1 (2025-10-06)
**Yesterday**:
- Created comprehensive linting fix plan
- Fixed 8 frontend linting errors
- Established type definition patterns

**Today**:
- Fix security test database connection issue
- Fix backend test import/setup issues
- Target: Green backend tests

**Blockers**: None

---

## Retrospective Notes

*To be filled at end of sprint*

### What Went Well
-

### What Could Be Improved
-

### Action Items for Next Sprint
-

---

## References

- **Linting Fix Plan**: `Linting fix plan.md`
- **Project README**: `README.md`
- **CLAUDE.md**: `CLAUDE.md` (project architecture)
- **CI/CD Workflows**: `.github/workflows/`
- **Backend Tests**: `python-backend/tests/`
- **Frontend Config**: `angular-frontend/angular.json`

---

**Last Updated**: 2025-10-06
**Next Review**: Daily
**Sprint End Date**: TBD (flexible based on completion)
