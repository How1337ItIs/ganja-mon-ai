#!/usr/bin/env python3
"""
Get swap event volume using BlockVision RPC with small block chunks.
"""
import json
import time
import requests
import os
from datetime import datetime, timezone

API_KEY = os.environ.get("BLOCKVISION_API_KEY")
RPC_URL = f"https://monad-mainnet.blockvision.org/v1/{API_KEY}" if API_KEY else "https://rpc.monad.xyz"

# Market contracts
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"

SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

def rpc_call(method, params):
    try:
        r = requests.post(RPC_URL, json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1}, timeout=30)
        data = r.json()
        if "error" in data:
            return None, data["error"]
        return data.get("result"), None
    except Exception as e:
        return None, str(e)

def get_logs_chunked(address, from_block, to_block, chunk_size=100):
    """Get logs in chunks."""
    all_logs = []
    current = from_block
    
    while current <= to_block:
        end = min(current + chunk_size - 1, to_block)
        result, err = rpc_call("eth_getLogs", [{
            "address": address,
            "topics": [SWAP_TOPIC],
            "fromBlock": hex(current),
            "toBlock": hex(end)
        }])
        
        if err:
            print(f"  Chunk {current}-{end} error: {err}")
            time.sleep(0.5)
            current = end + 1
            continue
        
        if result:
            all_logs.extend(result)
            print(f"  Found {len(result)} swaps in blocks {current}-{end}")
        
        time.sleep(0.1)  # Rate limit
        current = end + 1
    
    return all_logs

def decode_swap(log):
    data = log.get("data", "0x")
    if len(data) < 2 + 64*5:
        return None
    
    try:
        d = data[2:]
        base_amount = int(d[0:64], 16) / 1e18
        quote_amount = int(d[64:128], 16) / 1e18
        block = int(log.get("blockNumber", "0"), 16)
        
        return {
            "block": block,
            "tx": log.get("transactionHash"),
            "quote_mon": quote_amount,
            "base_tokens": base_amount
        }
    except:
        return None

def main():
    print("BlockVision Swap Volume Analysis")
    print("=" * 60)
    
    # Get current block
    result, _ = rpc_call("eth_blockNumber", [])
    current_block = int(result, 16) if result else 0
    print(f"Current block: {current_block}")
    
    # MON Market created around block 49,783,000 (Jan 21)
    # Let's check just the first day - about 216k blocks
    mon_start = 49_783_000
    mon_first_day_end = mon_start + 216_000  # ~1 day
    
    print(f"\n{'='*60}")
    print(f"MON Market - First Day Only (blocks {mon_start} to {mon_first_day_end})")
    print("This should capture the pre-reset activity")
    
    mon_logs = get_logs_chunked(MON_MARKET, mon_start, mon_first_day_end, chunk_size=1000)
    
    print(f"\nTotal MON swaps in first day: {len(mon_logs)}")
    
    total_volume = 0
    for log in mon_logs:
        decoded = decode_swap(log)
        if decoded:
            total_volume += decoded["quote_mon"]
    
    print(f"Total volume: {total_volume:.4f} MON")
    
    # Now check post-reset period
    epoch2_start = 50_582_793  # Jan 23 epoch start
    
    print(f"\n{'='*60}")
    print(f"MON Market - Post-Reset (blocks {epoch2_start} to {current_block})")
    
    mon_post_logs = get_logs_chunked(MON_MARKET, epoch2_start, current_block, chunk_size=1000)
    
    print(f"\nTotal MON swaps post-reset: {len(mon_post_logs)}")
    
    post_volume = 0
    for log in mon_post_logs:
        decoded = decode_swap(log)
        if decoded:
            post_volume += decoded["quote_mon"]
    
    print(f"Post-reset volume: {post_volume:.4f} MON")
    
    # Summary
    print("\n" + "=" * 60)
    print("VOLUME SUMMARY")
    print("=" * 60)
    print(f"MON Pre-Reset (Epoch 1): {len(mon_logs)} swaps, {total_volume:.4f} MON")
    print(f"MON Post-Reset (Epoch 2): {len(mon_post_logs)} swaps, {post_volume:.4f} MON")
    print(f"Total MON: {len(mon_logs) + len(mon_post_logs)} swaps, {total_volume + post_volume:.4f} MON")
    
    # Save results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_block": current_block,
        "MON": {
            "pre_reset": {
                "blocks": f"{mon_start} to {mon_first_day_end}",
                "swaps": len(mon_logs),
                "volume_mon": total_volume
            },
            "post_reset": {
                "blocks": f"{epoch2_start} to {current_block}",
                "swaps": len(mon_post_logs),
                "volume_mon": post_volume
            },
            "total": {
                "swaps": len(mon_logs) + len(mon_post_logs),
                "volume_mon": total_volume + post_volume
            }
        }
    }
    
    with open("docs/blockvision_swap_volume.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to docs/blockvision_swap_volume.json")

if __name__ == "__main__":
    main()
