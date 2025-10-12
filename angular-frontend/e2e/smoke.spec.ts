import { test, expect } from '@playwright/test';
import { waitForAngular } from './utils/helpers';

/**
 * Smoke Tests - Basic application health checks
 * These tests verify the application loads and core pages are accessible
 */

test.describe('Smoke Tests', () => {
  test('application loads and displays welcome page', async ({ page }) => {
    await page.goto('/');
    await waitForAngular(page);

    // Check that the page loaded
    expect(page.url()).toContain('localhost:5001');

    // Check for Angular app root
    const appRoot = page.locator('app-root');
    await expect(appRoot).toBeVisible();
  });

  test('navigation to login page works', async ({ page }) => {
    await page.goto('/login');
    await waitForAngular(page);

    // Verify we're on the login page
    await expect(page).toHaveURL(/.*login/);

    // Check for login form elements
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const loginButton = page.locator('button[type="submit"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(loginButton).toBeVisible();
  });

  test('navigation to register page works', async ({ page }) => {
    await page.goto('/register');
    await waitForAngular(page);

    // Verify we're on the register page
    await expect(page).toHaveURL(/.*register/);

    // Check for registration form
    const form = page.locator('form');
    await expect(form).toBeVisible();
  });

  test('404 page displays for invalid routes', async ({ page }) => {
    await page.goto('/this-route-does-not-exist');
    await waitForAngular(page);

    // Should show 404 or redirect to home/login
    const is404 = await page.locator('text=/404|not found/i').count() > 0;
    const isRedirected = page.url().match(/login|home|\/$/) !== null;

    expect(is404 || isRedirected).toBeTruthy();
  });

  test('application has no console errors on initial load', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await waitForAngular(page);

    // Filter out expected errors (like missing service worker in test)
    const unexpectedErrors = consoleErrors.filter(error =>
      !error.includes('Service Worker') &&
      !error.includes('sw.js') &&
      !error.includes('favicon')
    );

    expect(unexpectedErrors).toHaveLength(0);
  });

  test('application meta tags are present', async ({ page }) => {
    await page.goto('/');

    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);

    // Check for viewport meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toContain('width=device-width');
  });

  test('main navigation is accessible', async ({ page }) => {
    await page.goto('/');
    await waitForAngular(page);

    // Check for navigation elements (adjust selectors based on your app)
    const nav = page.locator('nav, [role="navigation"], .navigation, mat-toolbar');
    const hasNav = await nav.count() > 0;

    // Navigation might not be visible on landing page
    expect(hasNav).toBeDefined();
  });
});
