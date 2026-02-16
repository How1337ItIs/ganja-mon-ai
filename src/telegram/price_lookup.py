"""Real-time crypto price lookups for the Telegram bot.

Uses DexScreener API (free, no auth) and CoinGecko for price data.
Gives the bot ability to answer "what's the price of X?" questions.
"""

import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Cache prices for 60 seconds to avoid API spam
_price_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 60

# Known token addresses for quick lookup
KNOWN_TOKENS = {
    "$mon": {
        "address": "0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b",
        "chain": "monad",
        "name": "Ganja Mon",
    },
    "$wmon": {
        "address": "0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A",
        "chain": "monad",
        "name": "Wrapped MON",
    },
    "$eth": {"coingecko_id": "ethereum", "name": "Ethereum"},
    "$btc": {"coingecko_id": "bitcoin", "name": "Bitcoin"},
    "$sol": {"coingecko_id": "solana", "name": "Solana"},
}


async def lookup_dexscreener(address: str) -> dict | None:
    """Look up token info on DexScreener by contract address."""
    cache_key = f"dex:{address}"
    now = time.time()
    if cache_key in _price_cache:
        ts, data = _price_cache[cache_key]
        if now - ts < CACHE_TTL:
            return data

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            )
            if resp.status_code == 200:
                data = resp.json()
                pairs = data.get("pairs", [])
                if pairs:
                    # Use the highest liquidity pair
                    best = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
                    result = {
                        "name": best.get("baseToken", {}).get("name", "Unknown"),
                        "symbol": best.get("baseToken", {}).get("symbol", "?"),
                        "price_usd": best.get("priceUsd", "0"),
                        "price_change_24h": best.get("priceChange", {}).get("h24", 0),
                        "volume_24h": best.get("volume", {}).get("h24", 0),
                        "liquidity_usd": best.get("liquidity", {}).get("usd", 0),
                        "chain": best.get("chainId", "unknown"),
                        "dex": best.get("dexId", "unknown"),
                        "pair_url": best.get("url", ""),
                        "fdv": best.get("fdv", 0),
                        "market_cap": best.get("marketCap", 0),
                    }
                    _price_cache[cache_key] = (now, result)
                    return result
    except Exception as e:
        logger.warning(f"DexScreener lookup failed: {e}")
    return None


async def lookup_coingecko(coin_id: str) -> dict | None:
    """Look up token price on CoinGecko (for major tokens)."""
    cache_key = f"cg:{coin_id}"
    now = time.time()
    if cache_key in _price_cache:
        ts, data = _price_cache[cache_key]
        if now - ts < CACHE_TTL:
            return data

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                if coin_id in data:
                    info = data[coin_id]
                    result = {
                        "name": coin_id.replace("-", " ").title(),
                        "symbol": coin_id[:4].upper(),
                        "price_usd": str(info.get("usd", 0)),
                        "price_change_24h": info.get("usd_24h_change", 0),
                        "volume_24h": info.get("usd_24h_vol", 0),
                        "market_cap": info.get("usd_market_cap", 0),
                    }
                    _price_cache[cache_key] = (now, result)
                    return result
    except Exception as e:
        logger.warning(f"CoinGecko lookup failed: {e}")
    return None


async def search_dexscreener(query: str) -> dict | None:
    """Search DexScreener by token name/symbol."""
    cache_key = f"search:{query.lower()}"
    now = time.time()
    if cache_key in _price_cache:
        ts, data = _price_cache[cache_key]
        if now - ts < CACHE_TTL:
            return data

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.dexscreener.com/latest/dex/search",
                params={"q": query},
            )
            if resp.status_code == 200:
                data = resp.json()
                pairs = data.get("pairs", [])
                if pairs:
                    # Pick highest liquidity result
                    best = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
                    result = {
                        "name": best.get("baseToken", {}).get("name", "Unknown"),
                        "symbol": best.get("baseToken", {}).get("symbol", "?"),
                        "price_usd": best.get("priceUsd", "0"),
                        "price_change_24h": best.get("priceChange", {}).get("h24", 0),
                        "volume_24h": best.get("volume", {}).get("h24", 0),
                        "liquidity_usd": best.get("liquidity", {}).get("usd", 0),
                        "chain": best.get("chainId", "unknown"),
                        "dex": best.get("dexId", "unknown"),
                        "pair_url": best.get("url", ""),
                        "fdv": best.get("fdv", 0),
                        "market_cap": best.get("marketCap", 0),
                        "address": best.get("baseToken", {}).get("address", ""),
                    }
                    _price_cache[cache_key] = (now, result)
                    return result
    except Exception as e:
        logger.warning(f"DexScreener search failed: {e}")
    return None


async def get_price(query: str) -> dict | None:
    """Universal price lookup - handles addresses, symbols, and names.

    Tries in order:
    1. Known tokens table
    2. Contract address (DexScreener)
    3. CoinGecko (major tokens)
    4. DexScreener search
    """
    query = query.strip().lower()

    # Strip $ prefix for matching
    query_clean = query.lstrip("$")

    # Check known tokens
    for key, info in KNOWN_TOKENS.items():
        if query_clean in key.lstrip("$") or query_clean == info.get("name", "").lower():
            if "address" in info:
                return await lookup_dexscreener(info["address"])
            elif "coingecko_id" in info:
                return await lookup_coingecko(info["coingecko_id"])

    # Contract address
    if re.match(r'^0x[a-fA-F0-9]{8,40}$', query):
        return await lookup_dexscreener(query)

    # Major tokens via CoinGecko
    major_map = {
        "btc": "bitcoin", "bitcoin": "bitcoin",
        "eth": "ethereum", "ethereum": "ethereum",
        "sol": "solana", "solana": "solana",
        "bnb": "binancecoin", "avax": "avalanche-2",
        "matic": "matic-network", "pol": "matic-network",
        "doge": "dogecoin", "shib": "shiba-inu",
        "link": "chainlink", "uni": "uniswap",
        "aave": "aave", "arb": "arbitrum",
    }
    if query_clean in major_map:
        return await lookup_coingecko(major_map[query_clean])

    # Fall back to DexScreener search
    return await search_dexscreener(query_clean)


def format_price_response(data: dict) -> str:
    """Format price data for Telegram display."""
    if not data:
        return "Can't find dat token, bredren. Check di name or give me di contract address."

    name = data.get("name", "Unknown")
    symbol = data.get("symbol", "?")
    price = data.get("price_usd", "0")
    change = data.get("price_change_24h", 0)
    volume = data.get("volume_24h", 0)
    mcap = data.get("market_cap", 0)
    liq = data.get("liquidity_usd", 0)
    chain = data.get("chain", "")

    # Format price (handle very small numbers)
    try:
        price_f = float(price)
        if price_f < 0.0001:
            price_str = f"${price_f:.8f}"
        elif price_f < 1:
            price_str = f"${price_f:.6f}"
        elif price_f < 100:
            price_str = f"${price_f:.4f}"
        else:
            price_str = f"${price_f:,.2f}"
    except (ValueError, TypeError):
        price_str = f"${price}"

    # Change direction
    try:
        change_f = float(change) if change else 0
        change_str = f"{change_f:+.1f}%"
    except (ValueError, TypeError):
        change_str = "N/A"

    parts = [f"**{name}** ({symbol})"]
    parts.append(f"Price: {price_str} ({change_str} 24h)")

    if volume:
        try:
            parts.append(f"Volume: ${float(volume):,.0f}")
        except (ValueError, TypeError):
            pass

    if mcap:
        try:
            parts.append(f"MCap: ${float(mcap):,.0f}")
        except (ValueError, TypeError):
            pass

    if liq:
        try:
            parts.append(f"Liquidity: ${float(liq):,.0f}")
        except (ValueError, TypeError):
            pass

    if chain:
        parts.append(f"Chain: {chain}")

    return "\n".join(parts)


def detect_price_query(text: str) -> str | None:
    """Detect if a message is asking about a price.

    Returns the token/query to look up, or None.
    """
    text_lower = text.lower()

    # Direct price commands
    patterns = [
        r"price (?:of )?([^\s?]+)",
        r"how much is ([^\s?]+)",
        r"what(?:'s| is) ([^\s?]+) (?:at|worth|price|trading)",
        r"([^\s]+) price\??",
        r"check ([^\s]+) price",
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            token = match.group(1).strip("?.,!")
            # Filter out non-token words
            if token in ("the", "a", "an", "it", "this", "that", "my"):
                continue
            return token

    # Check for contract addresses mentioned with price context
    if "price" in text_lower or "worth" in text_lower or "trading at" in text_lower:
        addr_match = re.search(r'0x[a-fA-F0-9]{8,40}', text)
        if addr_match:
            return addr_match.group(0)

    return None
