# AdTicks Web Spider - User Guide

**Quick Start Guide for Privacy-Safe Website Analysis**

---

## What is the Web Spider?

Instead of uploading sensitive server logs, AdTicks can now crawl your website directly to analyze how search bots see it. This approach:
- ✅ **Protects privacy** - No IPs, referers, or user data collected
- ✅ **Simulates real bots** - Tests how Googlebot, Bingbot, Yandex, etc. crawl your site
- ✅ **Detects orphan pages** - Finds pages not linked in your sitemap
- ✅ **Respects robots.txt** - Follows crawl rules and rate limits
- ✅ **Fast analysis** - Cached results in seconds

---

## How to Use

### 1. Start a Website Crawl

Go to your project and click **"Analyze Website"**:

```
Domain: https://example.com
Bot Type: Googlebot (default)
Max URLs: 500 (adjustable 10-5000)
Max Depth: 3 (adjustable 1-10)
```

The spider will:
- Crawl your website following links
- Simulate the selected bot's behavior
- Respect your robots.txt file
- Rate limit requests (2 per second by default)
- Cache results for 24 hours

### 2. View Crawl Results

Once the analysis completes (takes seconds to minutes), you'll see:

#### **Crawl Statistics**
- Total URLs crawled
- Bot user agent used
- Crawl duration
- Response time breakdown

#### **Status Code Distribution**
- 2xx (Success) - pages crawling normally
- 3xx (Redirects) - temporary or permanent redirects
- 4xx (Client Errors) - pages not found or blocked
- 5xx (Server Errors) - server issues

#### **Orphan Pages** (NEW!)
Two important insights:
1. **Crawled but not in sitemap** - Pages found by the crawler that aren't listed in sitemap.xml (might be internal, old URLs, or link islands)
2. **In sitemap but not crawled** - Pages in your sitemap that the crawler couldn't reach (robots.txt blocked, broken links, etc.)

#### **Detailed Results**
For each crawled URL, you'll see:
- HTTP status code
- Response time (ms)
- Redirects (if any)
- Bot detection (if applicable)

---

## Features Explained

### Bot Simulation
Select which bot to simulate:
- **Googlebot** (default) - Most common search engine
- **Bingbot** - Microsoft search engine
- **Yandexbot** - Russian search engine
- **DuckDuckBot** - Privacy-focused search
- **Baiduspider** - Chinese search engine
- **Applebot** - Apple Siri search
- **Facebookbot** - Social media crawler
- **AhrefsBot** - SEO tool crawler
- **SemrushBot** - SEO tool crawler

Each bot has unique crawl patterns, which affects what they discover on your site.

### Rate Limiting
The spider respects rate limits to avoid overloading your server:
- **Default:** 2 requests per second
- **Respects robots.txt** - If your robots.txt specifies `Crawl-delay: 5`, the spider waits 5 seconds between requests
- **No hammering** - Sequential requests, never concurrent

### Robots.txt Compliance
The spider:
- Fetches and parses your robots.txt file
- Skips URLs marked as `Disallow`
- Respects bot-specific rules like `User-agent: Googlebot`
- Falls back to wildcards (`User-agent: *`) if no specific rule exists

### Orphan Detection
Automatically discovers:
1. **Orphaned pages** - Crawled URLs not mentioned in your sitemap
2. **Missing pages** - URLs in sitemap that can't be reached
3. **Redirect chains** - Multiple redirects that might confuse bots

---

## Best Practices

### ✅ Do's

1. **Run crawls regularly** - Monthly analysis helps track crawlability changes
2. **Test different bots** - Compare how different search engines see your site
3. **Adjust depth based on site size** - Smaller sites: depth 2-3, Large sites: depth 2-4
4. **Monitor orphan pages** - Either link them or remove from sitemap
5. **Check for redirect chains** - Fix 301 → 302 → 200 patterns
6. **Review robots.txt blocks** - Ensure you're not accidentally blocking important content

### ❌ Don'ts

1. **Don't set max_urls too high** - Start with 500, increase only if needed
2. **Don't run multiple crawls simultaneously** - Space them out by a few minutes
3. **Don't crawl during peak traffic** - Run at off-peak hours if concerned about load
4. **Don't ignore robots.txt blocks** - They usually exist for a reason
5. **Don't rely solely on the spider** - Combine with GSC, log analysis, and real user monitoring

---

## Troubleshooting

### Crawl Returns Empty Results

**Problem:** No URLs were crawled.

**Causes:**
- Domain is down or unreachable
- All pages blocked by robots.txt
- SSL/TLS certificate issues
- Firewall blocking the request

**Solution:**
- Check if the domain is accessible from your browser
- Verify robots.txt isn't blocking all bots
- Check your firewall/WAF logs
- Try a different bot type

### All Pages Return 403 Errors

**Problem:** All crawled pages return HTTP 403 Forbidden.

**Causes:**
- Bot is blocked by firewall/WAF rules
- User-agent is being rejected
- IP is rate-limited or blocked

**Solution:**
- Check your WAF/firewall rules
- Whitelist common search bot IPs
- Verify the bot's User-Agent is recognized
- Contact hosting provider if blocked

### Sitemap Not Found

**Problem:** Spider can't find sitemap.xml for orphan detection.

**Causes:**
- Sitemap not at standard location (root)
- Robots.txt doesn't reference sitemap
- Sitemap is broken or malformed

**Solution:**
- Place sitemap at `/sitemap.xml`
- Add reference in robots.txt: `Sitemap: https://example.com/sitemap.xml`
- Validate sitemap at `https://example.com/sitemap.xml`
- Check XML formatting

### Crawl Takes Too Long

**Problem:** Analysis is slow or timing out.

**Causes:**
- Site is very large (millions of pages)
- Network is slow
- Too many redirects or errors
- Rate limiting is too aggressive

**Solution:**
- Reduce `max_urls` to 100-200
- Reduce `max_depth` to 2
- Check network connectivity
- Run during off-peak hours

---

## Comparison: Logs vs. Spider

| Feature | Raw Logs | Web Spider |
|---------|----------|-----------|
| **Privacy** | ❌ Exposes IPs, referers | ✅ No sensitive data |
| **Bot Coverage** | Limited to your actual traffic | ✅ Simulates 9+ major bots |
| **Orphan Detection** | ❌ Requires manual analysis | ✅ Automatic |
| **robots.txt** | ✅ Already in logs | ✅ Respects rules |
| **Setup** | Complex (log aggregation) | ✅ One URL entry |
| **Real traffic** | ✅ Actual bot behavior | ❌ Simulated only |
| **Frequency** | Limited (as traffic arrives) | ✅ On-demand |
| **Cost** | High (log storage) | ✅ Low (compute only) |

**Recommendation:** Use both! Use logs for real-world traffic analysis and the spider for testing coverage and orphan detection.

---

## API Reference

### Start Crawl Analysis

```bash
POST /api/seo/analyze-website
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

Query Parameters:
  project_id: UUID of your project
  website_url: https://example.com
  bot_name: googlebot (optional, default: googlebot)
  max_urls: 500 (optional, 10-5000)
  max_depth: 3 (optional, 1-10)

Response (202 Accepted):
{
  "status": "queued",
  "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "project_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "website_url": "https://example.com",
  "bot": "googlebot",
  "message": "Website crawl queued. Results will be available shortly."
}
```

### Retrieve Results

```bash
GET /api/seo/crawl-results/{project_id}
Authorization: Bearer YOUR_TOKEN

Query Parameters:
  skip: 0 (optional, pagination)
  limit: 100 (optional, max 500)

Response (200 OK):
{
  "project_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "summary": {
    "total_urls_crawled": 247,
    "bot_user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
    "crawl_time_seconds": 45,
    "status_distribution": {
      "2xx": 230,
      "3xx": 5,
      "4xx": 10,
      "5xx": 2
    }
  },
  "aggregated": [
    {
      "status_code": 200,
      "count": 230,
      "avg_response_time_ms": 125
    },
    ...
  ],
  "orphans": {
    "crawled_not_in_sitemap": [
      "https://example.com/old-blog/post-123",
      "https://example.com/admin/dashboard"
    ],
    "in_sitemap_not_crawled": [
      "https://example.com/deleted-page"
    ]
  },
  "total": 247,
  "skip": 0,
  "limit": 100
}
```

---

## FAQ

### Q: Is the spider as good as Google's crawl?
**A:** Not exactly, but close enough for testing. The spider follows links and robots.txt like Google does, but doesn't execute JavaScript or handle every edge case Google handles. For JavaScript-heavy sites, results may differ.

### Q: How often should I run crawls?
**A:** For most sites, monthly is good. High-traffic sites might benefit from weekly crawls. After major site changes, run immediately.

### Q: Can the spider crawl behind a login?
**A:** Not in the current version. It simulates public bot crawls. For authenticated areas, use the raw logs approach or export those areas.

### Q: Why are some pages not crawled?
**A:** Common reasons:
- Blocked by robots.txt
- No links to the page (orphaned)
- Page is JavaScript-only (not executed by spider)
- Page redirects to blocked URL
- SSL/TLS certificate issue

### Q: Can I use this instead of Google Search Console?
**A:** No, they're complementary:
- **GSC** - Real data from Google's crawl, actual search traffic
- **Spider** - Simulated crawl, useful for testing and debugging

Use both together for complete coverage.

### Q: What's the maximum crawl size?
**A:** Default 5000 URLs. For larger sites, run multiple crawls targeting different sections (`/products/*`, `/blog/*`, etc.).

### Q: How is data cached?
**A:** Crawl results are cached for 24 hours in Redis. After 24 hours, the cache expires and you can run a new crawl for fresh data.

---

## Support & Feedback

Found a bug or have suggestions?
- 📧 Email: support@adticks.com
- 💬 Chat: Live support in the dashboard
- 📋 Issues: Report at https://adticks.com/support

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-02  
**Status:** Production Ready ✅
