# Bridge & Discovery Efficiency — $MON Monad ↔ Base

How to make bridging and discovery as efficient as possible so the Monad ↔ Base market is more efficient (tighter spreads, faster arbitrage, more volume).

---

## 1. Bridging efficiency

### Current bottleneck

- **Manual redemption:** User must paste VAA and click "Redeem on Base" ~15–20 min after initiating. Slow and easy to forget.
- **Wormhole attestation:** ~15–20 min is fixed by Guardians; we can’t shorten that, but we can **automate the redeem step**.

### A. Automatic relaying (when available)

- **Wormhole Executor on Monad:** When Wormhole deploys the Executor to Monad mainnet, transfers can auto-complete. No contract changes needed; users pay relay fee on Monad and the Executor service redeems on Base.
- **Action:** Watch [Wormhole docs](https://docs.wormhole.com) / Monad deployments; once Executor is live on Monad, enable or document the automatic flow.

### B. Your own relayer (high impact, today)

- Run a small **relayer service** that:
  1. Watches Wormhole for outbound NTT messages (Monad → Base) for your NTT Manager.
  2. Fetches the VAA once attested.
  3. Submits `receiveMessage(vaa)` on Base (you pay Base gas or user pre-pays).
- **Effect:** Users only do **one step** (initiate on Monad); ~15–20 min later MON appears on Base without them pasting a VAA.
- **Options:** Use Wormhole’s relayer SDK, or a simple indexer + script that calls Base transceiver. Relayer can be permissioned (only for your NTT) or open.

### C. UX improvements (no backend required)

- **Bridge UI:** Already have `src/web/bridge.html`. Add:
  - “Track transfer” after initiate: input tx hash, poll Wormholescan for VAA, show “Copy VAA” / “Redeem” when ready.
  - Clear copy: “Step 1: Initiate (Monad). Step 2: Wait 15–20 min. Step 3: Redeem (Base) — paste VAA below or use relayer when available.”
- **One-click approve:** Remember or suggest max approval so repeat users don’t approve every time.
- **Link from main site:** grokandmon.com → “Bridge $MON” → bridge UI or aggregator.

### D. NTT pool (Monad) liquidity

- Keep enough **MON in the Monad NTT Manager** so that Base → Monad unlocks never fail. Monitor pool balance; top up if you expect large flows back to Monad.

---

## 2. Discovery efficiency

The easier it is for people and bots to **find** MON and **see both markets**, the more efficient the combined market.

### A. Price & pair discovery

| Where | What to do |
|-------|------------|
| **DexScreener** | Once the Aerodrome pool exists, DexScreener usually picks it up. Add Base contract `0x9e0753d8855dcc69F1BdFEfbAEf995e1aedBaD8e`; ensure Monad pair is already listed. |
| **CoinGecko / CMC** | When applying or updating, submit **multi-chain**: Monad (primary) + Base. Same token, two chains; they can show price on both and “Markets” tabs per chain. |
| **Token lists** | Submit MON logo (and symbol/name) to [SmolDapp/tokenAssets](https://github.com/SmolDapp/tokenAssets) so Aerodrome and other UIs show the correct icon. |

### B. Bridge & swap aggregators

- **Goal:** So that “Get MON on Base” or “Bridge MON” appears in Li.Fi, Bungee, Jumper, Socket, etc.
- **Requirements (typical):**
  - Token exists on both chains (you have that).
  - Liquidity on both sides (Monad: Token Mill/v1; Base: Aerodrome).
  - Contract addresses and chain IDs documented and stable.
- **Actions:**
  1. **Document once:** One page (e.g. on repo or grokandmon.com) with:
     - Monad: chain ID 143, MON `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`
     - Base: chain ID 8453, MON `0x9e0753d8855dcc69F1BdFEfbAEf995e1aedBaD8e`
     - Bridge: Wormhole NTT (and link to your bridge UI or relayer when live).
  2. **Apply / request:** Use each aggregator’s “request token” or “add bridge route” process; point them to that page and to the pools.
  3. **Wormhole ecosystem:** If Wormhole has a token/bridge directory or partner form, register MON (Monad ↔ Base) so their front-ends can suggest the route.

### C. Website and in-app discovery

- **grokandmon.com:** Clear CTAs:
  - “Buy on Monad” → LFJ Token Mill (or DexScreener Monad).
  - “Buy on Base” → Aerodrome pool (or DexScreener Base once live).
  - “Bridge MON” → `src/web/bridge.html` or aggregator that supports MON.
- **Single “Get MON” page:** One page that detects chain and shows “Buy here” or “Bridge from Monad” / “Bridge from Base” with one click where possible.

---

## 3. Market efficiency (tighter spreads, more arb)

- **Arbitrage:** Tighter spreads need arbitrageurs to buy on the cheap chain and sell on the expensive one. That requires:
  - **Visibility:** Both markets visible (DexScreener, CoinGecko, aggregators) so bots and humans see both prices.
  - **Bridge speed and cost:** Faster/cheaper redeem (relayer or Executor) and low gas on both chains make arb more profitable and faster.
  - **Liquidity:** Deeper liquidity on both sides reduces slippage so arb size can be meaningful.
- **Optional — arb bot / docs:** Publish a minimal “MON cross-chain arb” note: contract addresses, NTT flow, and that you welcome bots. Some teams open-source a simple arb bot; even just clear docs can encourage third-party bots and keep the spread tight.

---

## 4. Priority checklist

| Priority | Action | Impact |
|----------|--------|--------|
| High | Run a **relayer** that auto-redeems VAAs on Base after attestation | One-step bridge; no VAA paste |
| High | **Document** MON on both chains (addresses, chain IDs, bridge) and **submit to aggregators** (Li.Fi, Bungee, Jumper, etc.) | Discovery; “Get MON on Base” in apps |
| High | **Token list / logo** (SmolDapp, etc.) so Base UIs show MON correctly | Trust and discovery |
| Medium | **Bridge UI:** add “track tx → fetch VAA → Redeem” or link to relayer | Fewer abandoned transfers |
| Medium | **CoinGecko/CMC:** list MON as multi-chain (Monad + Base) | One place to see both prices |
| Medium | **Website:** Buy Monad / Buy Base / Bridge links + “Get MON” flow | Direct discovery |
| Later | When **Wormhole Executor** is on Monad, use automatic relaying | Zero manual redeem |
| Optional | **NTT pool** monitoring + top-up; **arb bot** or public arb docs | Smooth unlocks; tighter spreads |

---

## Summary

- **Bridging:** Automate the redeem step (relayer or Executor) so users only initiate on Monad; keep NTT pool funded on Monad.
- **Discovery:** List MON on both chains everywhere (DexScreener, CoinGecko/CMC, token lists), and get MON into bridge/swap aggregators so “Bridge MON” / “Get MON on Base” appears in one click.
- **Market:** More visibility + faster/cheaper bridge + enough liquidity on both sides keeps spreads tight and the combined Monad–Base market efficient.
