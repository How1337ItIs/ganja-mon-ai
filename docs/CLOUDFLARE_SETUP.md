# Cloudflare Setup Guide for Viral Traffic
## Grok & Mon - Scale to 100k+ users

This guide will configure Cloudflare to handle viral traffic spikes while keeping your Chromebook origin server happy.

---

## 📊 Current vs. Optimized Performance

| Metric | Before | After Cloudflare |
|--------|--------|------------------|
| Max concurrent users | 50 | 10,000+ |
| Origin requests/sec | 100% | 5% (95% cache hit) |
| Global latency | 500ms+ | 50ms (edge) |
| Crash point | 200 users | N/A (Cloudflare scales) |
| Monthly cost | $0 | $5-10 |

---

## 🚀 Quick Setup (30 minutes)

### Step 1: Cloudflare Page Rules (FREE)

1. Log in to Cloudflare Dashboard
2. Go to **Rules** → **Page Rules**
3. Create these rules (in order):

**Rule 1: Cache Static Assets**
```
URL: *grokandmon.com/assets/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 month
```

**Rule 2: Cache API Responses**
```
URL: *grokandmon.com/api/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 minute
  - Browser Cache TTL: 30 seconds
```

**Rule 3: Cache Homepage**
```
URL: grokandmon.com/
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 5 minutes
  - Browser Cache TTL: 1 minute
```

### Step 2: Enable Cloudflare Features

Go to **Speed** → **Optimization**:
- ✅ Auto Minify (JS, CSS, HTML)
- ✅ Brotli compression
- ✅ Early Hints
- ✅ Rocket Loader (optional - test first)

Go to **Caching** → **Configuration**:
- Cache Level: **Standard**
- Browser Cache TTL: **Respect Existing Headers**

Go to **Security** → **Bots**:
- ✅ Bot Fight Mode (blocks bad bots)

### Step 3: Rate Limiting (Prevents DDoS)

Go to **Security** → **WAF** → **Rate limiting rules**:

**Rule 1: API Rate Limit**
```
If: (http.request.uri.path contains "/api/")
Then: Rate limit
  - Requests: 100 per 1 minute
  - Action: Block for 1 minute
  - Apply to: Each IP address
```

**Rule 2: Webcam Rate Limit**
```
If: (http.request.uri.path eq "/api/webcam/latest")
Then: Rate limit
  - Requests: 30 per 1 minute
  - Action: Challenge (CAPTCHA)
  - Apply to: Each IP address
```

---

## ⚡ Advanced: Cloudflare Workers ($5/mo for 10M requests)

### Deploy Webcam Worker

This moves webcam serving to Cloudflare's edge network (instant worldwide).

**1. Install Wrangler CLI**
```bash
npm install -g wrangler
wrangler login
```

**2. Create Worker Project**
```bash
cd /mnt/c/Users/natha/sol-cannabis
wrangler deploy cloudflare-worker-webcam.js --name grokmon-webcam
```

**3. Create KV Namespace**
```bash
wrangler kv:namespace create WEBCAM_CACHE
# Copy the ID shown, e.g., "abc123..."
```

**4. Create `wrangler.toml`**
```toml
name = "grokmon-webcam"
main = "cloudflare-worker-webcam.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "WEBCAM_CACHE"
id = "YOUR_KV_ID_HERE"  # From step 3

[triggers]
crons = ["*/1 * * * *"]  # Every minute (Cloudflare limit)

[vars]
ORIGIN_URL = "http://YOUR_CHROMEBOOK_IP:8000"
```

**5. Deploy**
```bash
wrangler deploy
```

**6. Set up Route**

In Cloudflare Dashboard:
- Go to **Workers & Pages** → **Routes**
- Add route: `grokandmon.com/api/webcam/latest`
- Worker: `grokmon-webcam`

**Result:** Webcam requests now served from edge in <50ms globally!

### Deploy API Cache Worker

Same process for `cloudflare-worker-api.js`:

```bash
wrangler deploy cloudflare-worker-api.js --name grokmon-api

# Add routes for:
# - /api/sensors/latest
# - /api/ai/latest
# - /api/grow/stage
# - /api/devices/latest
# - /api/stats
```

---

## 🛡️ Emergency Traffic Protection

### If site is getting hammered RIGHT NOW:

**1. Enable "Under Attack Mode"** (Cloudflare Dashboard → Overview)
- Shows 5-second CAPTCHA to all visitors
- Stops DDoS cold

**2. Disable Development Mode**
- Ensures caching is active

**3. SSH to Chromebook and check load:**
```bash
ssh natha@chromebook.lan "htop"
# If CPU >80%: Enable Under Attack Mode
# If RAM >90%: Restart service
```

**4. Check what's being requested:**
```bash
ssh natha@chromebook.lan "journalctl --user -u grokmon -n 100 --no-pager | grep 'HTTP/1.1'"
# Look for suspicious patterns (same IP spamming endpoints)
```

---

## 📈 Monitoring Setup (FREE)

### UptimeRobot (5-minute checks)

1. Sign up: https://uptimerobot.com
2. Add monitors:
   - **HTTP(s)**: `https://grokandmon.com/api/health`
   - Alert if down for 5 minutes
   - Alert if response time >5 seconds

3. Set up alerts:
   - Email: your-email@example.com
   - Webhook: Discord/Slack (optional)

### Cloudflare Analytics (Built-in)

Check **Analytics** → **Traffic** for:
- Requests/hour (watch for spikes)
- Cache hit ratio (should be >80%)
- Bandwidth saved
- Top countries/paths

---

## 🧪 Testing Your Setup

### 1. Verify Caching Works

```bash
# First request (should be MISS)
curl -I https://grokandmon.com/api/sensors/latest
# Look for: CF-Cache-Status: MISS

# Second request (should be HIT)
curl -I https://grokandmon.com/api/sensors/latest
# Look for: CF-Cache-Status: HIT
```

### 2. Load Test (Simulate Traffic)

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 1000 requests, 50 concurrent
ab -n 1000 -c 50 https://grokandmon.com/

# Watch for:
# - Requests per second (should be >500/sec with caching)
# - Failed requests: 0
# - Time per request: <200ms
```

### 3. Check Origin Load

```bash
ssh natha@chromebook.lan "htop"
# CPU should stay <50% even during load test
```

---

## 💰 Cost Estimate

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Cloudflare Page Rules** | 3 rules | $20/mo for 50 rules |
| **Cloudflare Workers** | 100k req/day | $5/mo for 10M req/mo |
| **Cloudflare KV** | 100k reads/day | Included in Workers |
| **UptimeRobot** | 50 monitors | $7/mo for 500 ms checks |

**Total for 100k users/day:** $5-10/mo

---

## 🎯 Quick Wins Checklist

Before going viral, verify:

- [ ] Cloudflare DNS is active (orange cloud)
- [ ] Page Rules created (3 rules)
- [ ] Cache hit ratio >70% (check Analytics)
- [ ] Rate limiting enabled
- [ ] UptimeRobot monitoring active
- [ ] Environment variables set (ADMIN_PASSWORD, JWT_SECRET_KEY)
- [ ] Bot Fight Mode enabled
- [ ] SSL/TLS mode: Full (strict)

Optional but recommended:
- [ ] Cloudflare Workers deployed (webcam + API)
- [ ] Argo Smart Routing enabled ($5/mo)
- [ ] Load testing completed (ab test passed)

---

## 🆘 Troubleshooting

### Cache Hit Ratio Low (<50%)

**Cause:** Page Rules not configured correctly

**Fix:**
1. Check Page Rules order (most specific first)
2. Verify "Cache Everything" is set
3. Check origin `Cache-Control` headers aren't saying `no-cache`

### Origin Still Getting Hammered

**Cause:** Cloudflare not proxying requests

**Fix:**
1. Check DNS records have orange cloud (proxied)
2. Verify SSL/TLS mode is Full or Full (strict)
3. Enable Development Mode OFF in dashboard

### Worker Not Caching

**Cause:** KV namespace not bound or cron not running

**Fix:**
```bash
# Check worker logs
wrangler tail grokmon-webcam

# Manually trigger cron
wrangler dev cloudflare-worker-webcam.js --local
```

### 522 Errors (Origin Unreachable)

**Cause:** Chromebook offline or firewall blocking Cloudflare IPs

**Fix:**
1. Check Chromebook is on and connected: `ping chromebook.lan`
2. Verify port 8000 is open
3. Check service running: `systemctl --user status grokmon`

---

## 📚 Additional Resources

- [Cloudflare Page Rules](https://developers.cloudflare.com/rules/page-rules/)
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Rate Limiting Guide](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- [Cache Rules](https://developers.cloudflare.com/cache/)

---

**Questions?** Check production logs:
```bash
ssh natha@chromebook.lan "journalctl --user -u grokmon -f"
```
