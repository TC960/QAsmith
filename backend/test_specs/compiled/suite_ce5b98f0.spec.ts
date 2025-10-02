import { test, expect } from '@playwright/test';

test.describe('Generated E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://rraval.vercel.app/');
  });

  test('Homepage loads with correct title', async ({ page }) => {
    // Verify homepage loads with expected title and content

    // Step 1: ActionType.GOTO
    await page.goto('https://rraval.vercel.app/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('text=AfterTheTrade — Portfolio (Not Advice)').first()).toBeVisible();

    // No explicit assertions
  });

  test('Homepage displays disclaimer', async ({ page }) => {
    // Verify the disclaimer text is visible on homepage

    // Step 1: ActionType.GOTO
    await page.goto('https://rraval.vercel.app/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('text=(Not Advice)').first()).toBeVisible();

    // No explicit assertions
  });
});
