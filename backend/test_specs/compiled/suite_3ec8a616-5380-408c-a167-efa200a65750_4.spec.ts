import { test, expect } from '@playwright/test';

test.describe('Generated E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://www.cvs.com/');
  });

  test('Clinic Locator Search', async ({ page }) => {
    // Tests the MinuteClinic location finder functionality

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/minuteclinic/clinic-locator/');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('.clinic-locator')).toBeVisible();
    // Step 3: ActionType.FILL
    await page.locator('#location-search').fill('10001');
    // Step 4: ActionType.CLICK
    await page.locator('#search-button').click();
    // Step 5: ActionType.EXPECT
    await expect(page.locator('.results-list')).toBeVisible();

    // No explicit assertions
  });

  test('Purchase History Navigation', async ({ page }) => {
    // Tests navigation between different purchase history sections

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/account/order/order-history');
    // Step 2: ActionType.CLICK
    await page.locator('a:text(\'Photo purchases\')').click();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('.photo-orders')).toBeVisible();
    // Step 4: ActionType.CLICK
    await page.locator('a:text(\'Contacts and glasses\')').click();
    // Step 5: ActionType.EXPECT
    await expect(page.locator('.vision-orders')).toBeVisible();
    // Step 6: ActionType.CLICK
    await page.locator('a:text(\'Other prescriptions\')').click();
    // Step 7: ActionType.EXPECT
    await expect(page.locator('.rx-orders')).toBeVisible();

    // No explicit assertions
  });

  test('Security Page Links', async ({ page }) => {
    // Verifies all security page links are accessible

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/retail/help/security');
    // Step 2: ActionType.EXPECT
    await expect(page.locator('a:text(\'MinuteClinic Services\')')).toBeVisible();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('a:text(\'Shop\')')).toBeVisible();
    // Step 4: ActionType.EXPECT
    await expect(page.locator('a:text(\'Savings & Rewards\')')).toBeVisible();
    // Step 5: ActionType.EXPECT
    await expect(page.locator('a[href=\'https://www.cvs.com/rx/dotm/ca\']')).toBeVisible();
    // Step 6: ActionType.EXPECT
    await expect(page.locator('a:text(\'Schedule a Vaccine\')')).toBeVisible();

    // No explicit assertions
  });

  test('Security Page Navigation', async ({ page }) => {
    // Tests navigation from security page to key sections

    // Step 1: ActionType.GOTO
    await page.goto('https://www.cvs.com/retail/help/security');
    // Step 2: ActionType.CLICK
    await page.locator('a:text(\'MinuteClinic Services\')').click();
    // Step 3: ActionType.EXPECT
    await expect(page.locator('.minuteclinic-services')).toBeVisible();
    // Step 4: ActionType.GOTO
    await page.goto('https://www.cvs.com/retail/help/security');
    // Step 5: ActionType.CLICK
    await page.locator('a:text(\'Schedule a Vaccine\')').click();
    // Step 6: ActionType.EXPECT
    await expect(page.locator('.vaccine-scheduler')).toBeVisible();

    // No explicit assertions
  });
});
