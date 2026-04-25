import { test, expect } from '@playwright/test';

test('debug page state', async ({ page }) => {
  const email = `debug-${Math.random().toString(36).substring(7)}@example.com`;
  
  page.on('request', request => console.log('>>', request.method(), request.url()));
  page.on('response', response => console.log('<<', response.status(), response.url()));

  console.log('--- Navigating to /login ---');
  await page.goto('/login');
  await page.screenshot({ path: 'login-page.png' });
  console.log('Page title:', await page.title());
  
  console.log('--- Testing wrong password ---');
  await page.getByPlaceholder('you@company.com').fill(email);
  await page.getByPlaceholder('••••••••').fill('wrong-password');
  await page.click('button:has-text("Sign In")');
  
  // Wait a bit for the error to appear
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'login-error.png' });
  
  const content = await page.content();
  console.log('--- FULL PAGE CONTENT LENGTH ---', content.length);
  
  // Find all visible text
  const textContent = await page.evaluate(() => document.body.innerText);
  console.log('--- ALL VISIBLE TEXT ---');
  console.log(textContent);
  
  console.log('--- SEARCHING FOR ERROR INDICATORS ---');
  const errorKeywords = ['invalid', 'wrong', 'error', 'failed', 'password', 'email'];
  errorKeywords.forEach(word => {
    if (textContent.toLowerCase().includes(word)) {
      console.log(`Found keyword: ${word}`);
    }
  });
});
