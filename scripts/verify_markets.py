#!/usr/bin/env python3
import requests
from web3 import Web3

MONAD_RPC = "https://rpc.monad.xyz"
FACTORY = "0xe70d21aD211DB6DCD3f54B9804A1b64BB21b17B1"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

def get_market(token_addr):
    # Function: getMarketOf(address)
    # Selector: keccak256("getMarketOf(address)")[:4]
    w3 = Web3()
    selector = w3.keccak(text="getMarketOf(address)")[:4].hex()
    
    # Pad address to 32 bytes
    param = "000000000000000000000000" + token_addr[2:]
    data = selector + param
    
    resp = rpc("eth_call", [{"to": FACTORY, "data": data}, "latest"])
    if "result" in resp:
        # Result is 32 bytes address
        return "0x" + resp["result"].lstrip('0')
    return None

print(f"Factory: {FACTORY}")
mon_market = get_market(MON_TOKEN)
print(f"MON Market:   {mon_market}")

booly_market = get_market(BOOLY_TOKEN)
print(f"BOOLY Market: {booly_market}")

# Now check for ANY activity on these markets in the last 1000 blocks
latest = int(rpc("eth_blockNumber", [])["result"], 16)
print(f"\nChecking activity on markets (Last 1000 blocks from {latest})...")

for name, addr in [("MON", mon_market), ("BOOLY", booly_market)]:
    if not addr or addr == "0x0000000000000000000000000000000000000000":
        print(f"{name}: No Market!")
        continue
        
    resp = rpc("eth_getLogs", [{
        "address": addr,
        "fromBlock": hex(latest - 1000),
        "toBlock": hex(latest)
    }])
    
    count = len(resp.get("result", []))
    print(f"{name} Market ({addr}): {count} events")
