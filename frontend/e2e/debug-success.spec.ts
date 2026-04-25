import { test, expect } from '@playwright/test';

test('debug registration success', async ({ page }) => {
  const randomId = Math.random().toString(36).substring(7);
  const email = `success-${randomId}@example.com`;
  const password = 'TestPassword123!';
  const fullName = 'Test User';
  
  page.on('request', request => console.log('>>', request.method(), request.url()));
  page.on('response', response => console.log('<<', response.status(), response.url()));

  console.log('--- Navigating to /register ---');
  await page.goto('/register');
  
  await page.getByPlaceholder('Jane Smith').fill(fullName);
  await page.getByPlaceholder('you@company.com').fill(email);
  await page.getByPlaceholder('Min. 8 characters').fill(password);
  await page.getByPlaceholder('Repeat your password').fill(password);
  
  console.log('--- Submitting registration ---');
  await page.click('button[type="submit"]');
  
  // Wait for potential redirect
  console.log('--- Waiting for redirect ---');
  try {
    await expect(page).toHaveURL(/.*dashboard|.*\//, { timeout: 15000 });
    console.log('Redirect successful to:', page.url());
  } catch (e) {
    console.log('Redirect timed out or failed. Current URL:', page.url());
  }
  
  await page.waitForTimeout(5000);
  await page.screenshot({ path: 'registration-success.png' });
  
  const textContent = await page.evaluate(() => document.body.innerText);
  console.log('--- ALL VISIBLE TEXT ---');
  console.log(textContent);
  
  const content = await page.content();
  console.log('--- HTML length ---', content.length);
});
