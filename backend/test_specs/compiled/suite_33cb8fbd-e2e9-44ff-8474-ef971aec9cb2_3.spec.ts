import { test, expect } from '@playwright/test';

test.describe('Generated E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://example.com/');
  });

  test('Example Domain Page Loads Successfully', async ({ page }) => {
    // Verifies that the example.com page loads and displays correctly

    // Step 1: ActionType.GOTO
    await page.goto('https://example.com/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('h1')).toHaveText('Example Domain');
    // Step 3: ActionType.EXPECT
    await expect(page.locator('p')).toBeVisible();

    // No explicit assertions
  });

  test('More Information Link Works', async ({ page }) => {
    // Verifies that the 'More information' link exists and points to the correct URL

    // Step 1: ActionType.GOTO
    await page.goto('https://example.com/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('a')).toHaveAttribute('https://www.iana.org/domains/reserved');
    // Step 3: ActionType.EXPECT
    await expect(page.locator('a')).toHaveText('More information...');

    // No explicit assertions
  });

  test('Page Accessibility', async ({ page }) => {
    // Verifies basic accessibility features of the page

    // Step 1: ActionType.GOTO
    await page.goto('https://example.com/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('html')).toHaveAttribute('en');
    // Step 3: ActionType.EXPECT
    await expect(page.locator('title')).toHaveText('Example Domain');

    // No explicit assertions
  });
});
