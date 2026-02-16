#!/usr/bin/env python3
"""
Query Swap events from Token Mill market contracts using BlockVision RPC.
Uses eth_getLogs with 100-block chunks (BlockVision limit).
"""
import json
import os
import time
import sys
from datetime import datetime, timezone

import requests

API_KEY = os.environ.get("BLOCKVISION_API_KEY")
RPC_URL = f"https://monad-mainnet.blockvision.org/v1/{API_KEY}" if API_KEY else "https://rpc.monad.xyz"

# Market contracts
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"

# Swap event topic
SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

# Monad ~0.4s blocks = 216000 blocks/day
BLOCKS_PER_DAY = 216_000

# Epoch timestamps
EPOCH1_START = datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)  # Jan 21 4AM PST
EPOCH1_END = datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc)    # Jan 23 4AM PST (reset)
EPOCH2_START = EPOCH1_END
EPOCH2_END = datetime(2026, 1, 29, 12, 0, 0, tzinfo=timezone.utc)    # Jan 29 4AM PST


def rpc_call(method, params):
    """Make RPC call with retry."""
    for attempt in range(3):
        try:
            r = requests.post(
                RPC_URL,
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                timeout=30,
            )
            data = r.json()
            if "error" in data:
                err = data["error"]
                if "429" in str(err) or "rate" in str(err).lower():
                    time.sleep(2 ** attempt)
                    continue
                return None, err
            return data.get("result"), None
        except Exception as e:
            time.sleep(1)
    return None, "Max retries exceeded"


def get_current_block():
    result, _ = rpc_call("eth_blockNumber", [])
    return int(result, 16) if result else 0


def get_block_timestamp(block_num):
    result, _ = rpc_call("eth_getBlockByNumber", [hex(block_num), False])
    if result:
        return int(result.get("timestamp", "0x0"), 16)
    return 0


def get_swap_logs(market_address, from_block, to_block):
    """Get all Swap events from a market contract, 100 blocks at a time."""
    all_logs = []
    current = from_block
    chunk_size = 100
    total_chunks = (to_block - from_block) // chunk_size + 1
    chunks_done = 0
    
    while current <= to_block:
        end = min(current + chunk_size - 1, to_block)
        
        result, err = rpc_call("eth_getLogs", [{
            "address": market_address,
            "fromBlock": hex(current),
            "toBlock": hex(end),
            "topics": [SWAP_TOPIC],
        }])
        
        if result is not None:
            all_logs.extend(result)
        elif err:
            print(f"\n  Error at {current}: {err}", file=sys.stderr)
        
        chunks_done += 1
        if chunks_done % 50 == 0:
            pct = (chunks_done / total_chunks) * 100
            print(f"\r  Progress: {pct:.1f}% ({len(all_logs)} swaps)", end="", flush=True)
        
        current = end + 1
        time.sleep(0.15)  # Rate limit
    
    print(f"\r  Complete: {len(all_logs)} swaps found" + " " * 20)
    return all_logs


def parse_swap_volume(log):
    """Parse deltaQuoteAmount from Swap event data."""
    data = log.get("data", "0x")
    if len(data) < 2 + 128:  # Need at least 2 int256 values
        return 0
    
    # data = deltaBaseAmount (32 bytes) + deltaQuoteAmount (32 bytes) + fees
    delta_quote = int(data[2+64:2+128], 16)
    if delta_quote >= 2**255:
        delta_quote -= 2**256
    
    return abs(delta_quote)


def main():
    print("Token Mill Swap Event Analysis")
    print("=" * 60)
    
    # Get current block and timestamp
    now_block = get_current_block()
    now_ts = get_block_timestamp(now_block)
    print(f"Current block: {now_block}")
    print(f"Current time: {datetime.fromtimestamp(now_ts, tz=timezone.utc)}")
    
    # Calculate block ranges for epochs
    def ts_to_block(dt):
        ts = dt.timestamp()
        return max(0, now_block - int((now_ts - ts) / 0.4))
    
    epoch1_start_block = ts_to_block(EPOCH1_START)
    epoch1_end_block = ts_to_block(EPOCH1_END)
    epoch2_start_block = epoch1_end_block
    epoch2_end_block = ts_to_block(EPOCH2_END)
    
    # Use creation date as actual start (MON created Jan 21)
    mon_start_block = epoch1_start_block
    
    print(f"\nEpoch 1: blocks {epoch1_start_block} - {epoch1_end_block}")
    print(f"Epoch 2: blocks {epoch2_start_block} - {epoch2_end_block}")
    
    results = {}
    
    for name, market in [("MON", MON_MARKET), ("BOOLY", BOOLY_MARKET)]:
        print(f"\n{'='*60}")
        print(f"Analyzing {name} Market: {market}")
        
        # Query from 10 days ago to cover everything
        start_block = now_block - (10 * BLOCKS_PER_DAY)
        print(f"Querying blocks {start_block} to {now_block}...")
        
        logs = get_swap_logs(market, start_block, now_block)
        
        # Categorize by epoch
        epoch1_swaps = []
        epoch2_swaps = []
        other_swaps = []
        epoch1_volume = 0
        epoch2_volume = 0
        
        for log in logs:
            block = int(log.get("blockNumber", "0x0"), 16)
            volume = parse_swap_volume(log)
            
            if epoch1_start_block <= block < epoch1_end_block:
                epoch1_swaps.append(log)
                epoch1_volume += volume
            elif epoch2_start_block <= block < epoch2_end_block:
                epoch2_swaps.append(log)
                epoch2_volume += volume
            else:
                other_swaps.append(log)
        
        results[name] = {
            "market": market,
            "total_swaps": len(logs),
            "epoch1": {
                "swaps": len(epoch1_swaps),
                "volume_wei": epoch1_volume,
                "volume_native": epoch1_volume / 1e18,
            },
            "epoch2": {
                "swaps": len(epoch2_swaps),
                "volume_wei": epoch2_volume,
                "volume_native": epoch2_volume / 1e18,
            },
            "other": len(other_swaps),
        }
        
        print(f"  Total swaps: {len(logs)}")
        print(f"  Epoch 1 (Jan 21-23): {len(epoch1_swaps)} swaps, {epoch1_volume/1e18:.2f} native")
        print(f"  Epoch 2 (Jan 23-29): {len(epoch2_swaps)} swaps, {epoch2_volume/1e18:.2f} native")
        print(f"  Other: {len(other_swaps)} swaps")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Token':<8} {'Epoch 1':<15} {'Epoch 2':<15} {'Total':<10}")
    print("-" * 60)
    for name in ["MON", "BOOLY"]:
        r = results[name]
        e1 = r["epoch1"]["swaps"]
        e2 = r["epoch2"]["swaps"]
        print(f"{name:<8} {e1:<15} {e2:<15} {r['total_swaps']:<10}")
    
    # Save
    with open("docs/swap_event_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved to docs/swap_event_analysis.json")


if __name__ == "__main__":
    main()
