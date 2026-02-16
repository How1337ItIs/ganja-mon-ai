#!/usr/bin/env python3
import requests

MONAD_RPC = "https://rpc.monad.xyz"
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

# Scan last 20k blocks for transfers
latest = int(rpc("eth_blockNumber", [])["result"], 16)
start = latest - 20000

print(f"Scanning BOOLY transfers {start}-{latest}...")
resp = rpc("eth_getLogs", [{
    "address": BOOLY_TOKEN,
    "fromBlock": hex(start),
    "toBlock": hex(latest),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} BOOLY transfers.")
    counts = {}
    for log in logs:
        if len(log["topics"]) < 3: continue
        src = "0x" + log["topics"][1][26:]
        dst = "0x" + log["topics"][2][26:]
        counts[src] = counts.get(src, 0) + 1
        counts[dst] = counts.get(dst, 0) + 1
    
    # Sort
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    print("Top BOOLY Addresses:")
    for addr, count in sorted_counts[:5]:
        print(f"  {addr}: {count}")
else:
    print(f"Error: {resp}")

# Same for MON
print(f"\nScanning MON transfers {start}-{latest}...")
resp = rpc("eth_getLogs", [{
    "address": MON_TOKEN,
    "fromBlock": hex(start),
    "toBlock": hex(latest),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} MON transfers.")
    counts = {}
    for log in logs:
        if len(log["topics"]) < 3: continue
        src = "0x" + log["topics"][1][26:]
        dst = "0x" + log["topics"][2][26:]
        counts[src] = counts.get(src, 0) + 1
        counts[dst] = counts.get(dst, 0) + 1
    
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    print("Top MON Addresses:")
    for addr, count in sorted_counts[:5]:
        print(f"  {addr}: {count}")
