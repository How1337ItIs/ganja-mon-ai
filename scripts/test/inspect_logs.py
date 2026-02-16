#!/usr/bin/env python3
import requests

MONAD_RPC = "https://rpc.monad.xyz"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    return requests.post(MONAD_RPC, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    }, timeout=5).json()

target = 51879087
print(f"Inspecting logs around block {target}...")

resp = rpc("eth_getLogs", [{
    "address": MON_TOKEN,
    "fromBlock": hex(target-10),
    "toBlock": hex(target+10),
    "topics": [TRANSFER_TOPIC]
}])

if "result" in resp:
    for log in resp["result"]:
        topics = log["topics"]
        src = "0x" + topics[1][26:]
        dst = "0x" + topics[2][26:]
        val = int(log["data"], 16) / 1e18
        print(f"Tx: {log['transactionHash']}")
        print(f"  From: {src}")
        print(f"  To:   {dst}")
        print(f"  Val:  {val:,.2f}")
else:
    print("No logs found.")
