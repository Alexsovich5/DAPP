# E2E Testing with Playwright

This directory contains end-to-end (E2E) tests for the Dinner First Angular application using Playwright.

## Structure

```
e2e/
├── auth/              # Authentication flow tests (login, register, logout)
├── discover/          # Discovery page tests (soul connections, matching)
├── onboarding/        # Emotional onboarding tests
├── profile/           # User profile tests
├── fixtures/          # Test data and fixtures
├── utils/             # Helper functions and utilities
├── smoke.spec.ts      # Basic smoke tests
└── README.md          # This file
```

## Running Tests

### Prerequisites
- Application must be running on `http://localhost:5001`
- Or tests will start the dev server automatically

### Commands

```bash
# Run all E2E tests
npm run e2e

# Run E2E tests in CI mode (with reporters)
npm run e2e:ci

# Run tests in headed mode (see browser)
npm run e2e:headed

# Debug tests
npm run e2e:debug

# Interactive UI mode
npm run e2e:ui

# Run specific test file
npx playwright test e2e/auth/login.spec.ts

# Run tests matching a pattern
npx playwright test --grep "login"
```

## Writing Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { waitForAngular } from './utils/helpers';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/route');
    await waitForAngular(page);
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await page.click('button');
    await expect(page.locator('.result')).toBeVisible();
  });
});
```

### Best Practices

1. **Use data-testid attributes** for reliable selectors
2. **Wait for Angular** to stabilize before assertions
3. **Clear storage** between authentication tests
4. **Use fixtures** for test data
5. **Take screenshots** on failures (automatic)
6. **Keep tests independent** - each test should be able to run alone

### Helpers

Common helper functions are available in `utils/helpers.ts`:

- `waitForAngular(page)` - Wait for Angular to stabilize
- `login(page, email, password)` - Login helper
- `logout(page)` - Logout helper
- `clearStorage(page)` - Clear localStorage and sessionStorage
- `isAuthenticated(page)` - Check auth status
- `takeScreenshot(page, name)` - Custom screenshot
- `waitForElement(page, selector)` - Wait for element
- `elementExists(page, selector)` - Check if element exists

### Fixtures

Test data fixtures are in `fixtures/test-users.ts`:

```typescript
import { testUsers } from './fixtures/test-users';

const { email, password } = testUsers.validUser;
```

## Configuration

Test configuration is in `playwright.config.ts`:

- Base URL: `http://localhost:5001`
- Browsers: Chromium (default), Firefox, WebKit (commented)
- Reporters: HTML, JSON, JUnit, Console
- Automatic retries on CI
- Screenshots and videos on failure

## CI/CD Integration

E2E tests run automatically in GitHub Actions:

```yaml
- name: Run E2E tests
  run: npm run e2e:ci
```

Tests will:
1. Start the dev server automatically
2. Run all tests in parallel
3. Generate HTML report in `e2e-results/html`
4. Upload artifacts on failure

## Debugging

### View Test Report

```bash
npx playwright show-report e2e-results/html
```

### Debug Mode

```bash
npm run e2e:debug
```

This opens Playwright Inspector for step-by-step debugging.

### UI Mode

```bash
npm run e2e:ui
```

Interactive mode with time-travel debugging.

## Troubleshooting

### Tests timing out
- Increase timeout in test or config
- Check if app is running on correct port
- Use `await waitForAngular(page)` after navigation

### Element not found
- Add `data-testid` attributes to components
- Use more specific selectors
- Wait for element: `await page.waitForSelector(selector)`

### Flaky tests
- Add proper waits (`waitForAngular`, `waitForLoadState`)
- Avoid hard-coded timeouts when possible
- Check for race conditions

## Current Test Coverage

- ✅ Smoke tests (app health checks)
- ✅ Authentication (login flow)
- ✅ Discovery page (basic navigation)
- 🚧 Onboarding flow (TODO)
- 🚧 Profile management (TODO)
- 🚧 Messaging (TODO)
- 🚧 Revelations (TODO)

## TODO

- [ ] Add full authentication flow tests (register, forgot password)
- [ ] Add onboarding flow tests
- [ ] Add profile creation/editing tests
- [ ] Add messaging E2E tests
- [ ] Add revelation timeline tests
- [ ] Add mobile viewport tests
- [ ] Add accessibility tests
- [ ] Add performance tests
- [ ] Set up visual regression testing
