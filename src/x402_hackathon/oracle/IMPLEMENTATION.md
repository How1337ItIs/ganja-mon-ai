# X402 Oracle Endpoints Implementation

## Overview

4 paid FastAPI routes using X402Verifier for payment verification, integrated into the main FastAPI app.

## Files Created/Modified

### Created: `src/x402_hackathon/oracle/endpoints.py`

FastAPI router with 5 endpoints:
- `GET /api/x402/oracle` — Premium oracle ($0.15, 5min cache)
- `GET /api/x402/grow-alpha` — Grow alpha signals ($0.05, 3min cache)
- `GET /api/x402/daily-vibes` — Daily vibes/wisdom ($0.02, 10min cache)
- `GET /api/x402/sensor-snapshot` — Raw sensor data ($0.005, 30s cache)
- `GET /api/x402/pricing` — Free pricing info (no payment)

### Modified: `src/api/app.py`

Added router registration after ops_router (line ~551):

```python
# Register x402 Oracle paid endpoints
try:
    from src.x402_hackathon.oracle.endpoints import router as x402_oracle_router
    app.include_router(x402_oracle_router)
except ImportError:
    pass  # x402_hackathon not deployed yet
```

## Architecture

### Payment Flow

1. **No payment header** → 402 Payment Required with `Accept-Payment` header
2. **Payment header present** → verify via `X402Verifier.verify_header()`
3. **Invalid payment** → 402 with verification failure reason
4. **Valid payment** → synthesize response + record payment + return 200

### Helper Functions

#### `_get_verifier_for_tier(tier_name: str) -> X402Verifier`
Creates X402Verifier instance with tier-specific pricing.

#### `_build_402_response(tier_name: str) -> JSONResponse`
Returns 402 status with Accept-Payment header containing:
- Payment requirements from verifier
- Tier info (name, description)
- Pricing URL

#### `_record_payment(tier_name: str, amount_usd: float, payer: str = "")`
Records payment in TWO places:

1. **ProfitSplitter** — Creates + executes batch for 60/25/10/5 allocation:
   ```python
   splitter = get_profit_splitter()
   batch = splitter.create_batch(amount_usd, f"x402-oracle-{tier_name}")
   splitter.execute_batch(batch)
   ```

2. **A2A Stats** (`data/a2a_stats.json`) — Updates:
   - `total_received_usd` — running total
   - `oracle_consultations` — total count
   - `oracle_{tier_name}_count` — per-tier count
   - `last_oracle_payment` — timestamp
   - `last_payer` — payer identifier

#### `_verify_and_serve(request, tier_name, synthesize_fn)`
Common verification + synthesis flow:

1. Get payment header (`PAYMENT-SIGNATURE` or `X-402-Payment`)
2. DEV_MODE bypass if enabled and no payment
3. No payment → return 402
4. Verify payment via tier-specific verifier
5. Invalid → return 402 with reason
6. Valid → call synthesize_fn(), add metadata, record payment, return 200

### Dev Mode

Set `X402_DEV_MODE=true` to bypass payment verification:
- Requests without payment headers will succeed
- Responses include `_dev_mode: true` flag
- No payment recording occurs

## Integration Points

### Dependencies

- `src.a2a.x402.X402Verifier` — Payment verification
- `src.payments.splitter.get_profit_splitter()` — Profit allocation
- `src.x402_hackathon.oracle.pricing` — Tier configuration
- `src.x402_hackathon.oracle.synthesis` — Oracle synthesis functions

### Data Files

- `data/payment_ledger.json` — ProfitSplitter records (60/25/10/5 batches)
- `data/a2a_stats.json` — Oracle payment stats and counters

### Environment Variables

- `X402_DEV_MODE` — Bypass payment verification (default: false)
- `A2A_PAYMENT_CHAIN` — Payment chain (default: base)
- `BASE_WALLET_ADDRESS` — Payment recipient address
- `MONAD_WALLET_ADDRESS` — Fallback payment address

## Response Format

### Paid Endpoints (200 OK after verification)

```json
{
  // Synthesis function output
  "narrative": "...",
  "signal": "...",
  "confidence": 0.75,
  // Payment metadata (added by _verify_and_serve)
  "payment_verified": true,
  "payment_usd": 0.15,
  "timestamp": 1707777777.0
}
```

### Payment Required (402)

```json
{
  "error": "Payment required",
  "tier": "premium",
  "price_usd": 0.15,
  "message": "This endpoint requires $0.15 USDC payment on Base"
}
```

Headers:
```
Accept-Payment: {
  "version": "x402-v1",
  "priceUSD": "0.15",
  "currency": "USDC",
  "network": "base",
  "chainId": 8453,
  "payTo": "eip155:8453:0x...",
  "tier": "premium",
  "description": "Full 5-domain AI synthesis in Rasta patois (Grok AI)",
  "pricingUrl": "https://grokandmon.com/.well-known/x402-pricing.json"
}
```

### Pricing Endpoint (free, no payment)

```json
{
  "version": "x402-oracle-v1",
  "agent": "GanjaMon",
  "agent_id": 4,
  "chain": "base",
  "currency": "USDC",
  "tiers": {
    "premium": {
      "price_usd": 0.15,
      "endpoint": "/api/x402/oracle",
      "description": "Full 5-domain AI synthesis in Rasta patois (Grok AI)",
      "cache_ttl_seconds": 300
    },
    // ... other tiers
  }
}
```

## Testing

### Import Test
```bash
python3 -c "from src.x402_hackathon.oracle.endpoints import router; print(f'Routes: {len(router.routes)}')"
```

### Dev Mode Test
```bash
export X402_DEV_MODE=true
curl http://localhost:8000/api/x402/oracle
# Should return synthesis without payment
```

### Payment Test
```bash
# Get requirements
curl -i http://localhost:8000/api/x402/oracle
# Extract Accept-Payment header and create payment proof
# Send request with PAYMENT-SIGNATURE header
```

## Deployment

### Chromebook Deployment

1. **Deploy to Chromebook:**
   ```bash
   ./deploy.sh --restart
   ```

2. **Verify routes:**
   ```bash
   curl https://grokandmon.com/api/x402/pricing
   ```

3. **Check logs:**
   ```bash
   ssh natha@chromebook.lan "journalctl --user -u grokmon -n 50"
   ```

### Environment Setup

Ensure these are set in Chromebook `.env`:
```bash
X402_DEV_MODE=false  # Enable payments in production
A2A_PAYMENT_CHAIN=base
BASE_WALLET_ADDRESS=0x734B0e337bfa7d4764f4B806B4245Dd312DdF134
```

## Security Considerations

1. **Payment verification tiers** (from X402Verifier):
   - ECDSA signature recovery (strongest)
   - On-chain tx hash lookup
   - Facilitator receipt
   - Honor system fallback

2. **Payment recording** is non-blocking:
   - Failures in ProfitSplitter or stats update don't fail the request
   - Warnings logged but request succeeds

3. **Dev mode** should NEVER be enabled in production:
   - Check `X402_DEV_MODE` before deploying
   - Responses include `_dev_mode: true` flag for transparency

4. **Payment headers** support both names:
   - `PAYMENT-SIGNATURE` (canonical)
   - `X-402-Payment` (fallback)

## Future Improvements

1. **Rate limiting** per payer address
2. **Payment caching** to prevent double-charging on retry
3. **Payer reputation** tracking (successful payments → trust score boost)
4. **Tiered response quality** (partial results for partial payments)
5. **Subscription model** (flat fee for N requests per period)

## Stats

- **4 paid endpoints** at $0.005 to $0.15 per request
- **5 total routes** (including free pricing endpoint)
- **2 data sinks** (ProfitSplitter + A2A stats)
- **60/25/10/5 allocation** on all oracle revenue
