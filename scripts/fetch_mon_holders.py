#!/usr/bin/env python3
"""
Fetch $MON token holders who own >1% of supply.
Uses Monadscan API (Etherscan-compatible).

Get your free API key at: https://monadscan.com/myapikey
Then run: MONADSCAN_API_KEY=your_key python scripts/fetch_mon_holders.py
"""
import os
import sys
import json
import requests
from pathlib import Path

# Config
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
TOTAL_SUPPLY = 1_000_000_000  # 1B tokens
ONE_PERCENT = TOTAL_SUPPLY // 100  # 10M tokens

API_KEY = os.getenv("MONADSCAN_API_KEY")
if not API_KEY:
    print("ERROR: Set MONADSCAN_API_KEY environment variable")
    print("Get free key at: https://monadscan.com/myapikey")
    sys.exit(1)

API_BASE = "https://api.monadscan.com/api"


def get_holders(page=1, offset=100):
    """Get token holders from Monadscan API."""
    params = {
        "module": "token",
        "action": "tokenholderlist",
        "contractaddress": MON_TOKEN,
        "page": page,
        "offset": offset,
        "apikey": API_KEY,
    }
    r = requests.get(API_BASE, params=params, timeout=30)
    data = r.json()
    if data.get("status") != "1":
        print(f"API Error: {data.get('message', data)}")
        return []
    return data.get("result", [])


def main():
    print(f"$MON Token: {MON_TOKEN}")
    print(f"Total Supply: {TOTAL_SUPPLY:,}")
    print(f"1% Threshold: {ONE_PERCENT:,} tokens\n")
    
    # Fetch all holders (paginated)
    all_holders = []
    page = 1
    while True:
        holders = get_holders(page=page)
        if not holders:
            break
        all_holders.extend(holders)
        print(f"Page {page}: {len(holders)} holders (total: {len(all_holders)})")
        page += 1
        if len(holders) < 100:
            break
    
    print(f"\nTotal holders: {len(all_holders)}")
    
    # Parse and filter for >1% holders
    top_holders = []
    for h in all_holders:
        address = h.get("TokenHolderAddress", "")
        quantity = int(h.get("TokenHolderQuantity", 0))
        balance = quantity / (10 ** 18)  # Adjust for decimals
        
        if balance >= ONE_PERCENT:
            top_holders.append({
                "address": address.lower(),
                "balance": balance,
                "percent": balance / TOTAL_SUPPLY * 100
            })
    
    top_holders.sort(key=lambda x: -x["balance"])
    
    print(f"\n{'='*70}")
    print(f"HOLDERS WITH >=1% OF SUPPLY ({ONE_PERCENT:,}+ tokens)")
    print(f"{'='*70}")
    
    for i, h in enumerate(top_holders, 1):
        print(f"{i:2}. {h['address']}: {h['balance']:,.0f} tokens ({h['percent']:.2f}%)")
    
    # Save
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output = {
        "token": MON_TOKEN,
        "total_supply": TOTAL_SUPPLY,
        "threshold_percent": 1,
        "threshold_tokens": ONE_PERCENT,
        "total_holders": len(all_holders),
        "whitelist_count": len(top_holders),
        "holders": top_holders
    }
    
    output_path = output_dir / "mon_top_holders.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to {output_path}")
    print(f"\n{'='*70}")
    print(f"WHITELIST FOR FREE MINT ({len(top_holders)} addresses):")
    print(f"{'='*70}")
    for h in top_holders:
        print(h["address"])


if __name__ == "__main__":
    main()
