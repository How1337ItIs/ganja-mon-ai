#!/usr/bin/env python3
import requests
import time

MONAD_RPC = "https://rpc.monad.xyz"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    try:
        return requests.post(MONAD_RPC, json={
            "jsonrpc": "2.0", "method": method, "params": params, "id": 1
        }, timeout=5).json()
    except Exception as e:
        print(f"Connection error: {e}")
        return {{}}

# 1. Check connection and latest block
latest = rpc("eth_blockNumber", [])
if "result" not in latest:
    print("FATAL: Could not get block number. Check RPC.")
    exit(1)
    
latest_block = int(latest["result"], 16)
print(f"Latest Block: {latest_block}")

# 2. Check logs in last 1000 blocks (chunked)
print("Checking recent MON activity...")
found_logs = []
for i in range(10):
    start = latest_block - (i+1)*100
    end = latest_block - i*100
    
    resp = rpc("eth_getLogs", [{
        "address": MON_TOKEN,
        "fromBlock": hex(start),
        "toBlock": hex(end),
        "topics": [TRANSFER_TOPIC]
    }])
    
    if "result" in resp:
        found_logs.extend(resp["result"])
    else:
        print(f"Error chunk {i}: {resp.get('error')}")

print(f"Found {len(found_logs)} logs in last 1000 blocks.")

if len(found_logs) > 0:
    # Identify Market Address (most active non-mint/burn address)
    activity = {{}}
    for log in found_logs:
        topics = log["topics"]
        if len(topics) < 3: continue
        src = "0x" + topics[1][26:].lower()
        dst = "0x" + topics[2][26:].lower()
        
        activity[src] = activity.get(src, 0) + 1
        activity[dst] = activity.get(dst, 0) + 1
        
    # Sort by activity
    sorted_act = sorted(activity.items(), key=lambda x: x[1], reverse=True)
    print("\nTop Active Addresses (Potential Market):")
    for addr, count in sorted_act[:5]:
        print(f"  {addr}: {count} txs")
else:
    print("No recent activity found. Trying a known active block from previous turn...")
    # Known block with activity: 51879087
    target = 51879087
    resp = rpc("eth_getLogs", [{
        "address": MON_TOKEN,
        "fromBlock": hex(target-10),
        "toBlock": hex(target+10),
        "topics": [TRANSFER_TOPIC]
    }])
    print(f"Check around block {target}: {len(resp.get('result', []))} logs")
