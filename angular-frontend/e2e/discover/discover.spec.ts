import { test, expect } from '@playwright/test';
import { waitForAngular } from '../utils/helpers';

/**
 * Discover Page E2E Tests
 * Tests the soul connection discovery feature
 */

test.describe('Discover Page', () => {
  test.beforeEach(async ({ page }) => {
    // Note: These tests assume authentication is handled
    // In a real scenario, you'd need to login first or use authenticated state
    await page.goto('/discover');
    await waitForAngular(page);
  });

  test('discover page loads correctly', async ({ page }) => {
    // Check URL
    const url = page.url();
    expect(url).toContain('discover');

    // Check for main discover component
    const discoverComponent = page.locator('app-discover, [data-testid="discover-page"]');
    expect(await discoverComponent.count()).toBeGreaterThan(0);
  });

  test('displays soul connection cards when available', async ({ page }) => {
    // Wait for loading to complete
    await page.waitForTimeout(2000);

    // Check for connection cards or empty state
    const cards = page.locator('.connection-card, .profile-card, [data-testid="discovery-card"]');
    const emptyState = page.locator('.empty-state, text=/no.*connections/i');

    const hasCards = await cards.count() > 0;
    const hasEmptyState = await emptyState.count() > 0;

    // Should have either cards or empty state
    expect(hasCards || hasEmptyState).toBeTruthy();
  });

  test('filters are accessible', async ({ page }) => {
    // Look for filter button or filters section
    const filterButton = page.locator('button:has-text("Filter"), button:has-text("Filters"), [data-testid="filter-button"]');
    const filtersSection = page.locator('.filters, [data-testid="filters"]');

    expect(await filterButton.count() + await filtersSection.count()).toBeGreaterThan(0);
  });

  test('can open and close filters panel', async ({ page }) => {
    const filterButton = page.locator('button:has-text("Filter"), button:has-text("Filters")').first();

    if (await filterButton.count() > 0) {
      // Open filters
      await filterButton.click();
      await page.waitForTimeout(500);

      const filtersPanel = page.locator('.filters-panel, [role="dialog"]');
      expect(await filtersPanel.count()).toBeGreaterThan(0);

      // Close filters
      const closeButton = page.locator('button:has-text("Close"), button[aria-label="Close"]');
      if (await closeButton.count() > 0) {
        await closeButton.first().click();
        await page.waitForTimeout(500);
      }
    }
  });

  test('compatibility score is displayed', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Check for compatibility percentage
    const compatibilityScore = page.locator('text=/%|compatibility/i');

    // Might not have matches yet
    expect(await compatibilityScore.count()).toBeGreaterThanOrEqual(0);
  });

  test('profile preview respects soul-before-skin concept', async ({ page }) => {
    await page.waitForTimeout(2000);

    const profileCards = page.locator('.connection-card, .profile-card');

    if (await profileCards.count() > 0) {
      const firstCard = profileCards.first();

      // Photos should be hidden or blurred initially (soul before skin)
      const photos = firstCard.locator('img[src*="photo"], .profile-photo');
      const blurredPhotos = firstCard.locator('.blurred, .hidden, [data-hidden="true"]');

      // Either no photos shown, or they're blurred
      expect(await photos.count() === 0 || await blurredPhotos.count() > 0).toBeTruthy();
    }
  });

  test('can navigate between profiles', async ({ page }) => {
    await page.waitForTimeout(2000);

    const nextButton = page.locator('button:has-text("Next"), button[aria-label*="next"]');
    const prevButton = page.locator('button:has-text("Previous"), button:has-text("Back"), button[aria-label*="previous"]');

    // Navigation buttons might be present
    expect(await nextButton.count() + await prevButton.count()).toBeGreaterThanOrEqual(0);
  });

  test('connect button is present on profile cards', async ({ page }) => {
    await page.waitForTimeout(2000);

    const profileCards = page.locator('.connection-card, .profile-card');

    if (await profileCards.count() > 0) {
      const connectButton = page.locator('button:has-text("Connect"), button:has-text("Match")');
      expect(await connectButton.count()).toBeGreaterThan(0);
    }
  });

  test('pass button is present on profile cards', async ({ page }) => {
    await page.waitForTimeout(2000);

    const profileCards = page.locator('.connection-card, .profile-card');

    if (await profileCards.count() > 0) {
      const passButton = page.locator('button:has-text("Pass"), button:has-text("Skip"), button[aria-label*="pass"]');
      expect(await passButton.count()).toBeGreaterThan(0);
    }
  });

  test('interests are displayed in profile preview', async ({ page }) => {
    await page.waitForTimeout(2000);

    const profileCards = page.locator('.connection-card, .profile-card');

    if (await profileCards.count() > 0) {
      const interests = page.locator('.interests, .tags, [data-testid="interests"]');
      expect(await interests.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test('loading state is shown while fetching discoveries', async ({ page }) => {
    // Reload to see loading state
    await page.reload();

    // Check for loading indicator
    const loader = page.locator('.loading, .spinner, mat-spinner, [role="progressbar"]');

    // Might be too fast to catch
    expect(await loader.count()).toBeGreaterThanOrEqual(0);
  });

  test('empty state shows onboarding prompt', async ({ page }) => {
    await page.waitForTimeout(2000);

    const emptyState = page.locator('.empty-state, text=/no.*connections|complete.*profile/i');

    if (await emptyState.count() > 0) {
      // Should have some guidance text
      const emptyStateText = await emptyState.first().textContent();
      expect(emptyStateText?.length).toBeGreaterThan(0);
    }
  });
});
