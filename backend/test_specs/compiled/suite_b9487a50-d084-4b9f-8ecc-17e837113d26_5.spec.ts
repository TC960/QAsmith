import { test, expect } from '@playwright/test';

test.describe('Generated E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://www.cvs.com/');
  });

  test('Homepage Navigation Links Test', async ({ page }) => {
    // Verifies all main navigation links are present and clickable on CVS homepage

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('a:text(\'Manage Prescriptions\')')).toBeVisible();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('a:text(\'Deals of the Week\')')).toBeVisible();
    // Step 4: ActionType.EXPECT
    await expect(page.locator('a:text(\'MinuteClinic Services\')')).toBeVisible();
    // Step 5: ActionType.EXPECT
    await expect(page.locator('a:text(\'Savings & Rewards\')')).toBeVisible();
    // Step 6: ActionType.EXPECT
    await expect(page.locator('a:text(\'Photo\')')).toBeVisible();

    // No explicit assertions
  });

  test('Manage Prescriptions Link Test', async ({ page }) => {
    // Tests the functionality of the Manage Prescriptions link

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/');
    // Step 2: ActionType.CLICK
    await page.locator('a:text(\'Manage Prescriptions\')').click();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('text=Pharmacy')).toBeVisible();

    // No explicit assertions
  });

  test('Photo Services Navigation Test', async ({ page }) => {
    // Verifies navigation to photo services section

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/');
    // Step 2: ActionType.CLICK
    await page.locator('a:text(\'Photo\')').click();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('text=Photo Services')).toBeVisible();

    // No explicit assertions
  });

  test('Deals Section Navigation Test', async ({ page }) => {
    // Tests navigation to Deals of the Week section

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/');
    // Step 2: ActionType.CLICK
    await page.locator('a:text(\'Deals of the Week\')').click();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('text=Weekly Deals')).toBeVisible();

    // No explicit assertions
  });

  test('MinuteClinic Services Access Test', async ({ page }) => {
    // Verifies access to MinuteClinic Services section

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/');
    // Step 2: ActionType.CLICK
    await page.locator('a:text(\'MinuteClinic Services\')').click();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('text=MinuteClinic')).toBeVisible();

    // No explicit assertions
  });
});
