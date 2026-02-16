#!/usr/bin/env python3
import requests

MONAD_RPC = "https://rpc.monad.xyz"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

# Binary search for first transfer
latest = int(rpc("eth_blockNumber", [])["result"], 16)
low = 0
high = latest
first_block = latest

print(f"Searching for birth block of {MON_TOKEN}...")

while low <= high:
    mid = (low + high) // 2
    # Check if any logs exist BEFORE mid
    # Actually, check if any logs exist IN range [0, mid] is too heavy.
    # Check a range around mid? No.
    
    # We want the FIRST log.
    # We can check if `eth_getLogs(from=0, to=mid)` returns anything?
    # No, that's too expensive/limited.
    
    # Better: Check if there are logs in [mid, latest]. If yes, might be earlier.
    # If no logs in [low, mid], then first block is > mid.
    
    # Let's just step back from latest.
    pass

# Simplified: Check if token existed at "Launch Day" (Jan 21 = Block ~50,150,000)
launch_block = 50153329 # From previous script
print(f"Checking for logs around Launch Block {launch_block}...")

resp = rpc("eth_getLogs", [{
    "address": MON_TOKEN,
    "fromBlock": hex(launch_block),
    "toBlock": hex(launch_block + 1000),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp and len(resp["result"]) > 0:
    print("Token EXISTED on Jan 21.")
else:
    print("No logs on Jan 21. Token might be newer.")

# Check around Reset Day (Jan 23 = Block ~50,580,000)
reset_block = 50584658
print(f"Checking for logs around Reset Block {reset_block}...")
resp = rpc("eth_getLogs", [{
    "address": MON_TOKEN,
    "fromBlock": hex(reset_block),
    "toBlock": hex(reset_block + 1000),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp and len(resp["result"]) > 0:
    print("Token EXISTED on Jan 23.")
else:
    print("No logs on Jan 23.")
