#!/usr/bin/env python3
"""
LFJ Token Mill Volume Report: MON vs Booly
Queries Monad RPC for Swap events from Token Mill MARKET contracts (bonding curve).
Swaps go through the Token Mill market contract, NOT the token contracts directly.
Each token has one market contract; we query that contract's Swap(address,...) logs.
Computes volume by period: first 2 days MON, week after, KOTM epoch.
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Add project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Contracts (Monad mainnet)
# IMPORTANT: Swaps go through the Token Mill MARKET contract (bonding curve), not the token.
# Query eth_getLogs on the market address for Swap(...) events.
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"  # MON's Token Mill market (bonding curve)
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"   # MON token (https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b)
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"  # Booly token (https://lfj.gg/monad/trade/0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d)
TM_FACTORY = "0xe70d21aD211DB6DCD3f54B9804A1b64BB21b17B1"  # Token Mill Factory Proxy (Monad); getMarketOf(token) -> market address. Source: LFJ Token Mill Deployment Addresses.
RPC_URL = os.getenv("MONAD_RPC_URL", "https://rpc.monad.xyz")

# Swap(address indexed sender, address indexed recipient, int256 deltaBaseAmount, int256 deltaQuoteAmount, (uint256,uint256,uint256,uint256) fees)
# topic0 = keccak256("Swap(address,address,int256,int256,(uint256,uint256,uint256,uint256))")
# Precomputed: 0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f
SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

BLOCKS_PER_DAY = 216_000  # ~0.4s block time
GETLOGS_BLOCK_RANGE = 100  # Monad public RPC limit


async def rpc(method: str, params: list) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            RPC_URL,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
        )
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data.get("result")


async def get_block_number() -> int:
    r = await rpc("eth_blockNumber", [])
    return int(r, 16)


async def get_block_timestamp(block_hex: str) -> int:
    b = await rpc("eth_getBlockByNumber", [block_hex, False])
    if not b:
        return 0
    return int(b["timestamp"], 16)


def _get_market_of_selector() -> str:
    """First 4 bytes of keccak256('getMarketOf(address)') for TMFactory.getMarketOf(token)."""
    try:
        from web3 import Web3
        return "0x" + Web3.keccak(text="getMarketOf(address)").hex()[:8]
    except Exception:
        # Precomputed: getMarketOf(address) = 0x6ca51cd0
        return "0x6ca51cd0"


async def get_market_of(token_address: str) -> str | None:
    """Get Token Mill market address for a token via TMFactory.getMarketOf(token). Returns None if not found."""
    addr = token_address.lower().replace("0x", "")
    if len(addr) != 40:
        return None
    token = ("0" * 24) + addr  # left-pad address to 32 bytes (64 hex) for ABI
    selector = _get_market_of_selector()
    if not selector.startswith("0x"):
        selector = "0x" + selector
    data = selector + token
    try:
        result = await rpc("eth_call", [{"to": TM_FACTORY, "data": data}, "latest"])
        if not result or result == "0x":
            return None
        # Return is 32-byte word; address is last 20 bytes (40 hex chars)
        if len(result) >= 66:
            addr = "0x" + result[-40:].lower()
            if addr == "0x" + "0" * 40:
                return None
            return addr
        return None
    except Exception as e:
        print(f"getMarketOf({token_address}) error: {e}", file=sys.stderr)
        return None


async def get_logs(address: str, from_block: int, to_block: int) -> list:
    """Fetch Swap logs from a Token Mill MARKET contract (not token). 100-block chunks (RPC limit)."""
    logs = []
    # Limit range per call
    step = GETLOGS_BLOCK_RANGE
    total_chunks = (to_block - from_block + 1 + step - 1) // step
    chunk = 0
    for start in range(from_block, to_block + 1, step):
        end = min(start + step - 1, to_block)
        chunk += 1
        if total_chunks >= 50 and chunk % 500 == 0:
            print(f"  getLogs progress: {chunk}/{total_chunks} chunks, {len(logs)} logs so far...", file=sys.stderr)
        try:
            batch = await rpc(
                "eth_getLogs",
                [{
                    "address": address,
                    "fromBlock": hex(start),
                    "toBlock": hex(end),
                    "topics": [SWAP_TOPIC],
                }],
            )
            logs.extend(batch or [])
            await asyncio.sleep(0.05)  # rate limit (reduce if RPC allows)
        except Exception as e:
            print(f"getLogs {start}-{end} error: {e}", file=sys.stderr)
    return logs


def parse_swap_log(log: dict) -> dict:
    """Decode Swap event. data = deltaBaseAmount (32) + deltaQuoteAmount (32) + fees (4*32)."""
    data = log.get("data", "0x")
    if data == "0x" or len(data) < 2 + 64 * 2:
        return {}
    # first two int256 in data
    delta_base = int(data[2:2+64], 16)
    if delta_base >= 2**255:
        delta_base -= 2**256
    delta_quote = int(data[2+64:2+128], 16)
    if delta_quote >= 2**255:
        delta_quote -= 2**256
    # Quote volume = abs(deltaQuoteAmount) when buying (quote in); for sell it's the quote value of base
    # For volume we sum quote token amount: buy = deltaQuoteAmount (positive in), sell = need quote equiv.
    # Simple: volume in quote = abs(delta_quote) for buys (quote->base), and for sells we use delta_base * price or same as quote received. Actually swap: deltaQuoteAmount is the change in quote reserve. So for a buy (quote in): deltaQuoteAmount is negative (quote leaves user). So abs(deltaQuoteAmount) = quote amount in = volume. For sell: deltaBaseAmount negative, deltaQuoteAmount positive = quote in. So volume_quote = abs(delta_quote) for both (quote side of trade).
    volume_quote = abs(delta_quote)
    block = int(log.get("blockNumber", "0x0"), 16)
    return {
        "blockNumber": block,
        "deltaBase": delta_base,
        "deltaQuote": delta_quote,
        "volumeQuote": volume_quote,
        "txHash": log.get("transactionHash", ""),
    }


async def main():
    now_block = await get_block_number()
    now_ts = await get_block_timestamp(hex(now_block))
    print(f"Current block: {now_block}, timestamp: {now_ts}")

    # Epoch: last Thursday 4 AM PST to this Thursday 4 AM PST
    # Jan 23 2026 12:00 UTC -> Jan 29 2026 12:00 UTC
    epoch_end_ts = int(datetime(2026, 1, 29, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    epoch_start_ts = int(datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    # MON launch: pairCreatedAt 1769042927 (Jan 20 2026 ~20:48 UTC)
    mon_launch_ts = 1769042927
    mon_first_2d_end_ts = mon_launch_ts + 2 * 86400

    # Approximate block numbers (block time ~0.4s)
    # block = now_block - (now_ts - ts) / 0.4
    def ts_to_block(ts: int) -> int:
        return now_block - int((now_ts - ts) / 0.4)

    epoch_start_block = ts_to_block(epoch_start_ts)
    epoch_end_block = ts_to_block(epoch_end_ts)
    mon_launch_block = ts_to_block(mon_launch_ts)
    mon_2d_end_block = ts_to_block(mon_first_2d_end_ts)
    # 9 days ago
    nine_days_ago_block = now_block - 9 * BLOCKS_PER_DAY

    # CLI: --test N (last N blocks), --epoch-only, --days N, --first-2d (MON launch +2d), or full 9 days
    args = sys.argv[1:]
    test_blocks = None
    epoch_only = "--epoch-only" in args
    first_2d = "--first-2d" in args
    days_arg = None
    for i, a in enumerate(args):
        if a == "--days" and i + 1 < len(args):
            try:
                days_arg = int(args[i + 1])
            except ValueError:
                pass
            break

    if "--test" in args and args.index("--test") + 1 < len(args):
        try:
            test_blocks = int(args[args.index("--test") + 1])
        except (ValueError, IndexError):
            pass
    if test_blocks is not None:
        from_block = max(nine_days_ago_block, now_block - test_blocks)
        to_block = now_block
        print(f"[TEST] Fetching last {test_blocks} blocks: {from_block} - {to_block}")
    elif first_2d:
        from_block = mon_launch_block
        to_block = mon_2d_end_block
        print(f"[FIRST 2 DAYS MON] Fetching blocks: {from_block} - {to_block} (~{(to_block - from_block) // BLOCKS_PER_DAY} days)")
    elif epoch_only:
        from_block = max(epoch_start_block, nine_days_ago_block)
        to_block = min(epoch_end_block, now_block)
        print(f"[EPOCH ONLY] Fetching epoch blocks: {from_block} - {to_block} (~{(to_block - from_block) // BLOCKS_PER_DAY} days)")
    elif days_arg is not None and days_arg > 0:
        from_block = now_block - days_arg * BLOCKS_PER_DAY
        to_block = now_block
        print(f"[LAST {days_arg} DAYS] Fetching blocks: {from_block} - {to_block}")
    else:
        from_block = nine_days_ago_block
        to_block = now_block

    print(f"Epoch blocks: {epoch_start_block} - {epoch_end_block}")
    print(f"MON launch block ~{mon_launch_block}, first 2d end ~{mon_2d_end_block}")
    print(f"Fetching MON market Swap logs from block {from_block} to {to_block}...")

    logs = await get_logs(MON_MARKET, from_block, to_block)
    print(f"MON market: {len(logs)} Swap events")

    swaps = [parse_swap_log(log) for log in logs]
    swaps = [s for s in swaps if s]

    def volume_in_range(from_b: int, to_b: int) -> float:
        total = 0
        for s in swaps:
            if from_b <= s["blockNumber"] <= to_b:
                total += s["volumeQuote"]
        return total / 1e18  # 18 decimals for quote (WMON/MON)

    mon_vol_first_2d = volume_in_range(mon_launch_block, mon_2d_end_block)
    mon_vol_week_after = volume_in_range(mon_2d_end_block, epoch_end_block)
    mon_vol_epoch = volume_in_range(epoch_start_block, epoch_end_block)
    mon_vol_9d = volume_in_range(nine_days_ago_block, now_block)

    print("\n--- MON (Token Mill market) ---")
    print(f"  First 2 days (launch to +2d): {mon_vol_first_2d:,.2f} MON")
    print(f"  Week after (+2d to epoch end): {mon_vol_week_after:,.2f} MON")
    print(f"  KOTM epoch (Jan 23 4AM PST - Jan 29 4AM PST): {mon_vol_epoch:,.2f} MON")
    print(f"  Last 9 days total: {mon_vol_9d:,.2f} MON")

    # Booly: resolve market via TMFactory.getMarketOf(BOOLY_TOKEN), then fetch Swap logs from market
    booly_market = await get_market_of(BOOLY_TOKEN)
    booly_vol_epoch = 0.0
    booly_vol_9d = 0.0
    booly_swap_count = 0
    if booly_market:
        print(f"\nBooly market: {booly_market} (from getMarketOf({BOOLY_TOKEN}))")
        print(f"Fetching Booly market Swap logs from block {from_block} to {to_block}...")
        booly_logs = await get_logs(booly_market, from_block, to_block)
        booly_swaps = [parse_swap_log(log) for log in booly_logs]
        booly_swaps = [s for s in booly_swaps if s]
        booly_swap_count = len(booly_swaps)

        def booly_volume_in_range(from_b: int, to_b: int) -> float:
            total = 0
            for s in booly_swaps:
                if from_b <= s["blockNumber"] <= to_b:
                    total += s["volumeQuote"]
            return total / 1e18

        booly_vol_epoch = booly_volume_in_range(epoch_start_block, epoch_end_block)
        booly_vol_9d = booly_volume_in_range(nine_days_ago_block, now_block)
        print("\n--- Booly (Token Mill market) ---")
        print(f"  KOTM epoch: {booly_vol_epoch:,.2f} MON")
        print(f"  Last 9 days total: {booly_vol_9d:,.2f} MON")
        print(f"  Swap count (9d): {booly_swap_count}")
    else:
        print(f"\nBooly market not found for token {BOOLY_TOKEN} (getMarketOf returned none)")

    # Output for report
    out = {
        "mon": {
            "market": MON_MARKET,
            "token": MON_TOKEN,
            "volume_first_2_days_mon": mon_vol_first_2d,
            "volume_week_after_mon": mon_vol_week_after,
            "volume_epoch_mon": mon_vol_epoch,
            "volume_9d_mon": mon_vol_9d,
            "swap_count_9d": len(swaps),
        },
        "booly": {
            "token": BOOLY_TOKEN,
            "market": booly_market,
            "volume_epoch_mon": booly_vol_epoch,
            "volume_9d_mon": booly_vol_9d,
            "swap_count_9d": booly_swap_count,
        },
        "epoch": {"start_ts": epoch_start_ts, "end_ts": epoch_end_ts},
    }
    report_path = ROOT / "docs" / "lfj_volume_report_data.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
