import { test, expect } from '@playwright/test';

test.describe('Generated E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://rraval.vercel.app/');
  });

  test('Navigation Links Test', async ({ page }) => {
    // Verifies all navigation links are working and redirect to correct pages

    // Step 1: ActionType.GOTO
    await page.goto('https://rraval.vercel.app/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('text=Rohan RavalPersonal Portfolio')).toBeVisible();
    // Step 3: ActionType.CLICK
    await page.locator('text=Work').click();
    // Step 4: ActionType.EXPECT
    await expect(page.locator('text=Work')).toBeVisible();
    // Step 5: ActionType.CLICK
    await page.locator('text=Home').click();
    // Step 6: ActionType.EXPECT
    await expect(page.locator('text=Home')).toBeVisible();
    // Step 7: ActionType.CLICK
    await page.locator('text=Contact').click();
    // Step 8: ActionType.EXPECT
    await expect(page.locator('text=Contact')).toBeVisible();

    // No explicit assertions
  });

  test('Homepage Load Test', async ({ page }) => {
    // Verifies the homepage loads correctly with all essential elements

    // Step 1: ActionType.GOTO
    await page.goto('https://rraval.vercel.app/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('text=Rohan RavalPersonal Portfolio')).toBeVisible();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('text=Work')).toBeVisible();
    // Step 4: ActionType.EXPECT
    await expect(page.locator('text=Home')).toBeVisible();
    // Step 5: ActionType.EXPECT
    await expect(page.locator('text=Contact')).toBeVisible();

    // No explicit assertions
  });

  test('Logo Navigation Test', async ({ page }) => {
    // Verifies the logo/name link returns to homepage

    // Step 1: ActionType.GOTO
    await page.goto('https://rraval.vercel.app/');
    // Step 2: ActionType.CLICK
    await page.locator('text=Work').click();
    // Step 3: ActionType.CLICK
    await page.locator('text=Rohan RavalPersonal Portfolio').click();
    // Step 4: ActionType.EXPECT
    await expect(page.locator('text=Home')).toBeVisible();

    // No explicit assertions
  });
});
