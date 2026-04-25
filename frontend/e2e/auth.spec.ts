import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  const getUniqueEmail = () => `test-${Math.random().toString(36).substring(7)}@example.com`;
  const password = 'TestPassword123!';
  const fullName = 'Test User';

  test('should register a new user', async ({ page }) => {
    const email = getUniqueEmail();
    await page.goto('/register');
    
    await page.getByPlaceholder('Jane Smith').fill(fullName);
    await page.getByPlaceholder('you@company.com').fill(email);
    await page.getByPlaceholder('Min. 8 characters').fill(password);
    await page.getByPlaceholder('Repeat your password').fill(password);
    
    await page.click('button[type="submit"]');
    
    // After registration, it should redirect to dashboard (/)
    await expect(page).toHaveURL(/.*dashboard|.*\//, { timeout: 15000 });
    // Should see the waiting state
    await expect(page.getByText(/Your Dashboard is Waiting/i)).toBeVisible({ timeout: 20000 });
  });

  test('should login with existing user', async ({ page }) => {
    const email = getUniqueEmail();
    
    // First register
    await page.goto('/register');
    await page.getByPlaceholder('Jane Smith').fill(fullName);
    await page.getByPlaceholder('you@company.com').fill(email);
    await page.getByPlaceholder('Min. 8 characters').fill(password);
    await page.getByPlaceholder('Repeat your password').fill(password);
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/.*dashboard|.*\//, { timeout: 15000 });
    await expect(page.getByText(/Your Dashboard is Waiting/i)).toBeVisible({ timeout: 20000 });
    
    // Logout - use header profile button
    // The initials circle is usually the last button in the header
    await page.locator('header button').last().click();
    await page.getByText('Sign out').click();
    await expect(page).toHaveURL(/.*login/);

    // Now login
    await page.getByPlaceholder('you@company.com').fill(email);
    await page.getByPlaceholder('••••••••').fill(password);
    await page.click('button:has-text("Sign In")');
    
    await expect(page).toHaveURL(/.*dashboard|.*\//, { timeout: 15000 });
    await expect(page.getByText(/Your Dashboard is Waiting/i)).toBeVisible({ timeout: 20000 });
  });

  test('should fail login with wrong password', async ({ page }) => {
    const email = getUniqueEmail();
    await page.goto('/login');
    
    await page.getByPlaceholder('you@company.com').fill(email);
    await page.getByPlaceholder('••••••••').fill('wrong-password');
    await page.click('button:has-text("Sign In")');
    
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
  });
});
