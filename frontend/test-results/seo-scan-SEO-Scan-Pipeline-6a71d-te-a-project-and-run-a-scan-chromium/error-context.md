# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: seo-scan.spec.ts >> SEO Scan Pipeline >> should create a project and run a scan
- Location: e2e\seo-scan.spec.ts:23:7

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Scan Complete')
Expected: visible
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 120000ms
  - waiting for getByText('Scan Complete')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - complementary [ref=e4]:
      - generic [ref=e5]:
        - generic [ref=e6]:
          - img [ref=e8]
          - generic [ref=e9]:
            - generic [ref=e10]: AdTicks
            - generic [ref=e11]: BETA
        - button "Collapse sidebar" [ref=e12] [cursor=pointer]:
          - img [ref=e13]
      - navigation [ref=e15]:
        - generic [ref=e16]:
          - paragraph [ref=e17]: Main
          - link "Overview" [ref=e20] [cursor=pointer]:
            - /url: /
            - img [ref=e22]
            - generic [ref=e27]: Overview
        - generic [ref=e28]:
          - paragraph [ref=e29]: Intelligence
          - generic [ref=e30]:
            - link "SEO Hub" [ref=e32] [cursor=pointer]:
              - /url: /seo
              - img [ref=e33]
              - generic [ref=e36]: SEO Hub
            - link "AEO Hub NEW" [ref=e38] [cursor=pointer]:
              - /url: /aeo
              - img [ref=e39]
              - generic [ref=e41]: AEO Hub
              - generic [ref=e43]: NEW
            - link "Local SEO" [ref=e48] [cursor=pointer]:
              - /url: /geo
              - img [ref=e49]
              - generic [ref=e52]: Local SEO
            - link "Search Console" [ref=e54] [cursor=pointer]:
              - /url: /gsc
              - img [ref=e55]
              - generic [ref=e57]: Search Console
        - generic [ref=e58]:
          - paragraph [ref=e59]: Performance
          - generic [ref=e60]:
            - link "Ads" [ref=e62] [cursor=pointer]:
              - /url: /ads
              - img [ref=e63]
              - generic [ref=e66]: Ads
            - link "Insights" [ref=e68] [cursor=pointer]:
              - /url: /insights
              - img [ref=e69]
              - generic [ref=e71]: Insights
        - generic [ref=e72]:
          - link "Settings" [ref=e74] [cursor=pointer]:
            - /url: /settings
            - img [ref=e75]
            - generic [ref=e78]: Settings
          - link "Help & Docs" [ref=e80] [cursor=pointer]:
            - /url: /help
            - img [ref=e81]
            - generic [ref=e84]: Help & Docs
      - generic [ref=e87]:
        - generic [ref=e88]:
          - generic [ref=e89]:
            - paragraph [ref=e90]: Trial Plan
            - paragraph [ref=e91]: 13 days remaining
          - img [ref=e93]
        - paragraph [ref=e98]: 7% of trial period used
        - button "Upgrade to Pro" [ref=e99] [cursor=pointer]:
          - text: Upgrade to Pro
          - img [ref=e100]
      - generic [ref=e102] [cursor=pointer]:
        - generic [ref=e103]: ST
        - generic [ref=e104]:
          - paragraph [ref=e106]: SEO Tester
          - paragraph [ref=e107]: seo-test-7c7jj@example.com
        - img [ref=e109]
    - banner [ref=e112]:
      - button "T Test Brand tlkxbo test-tlkxbo.com" [ref=e114] [cursor=pointer]:
        - generic [ref=e115]: T
        - generic [ref=e116]:
          - paragraph [ref=e117]: Test Brand tlkxbo
          - paragraph [ref=e118]:
            - img [ref=e119]
            - text: test-tlkxbo.com
        - img [ref=e122]
      - generic [ref=e124]:
        - img [ref=e125]
        - generic [ref=e127]: Overview
      - button "Search anything... ⌘ K" [ref=e128] [cursor=pointer]:
        - img [ref=e129]
        - generic [ref=e132]: Search anything...
        - generic [ref=e133]:
          - generic [ref=e134]: ⌘
          - generic [ref=e135]: K
      - generic [ref=e136]:
        - button "Switch to light mode" [ref=e137] [cursor=pointer]:
          - img [ref=e138]
        - generic [ref=e146]: Live
        - button [ref=e148] [cursor=pointer]:
          - img [ref=e149]
        - button "ST" [ref=e153] [cursor=pointer]
    - main [ref=e154]:
      - generic [ref=e157]:
        - generic [ref=e158]:
          - generic [ref=e159]:
            - heading "Good afternoon, SEO Tester 👋" [level=1] [ref=e161]
            - generic [ref=e162]:
              - generic [ref=e163]:
                - img [ref=e164]
                - text: Just now
              - generic [ref=e168]:
                - img [ref=e169]
                - text: test-tlkxbo.com
          - generic [ref=e172]:
            - button "Refresh" [ref=e173] [cursor=pointer]:
              - img [ref=e174]
              - generic [ref=e179]: Refresh
            - link "0 insights" [ref=e180] [cursor=pointer]:
              - /url: /insights
              - img [ref=e181]
              - generic [ref=e183]: 0 insights
              - img [ref=e184]
        - generic [ref=e186]:
          - link "SEO Report Export rankings" [ref=e187] [cursor=pointer]:
            - /url: /seo
            - img [ref=e189]
            - generic [ref=e190]:
              - paragraph [ref=e191]: SEO Report
              - paragraph [ref=e192]: Export rankings
            - img [ref=e193]
          - link "AI Scan Check LLM mentions" [ref=e196] [cursor=pointer]:
            - /url: /aeo
            - img [ref=e198]
            - generic [ref=e200]:
              - paragraph [ref=e201]: AI Scan
              - paragraph [ref=e202]: Check LLM mentions
            - img [ref=e203]
          - link "GSC Insights Search analytics" [ref=e206] [cursor=pointer]:
            - /url: /gsc
            - img [ref=e208]
            - generic [ref=e210]:
              - paragraph [ref=e211]: GSC Insights
              - paragraph [ref=e212]: Search analytics
            - img [ref=e213]
          - link "Campaign Perf. Ad performance" [ref=e216] [cursor=pointer]:
            - /url: /ads
            - img [ref=e218]
            - generic [ref=e222]:
              - paragraph [ref=e223]: Campaign Perf.
              - paragraph [ref=e224]: Ad performance
            - img [ref=e225]
        - generic [ref=e228]:
          - generic [ref=e230]:
            - generic [ref=e231]:
              - generic [ref=e232]:
                - heading "Visibility Score" [level=3] [ref=e233]
                - paragraph [ref=e234]: Unified brand presence index
              - generic [ref=e235]: Needs Work
            - generic [ref=e237]:
              - generic [ref=e238]:
                - img [ref=e241]:
                  - generic [ref=e243]:
                    - img [ref=e244]
                    - img [ref=e245]
                    - img [ref=e246]
                    - img [ref=e247]
                - generic:
                  - generic: "0"
                  - generic: Score
              - generic [ref=e248]:
                - link "SEO Hub 0% 0" [ref=e249] [cursor=pointer]:
                  - /url: /seo
                  - generic [ref=e250]:
                    - generic [ref=e251]: SEO Hub
                    - generic [ref=e252]:
                      - generic [ref=e253]:
                        - img [ref=e254]
                        - text: 0%
                      - generic [ref=e257]: "0"
                - link "AI Visibility 0% 0" [ref=e259] [cursor=pointer]:
                  - /url: /aeo
                  - generic [ref=e260]:
                    - generic [ref=e261]: AI Visibility
                    - generic [ref=e262]:
                      - generic [ref=e263]:
                        - img [ref=e264]
                        - text: 0%
                      - generic [ref=e267]: "0"
                - link "Search Console 0% 0" [ref=e269] [cursor=pointer]:
                  - /url: /gsc
                  - generic [ref=e270]:
                    - generic [ref=e271]: Search Console
                    - generic [ref=e272]:
                      - generic [ref=e273]:
                        - img [ref=e274]
                        - text: 0%
                      - generic [ref=e277]: "0"
                - link "Google Ads 0% 0" [ref=e279] [cursor=pointer]:
                  - /url: /ads
                  - generic [ref=e280]:
                    - generic [ref=e281]: Google Ads
                    - generic [ref=e282]:
                      - generic [ref=e283]:
                        - img [ref=e284]
                        - text: 0%
                      - generic [ref=e287]: "0"
            - generic [ref=e289]:
              - paragraph [ref=e290]: Refreshes every 24 hours
              - link "View full report" [ref=e291] [cursor=pointer]:
                - /url: /insights
                - text: View full report
                - img [ref=e292]
          - generic [ref=e294]:
            - link "% NaN Total Keywords tracked positions" [ref=e295] [cursor=pointer]:
              - /url: /seo
              - generic [ref=e297]:
                - generic [ref=e298]:
                  - img [ref=e300]
                  - generic [ref=e303]:
                    - img [ref=e304]
                    - text: "%"
                - paragraph [ref=e307]: NaN
                - paragraph [ref=e308]: Total Keywords
                - paragraph [ref=e309]: tracked positions
                - img [ref=e311]
            - link "% NaN AI Mentions across LLMs" [ref=e313] [cursor=pointer]:
              - /url: /aeo
              - generic [ref=e315]:
                - generic [ref=e316]:
                  - img [ref=e318]
                  - generic [ref=e321]:
                    - img [ref=e322]
                    - text: "%"
                - paragraph [ref=e325]: NaN
                - paragraph [ref=e326]: AI Mentions
                - paragraph [ref=e327]: across LLMs
                - img [ref=e329]
            - link "% NaN GSC Impressions last 28 days" [ref=e331] [cursor=pointer]:
              - /url: /gsc
              - generic [ref=e333]:
                - generic [ref=e334]:
                  - img [ref=e336]
                  - generic [ref=e337]:
                    - img [ref=e338]
                    - text: "%"
                - paragraph [ref=e341]: NaN
                - paragraph [ref=e342]: GSC Impressions
                - paragraph [ref=e343]: last 28 days
                - img [ref=e345]
            - link "0% $0 Ad Spend this month" [ref=e347] [cursor=pointer]:
              - /url: /ads
              - generic [ref=e349]:
                - generic [ref=e350]:
                  - img [ref=e352]
                  - generic [ref=e354]:
                    - img [ref=e355]
                    - text: 0%
                - paragraph [ref=e358]: $0
                - paragraph [ref=e359]: Ad Spend
                - paragraph [ref=e360]: this month
                - img [ref=e362]
        - generic [ref=e364]:
          - generic [ref=e366]:
            - generic [ref=e367]:
              - generic [ref=e368]:
                - img [ref=e370]
                - generic [ref=e371]:
                  - heading "Channel Performance" [level=3] [ref=e372]
                  - paragraph [ref=e373]: This week vs. last week
              - generic [ref=e374]:
                - button "7d" [ref=e375] [cursor=pointer]
                - button "14d" [ref=e376] [cursor=pointer]
                - button "30d" [ref=e377] [cursor=pointer]
            - generic [ref=e381]:
              - img [ref=e382]
              - list [ref=e387]:
                - listitem [ref=e388]:
                  - img [ref=e389]
                  - text: This Week
                - listitem [ref=e391]:
                  - img [ref=e392]
                  - text: Last Week
            - generic [ref=e394]:
              - generic [ref=e397]: This week
              - generic [ref=e400]: Last week
              - generic [ref=e401]:
                - img [ref=e402]
                - text: +8.3% overall
          - generic [ref=e406]:
            - generic [ref=e407]:
              - generic [ref=e408]:
                - heading "Activity" [level=3] [ref=e409]
                - paragraph [ref=e410]: Recent changes & events
              - button "View all" [ref=e411] [cursor=pointer]:
                - text: View all
                - img [ref=e412]
            - paragraph [ref=e416]: Showing last 0 events
        - generic [ref=e419]:
          - generic [ref=e420]:
            - heading "Top Insights" [level=3] [ref=e421]
            - paragraph [ref=e422]: AI-powered recommendations for your brand
          - link "View all" [ref=e423] [cursor=pointer]:
            - /url: /insights
            - text: View all
            - img [ref=e424]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('SEO Scan Pipeline', () => {
  4  |   const getUniqueEmail = () => `seo-test-${Math.random().toString(36).substring(7)}@example.com`;
  5  |   const password = 'TestPassword123!';
  6  |   const randomId = Math.random().toString(36).substring(7);
  7  |   const brandName = `Test Brand ${randomId}`;
  8  |   const domain = `test-${randomId}.com`;
  9  | 
  10 |   test.beforeEach(async ({ page }) => {
  11 |     const email = getUniqueEmail();
  12 |     // Register
  13 |     await page.goto('/register');
  14 |     await page.getByPlaceholder('Jane Smith').fill('SEO Tester');
  15 |     await page.getByPlaceholder('you@company.com').fill(email);
  16 |     await page.getByPlaceholder('Min. 8 characters').fill(password);
  17 |     await page.getByPlaceholder('Repeat your password').fill(password);
  18 |     await page.click('button[type="submit"]');
  19 |     
  20 |     await expect(page).toHaveURL(/.*dashboard|.*\//, { timeout: 15000 });
  21 |   });
  22 | 
  23 |   test('should create a project and run a scan', async ({ page }) => {
  24 |     test.setTimeout(120000);
  25 |     // Should see empty state if no projects
  26 |     await expect(page.getByText(/Your Dashboard is Waiting/i)).toBeVisible({ timeout: 15000 });
  27 |     
  28 |     // Click "Add a project" - in this UI we click the project selector first
  29 |     await page.click('button:has-text("No Project")');
  30 |     await page.click('button:has-text("Add new project")');
  31 |     
  32 |     // Fill Project Modal
  33 |     await page.fill('input[placeholder="e.g. Acme Corp"]', brandName);
  34 |     await page.fill('input[placeholder="e.g. acme.com"]', domain);
  35 |     await page.click('button:has-text("Create Project")');
  36 |     
  37 |     // Should now show project dashboard
  38 |     await expect(page.getByText(brandName)).toBeVisible({ timeout: 10000 });
  39 |     
  40 |     // Run Scan
  41 |     await page.click('button:has-text("Refresh")');
  42 |     
  43 |     // Scan Queued Modal pops up
  44 |     await expect(page.getByText(/Scan Queued/i)).toBeVisible({ timeout: 10000 });
  45 |     await page.click('button:has-text("OK")');
  46 |     
  47 |     // Wait for "Scan Complete" alert - using 2 minute timeout
  48 |     // We search for "Scan Complete" title
> 49 |     await expect(page.getByText('Scan Complete')).toBeVisible({ timeout: 120000 });
     |                                                   ^ Error: expect(locator).toBeVisible() failed
  50 |     
  51 |     // Verify the success message
  52 |     await expect(page.getByText(/completed successfully/i)).toBeVisible();
  53 |     
  54 |     // Click OK on completion alert
  55 |     await page.click('button:has-text("OK")');
  56 |     
  57 |     // Verify results - visibility score should be visible on dashboard
  58 |     await expect(page.getByText(/Visibility Score/i)).toBeVisible({ timeout: 10000 });
  59 |   });
  60 | });
  61 | 
```