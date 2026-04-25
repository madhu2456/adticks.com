import { test, expect } from '@playwright/test';

test.describe('SEO Scan Pipeline', () => {
  const getUniqueEmail = () => `seo-test-${Math.random().toString(36).substring(7)}@example.com`;
  const password = 'TestPassword123!';
  const randomId = Math.random().toString(36).substring(7);
  const brandName = `Test Brand ${randomId}`;
  const domain = `test-${randomId}.com`;

  test.beforeEach(async ({ page }) => {
    const email = getUniqueEmail();
    // Register
    await page.goto('/register');
    await page.getByPlaceholder('Jane Smith').fill('SEO Tester');
    await page.getByPlaceholder('you@company.com').fill(email);
    await page.getByPlaceholder('Min. 8 characters').fill(password);
    await page.getByPlaceholder('Repeat your password').fill(password);
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/.*dashboard|.*\//, { timeout: 15000 });
  });

  test('should create a project and run a scan', async ({ page }) => {
    test.setTimeout(120000);
    // Should see empty state if no projects
    await expect(page.getByText(/Your Dashboard is Waiting/i)).toBeVisible({ timeout: 15000 });
    
    // Click "Add a project" - in this UI we click the project selector first
    await page.click('button:has-text("No Project")');
    await page.click('button:has-text("Add new project")');
    
    // Fill Project Modal
    await page.fill('input[placeholder="e.g. Acme Corp"]', brandName);
    await page.fill('input[placeholder="e.g. acme.com"]', domain);
    await page.click('button:has-text("Create Project")');
    
    // Should now show project dashboard
    await expect(page.getByText(brandName)).toBeVisible({ timeout: 10000 });
    
    // Run Scan
    await page.click('button:has-text("Refresh")');
    
    // Scan Queued Modal pops up
    await expect(page.getByText(/Scan Queued/i)).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("OK")');
    
    // Wait for "Scan Complete" alert - using 2 minute timeout
    // We search for "Scan Complete" title
    await expect(page.getByText('Scan Complete')).toBeVisible({ timeout: 120000 });
    
    // Verify the success message
    await expect(page.getByText(/completed successfully/i)).toBeVisible();
    
    // Click OK on completion alert
    await page.click('button:has-text("OK")');
    
    // Verify results - visibility score should be visible on dashboard
    await expect(page.getByText(/Visibility Score/i)).toBeVisible({ timeout: 10000 });
  });
});
