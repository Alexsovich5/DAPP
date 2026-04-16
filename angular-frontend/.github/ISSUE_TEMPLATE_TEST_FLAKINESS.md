# Test Suite Flakiness and Remaining Failures

## Issue Summary

The Angular test suite shows execution order sensitivity with 18-31 failures (97-98% pass rate) depending on test execution order. All infrastructure is solid, but some tests exhibit flaky behavior when run in the full suite vs isolation.

## Current Status

- **Total Tests**: 1,047
- **Pass Rate**: 97-98% (1,016-1,029 passing)
- **Failures**: 18-31 (varies by execution order)
- **Stable Infrastructure**: localStorage/sessionStorage mocks working correctly

## Confirmed Working

✅ **ErrorLoggingService**: All 43 tests pass in isolation
✅ **AuthService**: All localStorage tests passing
✅ **OnboardingApiService**: All localStorage tests passing
✅ **localStorage Mock**: Full Storage API implementation with proper closure handling

## Remaining Test Failures

### Category 1: Execution Order Sensitive (0-13 failures)

**ABTestingService** (0-9 failures)
- Tests pass when run in isolation
- Fail when run after certain other tests
- Likely cause: Shared localStorage state from previous test suites
- Files: `src/app/core/services/ab-testing.service.spec.ts`

**ErrorLoggingService** (0-5 failures)
- All 43 tests pass when run in isolation
- 5 production mode tests fail in full suite
- Environment.production timing/state pollution
- Files: `src/app/core/services/error-logging.service.spec.ts`

**OnboardingApiService** (0-2 failures)
- localStorage integration tests
- Execution order dependent
- Files: `src/app/core/services/onboarding-api.service.spec.ts`

**HapticFeedbackService** (0-1 failure)
- Navigator.vibrate API mocking
- Files: `src/app/core/services/haptic-feedback.service.spec.ts`

### Category 2: Component Integration (12 failures)

**DiscoverComponent** (12 failures)
- Complex component with 11 service dependencies
- Requires comprehensive service mocking
- Tests need architectural review
- Files: `src/app/features/discover/discover.component.spec.ts`

Specific failing tests:
1. Swipe Gesture Handling: swipe left/right/up (3 tests)
2. Soul Orb Interactions: compatibility state (1 test)
3. Match Celebrations: trigger celebration (1 test)
4. Keyboard Navigation: Tab and Enter/Space (2 tests)
5. Haptic Feedback: success and hover feedback (2 tests)
6. Filter Changes: reload discoveries (1 test)
7. Accessibility: screen reader descriptions (1 test)
8. A/B Testing: track interactions (1 test)

### Category 3: Async/Timing (1 failure)

**WebSocketPoolService** (1 failure)
- Edge case: multiple simultaneous connections to same URL
- Async connection pooling race condition
- Files: `src/app/core/services/websocket-pool.service.spec.ts`

## Root Causes Identified

### 1. Test Isolation Issues
- Some tests modify shared global state (environment.production, localStorage)
- State cleanup not always happening in afterEach hooks
- Tests run in different orders produce different results

### 2. Service Dependency Complexity
- DiscoverComponent depends on 11 services
- Missing or incomplete service mocks
- Integration tests need better isolation

### 3. Async Timing
- WebSocket connection pooling has race conditions
- Need better async test patterns (fakeAsync, tick)

## Attempted Solutions

### ❌ Global beforeEach Hooks
**Approach**: Clear localStorage before every test globally
**Result**: Broke 400+ tests that intentionally persist state
**Lesson**: Global cleanup too aggressive for Angular test patterns

### ✅ Individual Suite Isolation
**Approach**: Each test suite manages its own beforeEach/afterEach
**Result**: Works well for most tests
**Recommendation**: Continue this pattern

## Recommended Fixes

### Short Term (Achieve 100% pass rate)

1. **Fix DiscoverComponent Mocks**
   - Create comprehensive service mocks for all 11 dependencies
   - Use Jasmine spy objects consistently
   - Consider using TestBed.overrideProvider for complex services

2. **Add Test Isolation to Flaky Services**
   ```typescript
   describe('MyService', () => {
     beforeEach(() => {
       localStorage.clear();
       sessionStorage.clear();
       // Reset environment to default state
       Object.assign(environment, originalEnvironment);
     });
   });
   ```

3. **Fix WebSocket Async Tests**
   - Use `fakeAsync` and `tick()` for better async control
   - Add proper cleanup in afterEach for connection pools

### Long Term (Improve Test Architecture)

1. **Test Execution Order Independence**
   - Ensure all tests can run in any order
   - Add stricter beforeEach/afterEach hooks
   - Consider test.each patterns for data-driven tests

2. **Component Integration Test Strategy**
   - Move complex integration tests to separate e2e suite
   - Keep unit tests focused on isolated component logic
   - Use component harnesses for Material components

3. **Shared Test Utilities**
   - Create reusable mock factories for common services
   - Build test data builders for complex objects
   - Standardize test setup patterns

## How to Reproduce

### Run All Tests
```bash
npm test
# Expected: 18-31 failures (varies by execution order)
```

### Run Specific Suite in Isolation
```bash
npm test -- --include="**/error-logging.service.spec.ts" --no-watch
# Expected: 0 failures (all pass)
```

### Run Full Suite Multiple Times
```bash
npm test && npm test && npm test
# Observe: Different number of failures each run (18-31 range)
```

## Success Metrics

- [x] localStorage mock infrastructure complete
- [x] 97-98% pass rate achieved (from 95.3%)
- [x] All Auth/Onboarding tests passing
- [ ] 100% pass rate in full suite
- [ ] Consistent results across multiple runs
- [ ] All tests pass in isolation AND full suite

## Related Files

### Infrastructure
- `src/test-setup.ts` - localStorage/sessionStorage mocks
- `karma.conf.js` - Karma test configuration
- `angular.json` - Angular test builder config
- `tsconfig.spec.json` - TypeScript test compilation

### Flaky Tests
- `src/app/core/services/ab-testing.service.spec.ts`
- `src/app/core/services/error-logging.service.spec.ts`
- `src/app/core/services/onboarding-api.service.spec.ts`
- `src/app/core/services/haptic-feedback.service.spec.ts`
- `src/app/core/services/websocket-pool.service.spec.ts`
- `src/app/features/discover/discover.component.spec.ts`

## Additional Context

This issue tracks the remaining test failures after successfully implementing localStorage/sessionStorage mocks and fixing 21+ tests. The infrastructure is solid, but test isolation and component mocking need improvement to achieve 100% pass rate.

The test suite is production-ready at 97-98% pass rate, but these remaining failures should be addressed to ensure reliable CI/CD and prevent regression.
