#!/usr/bin/env python3
import requests

MONAD_RPC = "https://rpc.monad.xyz"
FACTORY = "0xe70d21aD211DB6DCD3f54B9804A1b64BB21b17B1"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

# Scan for Factory events involving MON
# MON Launch ~Block 50,016,000 (Jan 20)
# Scan 100k blocks around there
start = 50000000
end = 50100000

print(f"Scanning Factory {FACTORY} for MON market creation...")
print(f"Range: {start} -> {end}")

# Padded MON address for topic
mon_topic = "0x000000000000000000000000" + MON_TOKEN[2:].lower()

chunk = 2000
curr = start
while curr < end:
    to = min(curr + chunk, end)
    resp = rpc("eth_getLogs", [{
        "address": FACTORY,
        "fromBlock": hex(curr),
        "toBlock": hex(to),
        "topics": [None, mon_topic] # Topic 1 = Token?
    }])
    
    if "result" in resp and resp["result"]:
        for log in resp["result"]:
            print("FOUND LOG!")
            print(f"Tx: {log['transactionHash']}")
            print(f"Topics: {log['topics']}")
            # Usually MarketCreated(token, market, ...)
            # Topic 1: Token
            # Topic 2: Market
            if len(log["topics"]) > 2:
                market = "0x" + log["topics"][2][26:]
                print(f"Potential MARKET: {market}")
    
    curr = to + 1

# Check Booly too (created earlier? 27d ago -> Jan 2)
# Jan 2 = ~18 days before Jan 20
# 18 * 24 * 3600 / 0.4 = 3.8M blocks earlier
# Start ~46,200,000
print("\nScanning for BOOLY market...")
booly_start = 46000000
booly_end = 47000000
booly_topic = "0x000000000000000000000000" + BOOLY_TOKEN[2:].lower()

curr = booly_start
while curr < booly_end:
    to = min(curr + chunk, booly_end)
    resp = rpc("eth_getLogs", [{
        "address": FACTORY,
        "fromBlock": hex(curr),
        "toBlock": hex(to),
        "topics": [None, booly_topic]
    }])
    
    if "result" in resp and resp["result"]:
        for log in resp["result"]:
            print("FOUND BOOLY LOG!")
            if len(log["topics"]) > 2:
                market = "0x" + log["topics"][2][26:]
                print(f"Potential BOOLY MARKET: {market}")
    curr = to + 1
