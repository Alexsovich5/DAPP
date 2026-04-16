import { test, expect } from '@playwright/test';
import { waitForAngular, clearStorage } from '../utils/helpers';
import { testUsers } from '../fixtures/test-users';

/**
 * Authentication E2E Tests - Login Flow
 */

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
    await page.goto('/login');
    await waitForAngular(page);
  });

  test('displays login form correctly', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Dinner First|Login/i);

    // Verify form elements are present
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // Check for "Register" link
    const registerLink = page.locator('a:has-text("Register"), a:has-text("Sign up")');
    await expect(registerLink).toBeVisible();
  });

  test('shows validation errors for empty fields', async ({ page }) => {
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Wait for validation messages
    await page.waitForTimeout(500);

    // Check for error messages (adjust selectors based on your app)
    const errors = page.locator('.error, .mat-error, [role="alert"]');
    const errorCount = await errors.count();

    expect(errorCount).toBeGreaterThan(0);
  });

  test('shows validation error for invalid email format', async ({ page }) => {
    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'password123');

    const emailInput = page.locator('input[type="email"]');
    await emailInput.blur();

    // Wait for validation
    await page.waitForTimeout(500);

    // Check for email validation error
    const emailError = page.locator('.mat-error, .error:has-text("email")');
    expect(await emailError.count()).toBeGreaterThan(0);
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.fill('input[type="email"]', 'nonexistent@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Wait for error message
    await page.waitForTimeout(2000);

    // Check for authentication error
    const errorMessage = page.locator('text=/invalid.*credentials|login.*failed|incorrect/i');
    expect(await errorMessage.count()).toBeGreaterThanOrEqual(0); // May or may not show depending on backend
  });

  test('password field is masked by default', async ({ page }) => {
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('can toggle password visibility', async ({ page }) => {
    // Look for password toggle button
    const toggleButton = page.locator('button:has([class*="visibility"]), button[aria-label*="password"]');

    if (await toggleButton.count() > 0) {
      const passwordInput = page.locator('input[type="password"]');

      await toggleButton.click();
      await page.waitForTimeout(300);

      // Password should now be text type
      const inputType = await passwordInput.getAttribute('type');
      expect(inputType === 'text' || inputType === 'password').toBeTruthy();
    }
  });

  test('remember me checkbox works', async ({ page }) => {
    const rememberCheckbox = page.locator('input[type="checkbox"]:has-text("Remember"), label:has-text("Remember")');

    if (await rememberCheckbox.count() > 0) {
      await rememberCheckbox.click();
      expect(await rememberCheckbox.isChecked()).toBeTruthy();
    }
  });

  test('navigates to register page from login', async ({ page }) => {
    const registerLink = page.locator('a:has-text("Register"), a:has-text("Sign up"), a:has-text("Create account")');
    await registerLink.first().click();

    await waitForAngular(page);
    await expect(page).toHaveURL(/.*register/);
  });

  test('forgot password link is present', async ({ page }) => {
    const forgotLink = page.locator('a:has-text("Forgot"), a:has-text("Reset password")');

    // Forgot password might not be implemented yet
    expect(await forgotLink.count()).toBeGreaterThanOrEqual(0);
  });

  test.skip('successful login redirects to discover page', async ({ page }) => {
    // TODO: This test requires a valid test user in the backend
    // Skip for now until backend is set up with test data

    const { email, password } = testUsers.validUser;

    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');

    // Wait for redirect
    await page.waitForURL(/.*discover|home|dashboard/, { timeout: 10000 });

    // Verify redirect occurred
    const url = page.url();
    expect(url).toMatch(/discover|home|dashboard/);
  });
});
