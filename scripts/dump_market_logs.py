#!/usr/bin/env python3
import requests

MONAD_RPC = "https://rpc.monad.xyz"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

# Wash trading happened around Jan 29 11:58 UTC = Block 51879087
# Let's check 100 blocks around there
start = 51879000
end = 51879100

print(f"Dumping logs for BOOLY Market {BOOLY_MARKET} blocks {start}-{end}...")
resp = rpc("eth_getLogs", [{
    "address": BOOLY_MARKET,
    "fromBlock": hex(start),
    "toBlock": hex(end)
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} logs.")
    for log in logs[:3]:
        print(f"Log: {log['topics']}")
        print(f"Topic 0: {log['topics'][0]}")
else:
    print(f"Error: {resp}")

# Check MON Market too
print(f"\nDumping logs for MON Market {MON_MARKET} same range...")
resp = rpc("eth_getLogs", [{
    "address": MON_MARKET,
    "fromBlock": hex(start),
    "toBlock": hex(end)
}])

if "result" in resp:
    logs = resp["result"]
    print(f"Found {len(logs)} logs.")
else:
    print(f"Error: {resp}")
