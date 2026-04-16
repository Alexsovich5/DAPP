import { Page, expect } from '@playwright/test';

/**
 * Helper utilities for E2E tests
 */

/**
 * Wait for Angular to be ready
 */
export async function waitForAngular(page: Page): Promise<void> {
  try {
    // First wait for load state
    await page.waitForLoadState('domcontentloaded');

    // Then try to wait for Angular if available
    await page.waitForFunction(() => {
      const testabilities = (window as any).getAllAngularTestabilities?.();
      if (!testabilities || testabilities.length === 0) {
        // Angular not loaded yet or not available, consider stable
        return true;
      }
      return testabilities.every((t: any) => t.isStable());
    }, { timeout: 5000 });
  } catch {
    // If Angular testability check fails, just wait for network idle
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
      // If even network idle fails, continue anyway
    });
  }
}

/**
 * Login helper
 */
export async function login(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/login');
  await waitForAngular(page);

  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for navigation after login
  await page.waitForURL('**/discover', { timeout: 10000 }).catch(() => {
    // Might redirect to onboarding or profile
    return page.waitForLoadState('networkidle');
  });
}

/**
 * Logout helper
 */
export async function logout(page: Page): Promise<void> {
  // Click user menu or logout button
  await page.click('[data-testid="user-menu"]').catch(() => {
    return page.click('button:has-text("Logout")');
  });
  await page.click('button:has-text("Logout")');
  await page.waitForURL('**/login');
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    const token = await page.evaluate(() => {
      return localStorage.getItem('token') || sessionStorage.getItem('token');
    });
    return !!token;
  } catch {
    return false;
  }
}

/**
 * Clear all storage
 */
export async function clearStorage(page: Page): Promise<void> {
  try {
    await page.evaluate(() => {
      try {
        localStorage.clear();
      } catch (e) {
        // localStorage might not be accessible
      }
      try {
        sessionStorage.clear();
      } catch (e) {
        // sessionStorage might not be accessible
      }
    });
  } catch {
    // If evaluate fails entirely, continue anyway
  }
}

/**
 * Take screenshot with timestamp
 */
export async function takeScreenshot(page: Page, name: string): Promise<void> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ path: `e2e-results/screenshots/${name}-${timestamp}.png`, fullPage: true });
}

/**
 * Wait for element to be visible
 */
export async function waitForElement(page: Page, selector: string, timeout = 5000): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible', timeout });
}

/**
 * Check if element exists
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  try {
    await page.waitForSelector(selector, { timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Get element text
 */
export async function getElementText(page: Page, selector: string): Promise<string> {
  const element = await page.locator(selector);
  return await element.textContent() || '';
}

/**
 * Check for error messages
 */
export async function checkForErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  // Check for Angular error toasts
  const errorToasts = await page.locator('.error-toast, .mat-error, [role="alert"]').allTextContents();
  errors.push(...errorToasts);

  // Check console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}
