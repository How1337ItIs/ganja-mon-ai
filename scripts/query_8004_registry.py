#!/usr/bin/env python3
"""Query Monad ERC-8004 Identity Registry for agent tokenURIs (agents 1-4)."""
import json
import urllib.request

RPC = "https://rpc.monad.xyz/"
REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
# tokenURI(uint256) selector
SELECTOR = "0xc87b56dd"

def eth_call(data_hex: str) -> str:
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"to": REGISTRY, "data": data_hex},
            "latest",
        ],
        "id": 1,
    }
    req = urllib.request.Request(
        RPC,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        out = json.load(r)
    if "error" in out:
        raise RuntimeError(out["error"])
    return out.get("result", "")

def decode_string_result(hex_result: str) -> str:
    if not hex_result or hex_result == "0x":
        return ""
    # Dynamic string: offset 32, length in first word
    data = bytes.fromhex(hex_result[2:])
    if len(data) < 64:
        return ""
    length = int.from_bytes(data[32:64], "big")
    if len(data) < 64 + length:
        return ""
    return data[64 : 64 + length].decode("utf-8", errors="replace")

def main():
    for agent_id in range(1, 5):
        data_hex = SELECTOR + hex(agent_id)[2:].zfill(64)
        try:
            result = eth_call(data_hex)
            uri = decode_string_result(result)
            print(f"Agent {agent_id}: {uri or '(empty)'}")
        except Exception as e:
            print(f"Agent {agent_id}: error - {e}")

if __name__ == "__main__":
    main()
