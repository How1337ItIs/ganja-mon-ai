# ClankerScreener — Full Documentation

**Bitget ClankerScreener (UI):** https://web3.bitget.com/clankerscreener/

This doc covers everything about the ClankerScreener: what it is, how it works, the APIs it uses, response shapes, warnings, and how to replicate or extend it in code (including alpha patterns).

---

## 1. Overview

- **What it is:** A Bitget-hosted web UI for browsing and searching Clanker/Clank.fun tokens (Base chain meme coins launched via Clanker).
- **Data source:** The screener is a **frontend only**. It calls the **official Clanker public API**; there is **no Bitget-specific API** for the screener.
- **Programmatic access:** Use `GET https://www.clanker.world/api/tokens` and `GET https://clanker.world/api/search-creator` (same data the UI uses).
- **Official API docs:** [Clanker Documentation – Public API](https://clanker.gitbook.io/clanker-documentation/public).

---

## 2. How the ClankerScreener UI works

The page is a thin client: each user action maps to one or more requests to the Clanker tokens API with different query parameters.

### 2.1 Tabs (All / Bankr / Moltx)

| Tab    | API behavior |
|--------|----------------|
| **All**  | No `socialInterface`. Full token set (typically with `chainId=8453` for Base). |
| **Bankr**| `socialInterface=Bankr` — tokens launched via the Bankr interface only. |
| **Moltx**| `socialInterface=Moltx` — tokens launched via Moltx (index may return 0 until Moltx is fully indexed). |

### 2.2 “Trending Tokens” table

The table is the tokens endpoint with:

- `includeMarket=true` (so market cap, 24h change, etc. are shown).
- A **sort** chosen by the UI (equivalent to `sortBy` + `sort=desc`):

| sortBy value         | Meaning |
|----------------------|--------|
| `market-cap`         | Largest market cap (default “top” view). |
| `tx-h24`             | Most 24h trading activity (tx count + volume). Best for **momentum**. |
| `price-percent-h24`  | Biggest 24h % price move. Often low-cap / low volume. |
| `price-percent-h1`   | Biggest 1h % move. Noisy; can surface pumps. |
| `deployed-at`        | Newest deploys (default when no sortBy). |

### 2.3 Search box

- **Contract address or name/symbol** → same tokens endpoint with `q=<query>`.
- No separate search API; search is a parameter on the same list endpoint.
- “Token not found” in the UI means the API returned no results for that `q`.

### 2.4 Token detail (modal / panel)

- When you click a token or paste a contract, the UI shows: symbol, name, creator, creator rewards claimed, fees claimed, holders, created time, market cap, claimers table, claimed records.
- **Creator / claimers / fees** data may come from the same API (with `includeUser=true` for creator) or from additional Clanker/Bitget endpoints not documented here; the **list and search** behavior is fully covered by the public tokens + search-creator APIs below.

---

## 3. Tokens API (list, trending, search)

**Endpoint:** `GET https://www.clanker.world/api/tokens`

This is the main API the screener uses for the table and for search.

### 3.1 Query parameters (full list)

| Parameter         | Type    | Default   | Description |
|-------------------|---------|-----------|-------------|
| `q`               | string  | —         | Search: token name, symbol, or contract address. Case-insensitive. |
| `fid`             | number  | —         | Filter by a single Farcaster user ID (e.g. `12345`). |
| `fids`            | string  | —         | Filter by multiple FIDs, comma-separated (e.g. `123,456,789`). |
| `pairAddress`     | string  | —         | Filter by paired token contract address. |
| `sort`            | string  | `desc`    | Sort order: `asc` (oldest first) or `desc` (newest/highest first). |
| `sortBy`          | string  | —         | Sort field: `market-cap`, `tx-h24`, `price-percent-h24`, `price-percent-h1`, `deployed-at`. |
| `socialInterface`  | string  | —         | Filter by launch interface: e.g. `clanker.world`, `Bankr`, `Moltx`. |
| `limit`           | number  | 10        | Number of results (max **20**). |
| `cursor`          | string  | —         | Pagination cursor from the previous response. |
| `includeUser`     | boolean | false     | Include creator profile (avatar, name, bio, etc.) in `related.user`. |
| `includeMarket`   | boolean | false     | Include market data in `related.market` (cap, volume, % changes). |
| `startDate`       | number  | —         | Filter: tokens created after this Unix timestamp. |
| `chainId`         | number  | —         | Filter by chain; e.g. `8453` for Base. |
| `champagne`       | boolean | false     | When true, only “champagne” tokens. |

### 3.2 Response shape

```json
{
  "data": [ { /* token object */ } ],
  "total": 12345,
  "cursor": "eyJ...",
  "tokensDeployed": 1
}
```

- **data:** Array of token objects (see below).
- **total:** Total number of tokens matching the query.
- **cursor:** Opaque cursor for the next page; send as `cursor` in the next request.
- **tokensDeployed:** When filtering by creator (`fid`/`fids`), total tokens deployed by that creator.

### 3.3 Token object (fields)

Base fields (always present when the token is in the list):

| Field               | Type   | Description |
|---------------------|--------|-------------|
| `id`                | number | Internal ID. |
| `created_at`        | string | ISO timestamp. |
| `last_indexed`      | string | Last index time. |
| `tx_hash`           | string | Deployment transaction hash. |
| `contract_address`  | string | Token contract address. |
| `name`              | string | Token name. |
| `symbol`            | string | Token symbol. |
| `description`       | string | Token description. |
| `supply`            | string | Total supply (raw). |
| `img_url`           | string | Logo/image URL. |
| `pool_address`      | string | Uniswap pool address. |
| `type`              | string | e.g. `clanker_v4`, `clanker_v3_1`. |
| `pair`              | string | Quote token, e.g. `WETH`, `DEGEN`. |
| `chain_id`         | number | e.g. 8453 (Base). |
| `deployed_at`       | string | Deployment time. |
| `msg_sender`        | string | Deployer address. |
| `factory_address`   | string | Clanker factory contract. |
| `locker_address`    | string | LP locker contract. |
| `position_id`       | string | Position ID. |
| `warnings`          | array | Risk tags (see Warnings below). |
| `metadata`          | object | Extra metadata (e.g. social links). |
| `pool_config`       | object | Pool config (paired token, tick, etc.). |
| `starting_market_cap` | —    | When available. |
| `tags`              | array | Tags. |
| `extensions`        | object | Fees, vault, airdrop, etc. |
| `admin`             | string | Admin address. |
| `socialLinks`       | —      | Social links. |

When `includeUser=true`, each token can have:

- **related.user:** Creator profile (avatar, name, bio, etc.).

When `includeMarket=true`, each token has:

- **related.market:** Object with:
  - `marketCap` (number)
  - `volume24h` (number)
  - `priceChangePercent1h`, `priceChangePercent6h`, `priceChangePercent24h` (numbers)

### 3.4 Pagination

- Use `limit` (max 20) and `cursor`.
- Next page: same params, add `cursor` from the previous response.
- When there is no next page, `cursor` may be null or omitted.

---

## 4. Search-creator API (tokens by creator)

**Endpoint:** `GET https://clanker.world/api/search-creator`

Used to find tokens by Farcaster username or wallet address (not the main screener table, but useful for alpha and research).

### 4.1 Query parameters

| Parameter     | Type    | Required | Default | Description |
|---------------|---------|----------|---------|-------------|
| `q`           | string  | Yes      | —       | Farcaster username (e.g. `dish`) or wallet address (0x...). |
| `limit`       | integer | No       | 20      | Results per page (1–50). |
| `offset`      | integer | No       | 0       | Pagination offset. |
| `sort`        | string  | No       | `desc`  | `asc` (oldest first) or `desc` (newest first). |
| `trustedOnly` | boolean | No       | false   | When true, only verified/trusted tokens. |

### 4.2 Response shape

```json
{
  "tokens": [ { /* token with trustStatus */ } ],
  "user": { "fid", "username", "displayName", "pfpUrl", "verifiedAddresses" },
  "searchedAddress": "0x...",
  "total": 42,
  "hasMore": true
}
```

- **tokens:** Array of token objects (with creator/trust context).
- **user:** Farcaster user info if found.
- **searchedAddress:** Wallet address used for the search (if applicable).
- **total:** Total count matching the query.
- **hasMore:** Whether more pages exist (use `offset` for next page).

### 4.3 Trust status (per token)

Each token can include a **trustStatus** object:

| Field                  | Type    | Description |
|------------------------|---------|-------------|
| `isTrustedDeployer`   | boolean | Deployed by a known trusted deployer. |
| `isTrustedClanker`    | boolean | Token contract is on the allowlist. |
| `fidMatchesDeployer` | boolean | Creator’s Farcaster verified address matches deployer. |
| `verifiedAddresses`  | array   | Creator’s verified addresses. |

Trust priority (highest first): allowlisted → trusted deployer → FID verified → unverified.

---

## 5. Warnings (risk tags)

From [Clanker.world Warning Tags](https://clanker.gitbook.io/clanker-documentation/general/clanker.world-warning-tags): tokens can have a `warnings` array. These are also exposed via the API.

| Tag                   | Meaning |
|-----------------------|--------|
| **UNUSUAL_TICK**      | Initial price/market cap doesn’t match expected thresholds. Possible misconfiguration. |
| **UNUSUAL_PAIR_ADDRESS** | Quote token not in the supported list. Liquidity may be non-standard. |
| **MISSING_POOL_CONFIG**  | Pool config missing (legacy or indexing issue). |
| **UNUSUAL_POSITIONS**  | LP positions don’t match standard configurations. |

Use these to filter or flag tokens when building alpha or risk filters.

---

## 6. In-repo client (`src.tools.clanker`)

The repo provides a small client that mirrors the screener’s behavior and adds alpha helpers.

### 6.1 Functions

| Function | Purpose |
|----------|---------|
| **clanker_tokens(...)** | Raw tokens API: all params (q, fid, sortBy, socialInterface, limit, cursor, includeMarket, etc.). |
| **clanker_search_creator(q, ...)** | Search-creator API: by username or 0x address. |
| **trending_tokens(limit, sort_by, chain_id)** | Convenience: trending list with `includeMarket=true`. |
| **screener_views(provider, sort_by, limit, ...)** | Replicate screener tabs: provider = `"All"` \| `"Bankr"` \| `"Moltx"` and any sortBy. |
| **alpha_candidates(sort_by, limit, min_volume_24h, exclude_warnings, ...)** | Alpha-oriented list: sort by activity/movers, optional min 24h volume and exclusion of tokens with warnings. |

### 6.2 Constants

- **SCREENER_PROVIDERS:** `{"All": None, "Bankr": "Bankr", "Moltx": "Moltx"}` — used by `screener_views`.

### 6.3 Example usage

```python
from src.tools.clanker import (
    clanker_tokens,
    clanker_search_creator,
    trending_tokens,
    screener_views,
    alpha_candidates,
)

# Trending (screener-style)
data = trending_tokens(limit=20, sort_by="market-cap")

# Same as Bitget tabs + sort
data = screener_views(provider="All", sort_by="tx-h24", limit=20)
data = screener_views(provider="Bankr", sort_by="market-cap", limit=20)

# Alpha: momentum, min volume, no warnings
data = alpha_candidates(
    sort_by="tx-h24",
    limit=30,
    min_volume_24h=1000.0,
    exclude_warnings=True,
)

# Search by contract or name/symbol
data = clanker_tokens(q="0x...", include_market=True)

# By Farcaster username or wallet
data = clanker_search_creator(q="dish", limit=20)
```

---

## 7. Borrowing patterns for Clanker alpha

Patterns you can reuse (same primitives as the screener):

1. **Trending by activity** — `sortBy=tx-h24&sort=desc&includeMarket=true&chainId=8453` for momentum.
2. **Trending by market cap** — `sortBy=market-cap&sort=desc`; then filter by `volume24h` for liquidity.
3. **Movers** — `sortBy=price-percent-h24` or `price-percent-h1`; filter by `volume24h` / `marketCap` to avoid no-volume pumps.
4. **Interface-specific** — `socialInterface=Bankr` (or Moltx when available).
5. **Creator / FID** — `fid=` or `fids=` on tokens API, or search-creator with `q=username`; use `includeMarket=true` and sort for best performers.
6. **Recency** — `sortBy=deployed-at&sort=desc`; optionally `startDate=<unix>`.
7. **Risk filter** — Drop or flag tokens with non-empty `warnings`.
8. **Pagination** — `limit=20` and `cursor` to walk top N (e.g. top 100 by tx-h24).

---

## 8. Quick reference (curl)

```bash
# Trending by market cap (Base)
curl "https://www.clanker.world/api/tokens?sortBy=market-cap&sort=desc&limit=20&includeMarket=true&chainId=8453"

# Trending by 24h activity
curl "https://www.clanker.world/api/tokens?sortBy=tx-h24&sort=desc&limit=20&includeMarket=true&chainId=8453"

# Bankr only
curl "https://www.clanker.world/api/tokens?socialInterface=Bankr&limit=20&includeMarket=true"

# Search by contract
curl "https://www.clanker.world/api/tokens?q=0x525358b364b9bb38227054affdc37cecdd516b81&includeMarket=true"

# Tokens by creator (username or 0x)
curl "https://clanker.world/api/search-creator?q=dish&limit=20"
```

---

## 9. Other data sources

- **Bitquery:** For raw on-chain Clanker activity (e.g. latest TokenCreated events, by deployer), see [Base Clanker API](https://docs.bitquery.io/docs/examples/Base/base-clanker-api/). Requires Bitquery API key; use when you need event-level chain data rather than the indexed Clanker API.
- **Clanker docs:** [Quick Start](https://clanker.gitbook.io/clanker-documentation/quick-start), [Deployed Contracts](https://clanker.gitbook.io/clanker-documentation/references/deployed-contracts), [Supported Quote Tokens](https://clanker.gitbook.io/clanker-documentation/references/supported-quote-tokens).

---

## 10. Summary table

| Topic | Detail |
|-------|--------|
| **Screener URL** | https://web3.bitget.com/clankerscreener/ |
| **List / search API** | `GET https://www.clanker.world/api/tokens` |
| **Creator API** | `GET https://clanker.world/api/search-creator` |
| **Tabs** | All (no socialInterface), Bankr, Moltx |
| **Sort options** | market-cap, tx-h24, price-percent-h24, price-percent-h1, deployed-at |
| **Max list limit** | 20 per request; paginate with cursor |
| **Market fields** | marketCap, volume24h, priceChangePercent1h/6h/24h (with includeMarket=true) |
| **Risk** | Token `warnings[]`: UNUSUAL_TICK, UNUSUAL_PAIR_ADDRESS, MISSING_POOL_CONFIG, UNUSUAL_POSITIONS |
| **Repo client** | `src.tools.clanker`: clanker_tokens, clanker_search_creator, trending_tokens, screener_views, alpha_candidates |
