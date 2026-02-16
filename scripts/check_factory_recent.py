#!/usr/bin/env python3
import requests

MONAD_RPC = "https://rpc.monad.xyz"
FACTORY = "0xe70d21aD211DB6DCD3f54B9804A1b64BB21b17B1"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

latest = int(rpc("eth_blockNumber", [])["result"], 16)
print(f"Latest: {latest}")
start = latest - 10000

print(f"Scanning Factory {FACTORY} recent activity...")
resp = rpc("eth_getLogs", [{
    "address": FACTORY,
    "fromBlock": hex(start),
    "toBlock": hex(latest)
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} logs.")
    for log in logs[:3]:
        print(f"Log: {log['topics']}")
        if len(log['topics']) > 0:
            print(f"  Event Sig: {log['topics'][0]}")
else:
    print(f"Error: {resp}")
