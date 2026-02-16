#!/usr/bin/env python3
import requests
import time

MONAD_RPC = "https://rpc.monad.xyz"
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    try:
        return requests.post(MONAD_RPC, json={
            "jsonrpc": "2.0", "method": method, "params": params, "id": 1
        }, timeout=5).json()
    except:
        return {}

# Scan ~4000 blocks before epoch end (27 mins)
end_block = 51879038
start_block = end_block - 4000

print(f"Scanning BOOLY {start_block}-{end_block} (Wash Trade Window)...")

chunk = 90
curr = start_block
total_logs = []

while curr < end_block:
    to = min(curr + chunk, end_block)
    resp = rpc("eth_getLogs", [{
        "address": BOOLY_TOKEN,
        "fromBlock": hex(curr),
        "toBlock": hex(to),
        "topics": [TRANSFER_TOPIC]
    }])
    
    if "result" in resp:
        total_logs.extend(resp["result"])
        if len(resp["result"]) > 0:
            print(f"  Found {len(resp['result'])} logs at {curr}")
            
    curr = to + 1
    # time.sleep(0.01)

print(f"\nTotal BOOLY Transfers Found: {len(total_logs)}")
if len(total_logs) == 0:
    print("CONFIRMED: Zero ERC20 Transfers for Booly in this window.")
else:
    print("Found activity!")
