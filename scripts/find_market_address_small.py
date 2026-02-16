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

# Scan 100 blocks at Epoch End
start = 51879000
end = 51879100

print(f"Scanning BOOLY transfers {start}-{end}...")
resp = rpc("eth_getLogs", [{
    "address": BOOLY_TOKEN,
    "fromBlock": hex(start),
    "toBlock": hex(end),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} BOOLY transfers.")
else:
    print(f"Booly Error: {resp}")

print(f"\nScanning MON transfers {start}-{end}...")
resp = rpc("eth_getLogs", [{
    "address": MON_TOKEN,
    "fromBlock": hex(start),
    "toBlock": hex(end),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} MON transfers.")
    for log in logs:
        src = "0x" + log["topics"][1][26:]
        dst = "0x" + log["topics"][2][26:]
        print(f"  {src} -> {dst}")
else:
    print(f"MON Error: {resp}")
