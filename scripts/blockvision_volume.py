#!/usr/bin/env python3
"""
Token Mill Volume Analysis using BlockVision Indexing API
Gets transaction history for market contracts and calculates volume by epoch.
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

# BlockVision API — set BLOCKVISION_API_KEY in .env (do not commit)
API_KEY = os.getenv("BLOCKVISION_API_KEY")
API_BASE = "https://api.blockvision.org/v2/monad"

# Market contracts (where swaps happen)
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"

# Epoch timestamps (Unix ms)
EPOCH1_START_TS = int(datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
EPOCH1_END_TS = int(datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
EPOCH2_START_TS = EPOCH1_END_TS
EPOCH2_END_TS = int(datetime(2026, 1, 29, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)


def api_get(endpoint: str, params: dict = None) -> dict:
    """Make API request to BlockVision."""
    headers = {"x-api-key": API_KEY}
    url = f"{API_BASE}/{endpoint}"
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            print(f"  API error: {data.get('message')}", file=sys.stderr)
            return {}
        return data.get("result", {})
    except Exception as e:
        print(f"  Request error: {e}", file=sys.stderr)
        return {}


def get_all_transactions(address: str, limit: int = 100) -> list:
    """Get all transactions for an address using pagination."""
    all_txs = []
    cursor = None
    page = 0
    
    while True:
        params = {"address": address, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        result = api_get("account/transactions", params)
        txs = result.get("data", [])
        
        if not txs:
            break
            
        all_txs.extend(txs)
        page += 1
        
        # Check if we've gone past epoch 1 start (oldest we need)
        oldest_ts = min(tx.get("timestamp", 0) for tx in txs)
        print(f"\r  Page {page}: {len(all_txs)} transactions (oldest: {datetime.fromtimestamp(oldest_ts/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')})", end="", flush=True)
        
        # Stop if we've gotten data older than epoch 1 start
        if oldest_ts < EPOCH1_START_TS:
            break
        
        cursor = result.get("nextPageCursor")
        if not cursor:
            break
    
    print()
    return all_txs


def analyze_market(market_address: str, name: str) -> dict:
    """Analyze a market contract's transaction volume."""
    print(f"\n{'='*60}")
    print(f"Analyzing {name} Market: {market_address}")
    print("="*60)
    
    # Get all transactions
    print("Fetching transactions...")
    txs = get_all_transactions(market_address)
    print(f"Total transactions fetched: {len(txs)}")
    
    # Filter to swaps only and categorize by epoch
    epoch1_swaps = []
    epoch2_swaps = []
    all_swaps = []
    
    for tx in txs:
        method = tx.get("methodName", "")
        ts = tx.get("timestamp", 0)
        
        # Only count swap transactions
        if method.lower() != "swap":
            continue
        
        all_swaps.append(tx)
        
        if EPOCH1_START_TS <= ts < EPOCH1_END_TS:
            epoch1_swaps.append(tx)
        elif EPOCH2_START_TS <= ts < EPOCH2_END_TS:
            epoch2_swaps.append(tx)
    
    print(f"Total swaps: {len(all_swaps)}")
    print(f"Epoch 1 swaps (Jan 21-23, RESET): {len(epoch1_swaps)}")
    print(f"Epoch 2 swaps (Jan 23-29, KOTM): {len(epoch2_swaps)}")
    
    return {
        "market": market_address,
        "name": name,
        "total_transactions": len(txs),
        "total_swaps": len(all_swaps),
        "epoch1": {
            "period": "Jan 21-23 (RESET by LFJ)",
            "swaps": len(epoch1_swaps),
            "sample_txs": [tx["hash"] for tx in epoch1_swaps[:3]],
        },
        "epoch2": {
            "period": "Jan 23-29 (KOTM epoch)",
            "swaps": len(epoch2_swaps),
            "sample_txs": [tx["hash"] for tx in epoch2_swaps[:3]],
        },
    }


def main():
    if not API_KEY:
        print("Error: BLOCKVISION_API_KEY not set. Add it to .env or export BLOCKVISION_API_KEY=...", file=sys.stderr)
        sys.exit(1)
    print("BlockVision Token Mill Volume Analysis")
    print("API Key: (set)")
    print(f"\nEpoch 1: {datetime.fromtimestamp(EPOCH1_START_TS/1000, tz=timezone.utc)} - {datetime.fromtimestamp(EPOCH1_END_TS/1000, tz=timezone.utc)}")
    print(f"Epoch 2: {datetime.fromtimestamp(EPOCH2_START_TS/1000, tz=timezone.utc)} - {datetime.fromtimestamp(EPOCH2_END_TS/1000, tz=timezone.utc)}")
    
    results = {}
    
    # Analyze MON market
    results["MON"] = analyze_market(MON_MARKET, "MON")
    
    # Analyze BOOLY market
    results["BOOLY"] = analyze_market(BOOLY_MARKET, "BOOLY")
    
    # Summary
    print("\n" + "="*70)
    print("SWAP VOLUME SUMMARY BY EPOCH")
    print("="*70)
    print(f"\n{'Token':<10} {'Epoch 1 (RESET)':<20} {'Epoch 2 (KOTM)':<20} {'TOTAL':>12}")
    print("-"*70)
    
    for token in ["MON", "BOOLY"]:
        data = results[token]
        e1 = data["epoch1"]["swaps"]
        e2 = data["epoch2"]["swaps"]
        total = data["total_swaps"]
        print(f"{token:<10} {e1:<20} {e2:<20} {total:>12}")
    
    print("\n" + "-"*70)
    print("KEY FINDING:")
    mon_e1 = results["MON"]["epoch1"]["swaps"]
    mon_e2 = results["MON"]["epoch2"]["swaps"]
    booly_e1 = results["BOOLY"]["epoch1"]["swaps"]
    booly_e2 = results["BOOLY"]["epoch2"]["swaps"]
    
    print(f"  MON Epoch 1 (erased by reset): {mon_e1} swaps")
    print(f"  MON Epoch 2 (KOTM counted):    {mon_e2} swaps")
    print(f"  BOOLY Epoch 1:                 {booly_e1} swaps")
    print(f"  BOOLY Epoch 2:                 {booly_e2} swaps")
    
    if mon_e1 > 0:
        print(f"\n  ** MON's {mon_e1} swaps in Epoch 1 were ERASED by LFJ's reset **")
    
    # Save results
    output_path = "docs/blockvision_market_volume.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
