"""
Clanker API client — programmatic access to Clanker/Clank.fun token data.

The Bitget ClankerScreener (https://web3.bitget.com/clankerscreener/) uses the same
data source. This client wraps the official public API so agents and scripts can
screen trending tokens, lookup by contract, or search by creator without scraping.

API docs: https://clanker.gitbook.io/clanker-documentation/public

Usage:
    from src.tools.clanker import clanker_tokens, clanker_search_creator

    # Trending tokens (market cap, 24h volume, etc.)
    data = clanker_tokens(sort_by="market-cap", limit=20, include_market=True)

    # Lookup by contract address
    data = clanker_tokens(q="0x525358b364b9bb38227054affdc37cecdd516b81", include_market=True)

    # Tokens by Farcaster creator
    data = clanker_search_creator(q="dish", limit=20)
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_TOKENS = "https://www.clanker.world/api/tokens"
BASE_SEARCH_CREATOR = "https://clanker.world/api/search-creator"

# Default timeout for external API
DEFAULT_TIMEOUT = 15.0


def clanker_tokens(
    q: Optional[str] = None,
    fid: Optional[int] = None,
    fids: Optional[str] = None,
    pair_address: Optional[str] = None,
    sort: str = "desc",
    sort_by: Optional[str] = None,
    social_interface: Optional[str] = None,
    limit: int = 10,
    cursor: Optional[str] = None,
    include_user: bool = False,
    include_market: bool = False,
    start_date: Optional[int] = None,
    chain_id: Optional[int] = None,
    champagne: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    Get paginated list of Clanker tokens (trending, search, or filtered).

    sort_by: "market-cap" | "tx-h24" | "price-percent-h24" | "price-percent-h1" | "deployed-at"
    social_interface: e.g. "clanker.world", "Bankr", "Moltx"
    chain_id: e.g. 8453 for Base
    """
    params: dict[str, Any] = {
        "sort": sort,
        "limit": min(limit, 20),
    }
    if q is not None:
        params["q"] = q
    if fid is not None:
        params["fid"] = fid
    if fids is not None:
        params["fids"] = fids
    if pair_address is not None:
        params["pairAddress"] = pair_address
    if sort_by is not None:
        params["sortBy"] = sort_by
    if social_interface is not None:
        params["socialInterface"] = social_interface
    if cursor is not None:
        params["cursor"] = cursor
    if include_user:
        params["includeUser"] = "true"
    if include_market:
        params["includeMarket"] = "true"
    if start_date is not None:
        params["startDate"] = start_date
    if chain_id is not None:
        params["chainId"] = chain_id
    if champagne:
        params["champagne"] = "true"

    try:
        r = httpx.get(BASE_TOKENS, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        logger.warning("Clanker tokens API error: %s", e)
        return {"data": [], "total": 0, "cursor": None, "tokensDeployed": 0, "error": str(e)}


def clanker_search_creator(
    q: str,
    limit: int = 20,
    offset: int = 0,
    sort: str = "desc",
    trusted_only: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    Get tokens by creator: Farcaster username or wallet address (0x...).
    """
    params: dict[str, Any] = {
        "q": q,
        "limit": min(limit, 50),
        "offset": offset,
        "sort": sort,
    }
    if trusted_only:
        params["trustedOnly"] = "true"

    try:
        r = httpx.get(BASE_SEARCH_CREATOR, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        logger.warning("Clanker search-creator API error: %s", e)
        return {"tokens": [], "total": 0, "hasMore": False, "error": str(e)}


def trending_tokens(
    limit: int = 20,
    sort_by: str = "market-cap",
    chain_id: int = 8453,
    include_market: bool = True,
) -> dict[str, Any]:
    """
    Convenience: fetch trending Clanker tokens (screener-style).
    Matches typical Bitget ClankerScreener "Trending" view.
    """
    return clanker_tokens(
        sort_by=sort_by,
        sort="desc",
        limit=limit,
        chain_id=chain_id,
        include_market=include_market,
    )


# Screener tab equivalents: All | Bankr | Moltx
SCREENER_PROVIDERS: dict[str, Optional[str]] = {
    "All": None,
    "Bankr": "Bankr",
    "Moltx": "Moltx",
}


def screener_views(
    provider: str = "All",
    sort_by: str = "market-cap",
    limit: int = 20,
    chain_id: int = 8453,
    include_market: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    Same logical views as Bitget ClankerScreener tabs (All / Bankr / Moltx)
    with configurable sort. Use for replicating the screener in code.

    provider: "All" | "Bankr" | "Moltx"
    sort_by: "market-cap" | "tx-h24" | "price-percent-h24" | "price-percent-h1" | "deployed-at"
    """
    social_interface = SCREENER_PROVIDERS.get(provider) if provider else None
    return clanker_tokens(
        sort_by=sort_by,
        sort="desc",
        limit=limit,
        chain_id=chain_id,
        include_market=include_market,
        social_interface=social_interface,
        timeout=timeout,
    )


def alpha_candidates(
    sort_by: str = "tx-h24",
    limit: int = 30,
    provider: str = "All",
    chain_id: int = 8453,
    min_volume_24h: Optional[float] = None,
    exclude_warnings: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    Fetch tokens tuned for alpha: sort by activity or movers, optional
    min 24h volume filter and exclusion of tokens with API warnings.

    sort_by: "tx-h24" (momentum), "market-cap", "price-percent-h24", "price-percent-h1", "deployed-at"
    min_volume_24h: if set, only tokens with related.market.volume24h >= this (float).
    exclude_warnings: if True, strip tokens that have non-empty warnings[].
    """
    # Fetch in batches of 20 (API max) until we have enough after filters
    social_interface = SCREENER_PROVIDERS.get(provider) if provider else None
    collected: list[dict[str, Any]] = []
    cursor: Optional[str] = None
    need = limit

    while need > 0:
        batch = clanker_tokens(
            sort_by=sort_by,
            sort="desc",
            limit=min(20, need * 2),
            chain_id=chain_id,
            include_market=True,
            social_interface=social_interface,
            cursor=cursor,
            timeout=timeout,
        )
        if batch.get("error"):
            break
        data = batch.get("data") or []
        cursor = batch.get("cursor")
        for t in data:
            if exclude_warnings and (t.get("warnings") or []):
                continue
            if min_volume_24h is not None:
                vol = (t.get("related") or {}).get("market") or {}
                if (vol.get("volume24h") or 0) < min_volume_24h:
                    continue
            collected.append(t)
            need -= 1
            if need <= 0:
                break
        if not data or not cursor:
            break

    return {
        "data": collected[:limit],
        "total": len(collected),
        "sort_by": sort_by,
        "provider": provider,
        "filters": {"min_volume_24h": min_volume_24h, "exclude_warnings": exclude_warnings},
    }
