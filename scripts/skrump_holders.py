#!/usr/bin/env python3
"""
Fetch SKRUMP (Skrumpeys) NFT holders on Monad via OpenSea API.
Contract: 0xb0dad798c80e40dd6b8e8545074c6a5b7b97d2c0
List endpoint doesn't include owners; we fetch each NFT by id to get owner.
Output: CSV + JSON with address and quantity.
"""
import csv
import json
import time
from pathlib import Path

import requests

CONTRACT = "0xb0dad798c80e40dd6b8e8545074c6a5b7b97d2c0"
CHAIN = "monad"
BASE = f"https://api.opensea.io/v2/chain/{CHAIN}/contract/{CONTRACT}/nfts"
LIMIT = 100
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "skrump_holders"
DELAY = 0.25  # seconds between single-NFT requests


def fetch_list_page(cursor: str | None = None) -> dict:
    params = {"limit": LIMIT}
    if cursor:
        params["next"] = cursor
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_nft(token_id: str) -> dict | None:
    url = f"{BASE}/{token_id}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  skip {token_id}: {e}")
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Collect all token identifiers from list endpoint
    identifiers: list[str] = []
    cursor = None
    while True:
        data = fetch_list_page(cursor)
        nfts = data.get("nfts") or []
        for nft in nfts:
            identifiers.append(nft["identifier"])
        cursor = data.get("next")
        if not cursor or not nfts:
            break
        time.sleep(0.3)
    print(f"Collected {len(identifiers)} token IDs. Fetching owners (one request per NFT)...")

    # 2) Fetch each NFT by id to get owners
    holders: dict[str, int] = {}
    for i, token_id in enumerate(identifiers):
        data = fetch_nft(token_id)
        if data and "nft" in data:
            for owner in (data["nft"].get("owners") or []):
                addr = (owner.get("address") or "").strip().lower()
                qty = int(owner.get("quantity", 1))
                if addr:
                    holders[addr] = holders.get(addr, 0) + qty
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(identifiers)} NFTs, {len(holders)} unique holders")
        time.sleep(DELAY)

    rows = sorted(holders.items(), key=lambda x: (-x[1], x[0]))

    csv_path = OUT_DIR / "skrump_holders.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["address", "quantity"])
        w.writerows(rows)

    json_path = OUT_DIR / "skrump_holders.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            [{"address": a, "quantity": q} for a, q in rows],
            f,
            indent=2,
        )

    print(f"Done. {len(holders)} unique holders, {sum(holders.values())} total NFTs.")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
