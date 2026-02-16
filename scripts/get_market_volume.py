#!/usr/bin/env python3
"""
Fast Token Mill Market Volume Calculator
Uses Monad RPC with optimized chunking to get Swap event volume.
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import httpx

# Market contracts (where swaps happen)
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"

RPC_URL = os.getenv("MONAD_RPC_URL") or (f"https://monad-mainnet.blockvision.org/v1/{os.getenv('BLOCKVISION_API_KEY', '')}" if os.getenv("BLOCKVISION_API_KEY") else "https://rpc.monad.xyz")

# Swap event topic
SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

# Monad ~0.4s blocks = 216000 blocks/day
BLOCKS_PER_DAY = 216_000

# Try larger chunks first, fall back if needed
BLOCK_CHUNK_SIZES = [10000, 5000, 2000, 1000, 500, 100]


async def rpc(method: str, params: list, client: httpx.AsyncClient) -> dict | None:
    try:
        r = await client.post(
            RPC_URL,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            # Check if it's a block range error
            error_msg = str(data.get("error", {}))
            if "range" in error_msg.lower() or "limit" in error_msg.lower():
                return {"range_error": True}
            print(f"  RPC error: {data['error']}", file=sys.stderr)
            return None
        return data.get("result")
    except Exception as e:
        print(f"  RPC exception: {e}", file=sys.stderr)
        return None


async def get_block_number(client: httpx.AsyncClient) -> int:
    r = await rpc("eth_blockNumber", [], client)
    return int(r, 16) if r else 0


async def get_logs_adaptive(
    address: str, 
    from_block: int, 
    to_block: int, 
    client: httpx.AsyncClient,
    chunk_size: int = 10000
) -> list:
    """Get logs with adaptive chunk sizing."""
    all_logs = []
    current_from = from_block
    current_chunk = chunk_size
    
    total_blocks = to_block - from_block
    processed = 0
    
    while current_from <= to_block:
        current_to = min(current_from + current_chunk - 1, to_block)
        
        result = await rpc(
            "eth_getLogs",
            [{
                "address": address,
                "fromBlock": hex(current_from),
                "toBlock": hex(current_to),
                "topics": [SWAP_TOPIC],
            }],
            client,
        )
        
        if result is None:
            # Error, try smaller chunk
            if current_chunk > 100:
                current_chunk = current_chunk // 2
                continue
            else:
                # Skip this range
                current_from = current_to + 1
                continue
        
        if isinstance(result, dict) and result.get("range_error"):
            # Range too big, reduce chunk size
            if current_chunk > 100:
                current_chunk = current_chunk // 2
                continue
            else:
                current_from = current_to + 1
                continue
        
        all_logs.extend(result)
        processed = current_from - from_block
        pct = (processed / total_blocks) * 100 if total_blocks > 0 else 100
        print(f"\r  Progress: {pct:.1f}% ({len(all_logs)} swaps found)", end="", flush=True)
        
        current_from = current_to + 1
        await asyncio.sleep(0.05)  # Small rate limit
    
    print()  # Newline after progress
    return all_logs


def parse_swap_log(log: dict) -> dict:
    """Parse Swap event to extract volume."""
    data = log.get("data", "0x")
    if data == "0x" or len(data) < 2 + 64 * 2:
        return {}
    
    # deltaBaseAmount (32 bytes) + deltaQuoteAmount (32 bytes) + fees
    delta_base = int(data[2:2+64], 16)
    if delta_base >= 2**255:
        delta_base -= 2**256
    
    delta_quote = int(data[2+64:2+128], 16)
    if delta_quote >= 2**255:
        delta_quote -= 2**256
    
    # Volume = abs(deltaQuoteAmount) - this is the quote token amount in the swap
    volume_quote = abs(delta_quote)
    block = int(log.get("blockNumber", "0x0"), 16)
    
    return {
        "block": block,
        "volume_quote_wei": volume_quote,
        "tx": log.get("transactionHash", ""),
    }


async def get_market_volume(market_address: str, name: str, client: httpx.AsyncClient):
    """Get volume data for a market contract."""
    now_block = await get_block_number(client)
    print(f"\n{'='*60}")
    print(f"Analyzing {name} Market: {market_address}")
    print(f"Current block: {now_block}")
    
    # Define time periods
    # Epoch 1: Jan 21-23 (reset)
    # Epoch 2: Jan 23-29 (4 AM PST = 12:00 UTC)
    epoch1_start_ts = int(datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    epoch1_end_ts = int(datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    epoch2_start_ts = epoch1_end_ts
    epoch2_end_ts = int(datetime(2026, 1, 29, 12, 0, 0, tzinfo=timezone.utc).timestamp())
    
    # Get current timestamp from RPC
    block_result = await rpc("eth_getBlockByNumber", [hex(now_block), False], client)
    now_ts = int(block_result.get("timestamp", "0x0"), 16) if block_result else 0
    
    # Convert timestamps to blocks
    def ts_to_block(ts: int) -> int:
        return max(0, now_block - int((now_ts - ts) / 0.4))
    
    epoch1_start_block = ts_to_block(epoch1_start_ts)
    epoch1_end_block = ts_to_block(epoch1_end_ts)
    epoch2_start_block = ts_to_block(epoch2_start_ts)
    epoch2_end_block = ts_to_block(epoch2_end_ts)
    
    print(f"Epoch 1 blocks: {epoch1_start_block} - {epoch1_end_block}")
    print(f"Epoch 2 blocks: {epoch2_start_block} - {epoch2_end_block}")
    
    # Fetch all swaps from epoch 1 start to now
    print(f"Fetching Swap events from block {epoch1_start_block} to {now_block}...")
    logs = await get_logs_adaptive(market_address, epoch1_start_block, now_block, client)
    
    swaps = [parse_swap_log(log) for log in logs]
    swaps = [s for s in swaps if s]
    
    print(f"Total swaps found: {len(swaps)}")
    
    # Calculate volume by period
    def volume_in_range(from_b: int, to_b: int) -> tuple[float, int]:
        total_wei = 0
        count = 0
        for s in swaps:
            if from_b <= s["block"] <= to_b:
                total_wei += s["volume_quote_wei"]
                count += 1
        # Convert from wei (18 decimals) to native
        return total_wei / 1e18, count
    
    epoch1_vol, epoch1_count = volume_in_range(epoch1_start_block, epoch1_end_block)
    epoch2_vol, epoch2_count = volume_in_range(epoch2_start_block, epoch2_end_block)
    total_vol, total_count = volume_in_range(epoch1_start_block, now_block)
    
    return {
        "market": market_address,
        "name": name,
        "epoch1": {"volume_native": epoch1_vol, "swaps": epoch1_count, "period": "Jan 21-23"},
        "epoch2": {"volume_native": epoch2_vol, "swaps": epoch2_count, "period": "Jan 23-29"},
        "total": {"volume_native": total_vol, "swaps": total_count},
    }


async def main():
    async with httpx.AsyncClient() as client:
        results = {}
        
        # Get MON volume
        mon_data = await get_market_volume(MON_MARKET, "MON", client)
        results["MON"] = mon_data
        
        # Get BOOLY volume  
        booly_data = await get_market_volume(BOOLY_MARKET, "BOOLY", client)
        results["BOOLY"] = booly_data
        
        # Summary
        print("\n" + "="*60)
        print("VOLUME SUMMARY")
        print("="*60)
        print(f"\n{'Token':<10} {'Period':<12} {'Volume (Native)':<20} {'Swaps':<10}")
        print("-"*60)
        
        for token in ["MON", "BOOLY"]:
            data = results[token]
            print(f"{token:<10} {'Epoch 1':<12} {data['epoch1']['volume_native']:>18,.2f} {data['epoch1']['swaps']:>10}")
            print(f"{'':<10} {'Epoch 2':<12} {data['epoch2']['volume_native']:>18,.2f} {data['epoch2']['swaps']:>10}")
            print(f"{'':<10} {'Total':<12} {data['total']['volume_native']:>18,.2f} {data['total']['swaps']:>10}")
            print()
        
        # Save results
        output_path = "docs/market_volume_data.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
