#!/usr/bin/env python3
"""
Quick volume check using Monad Infrastructure historical RPC.
Uses the rpc-mainnet.monadinfra.com endpoint for historical data.
"""
import json
import requests
import os
from datetime import datetime, timezone

# Market contracts
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"

# Swap event topic (Token Mill)
SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

# RPC endpoints to try (BlockVision only if BLOCKVISION_API_KEY is set)
_bv_key = os.environ.get("BLOCKVISION_API_KEY")
RPC_ENDPOINTS = [
    "https://rpc-mainnet.monadinfra.com",
    "https://rpc.monad.xyz",
]
if _bv_key:
    RPC_ENDPOINTS.append(f"https://monad-mainnet.blockvision.org/v1/{_bv_key}")

def rpc_call(url, method, params):
    """Make RPC call."""
    try:
        r = requests.post(
            url,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        data = r.json()
        if "error" in data:
            return None, data["error"]
        return data.get("result"), None
    except Exception as e:
        return None, str(e)

def get_logs_single_call(rpc_url, address, from_block, to_block):
    """Get logs with a single eth_getLogs call."""
    print(f"Querying {rpc_url} blocks {from_block} to {to_block}...")
    
    result, err = rpc_call(rpc_url, "eth_getLogs", [{
        "address": address,
        "topics": [SWAP_TOPIC],
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block)
    }])
    
    if err:
        print(f"  Error: {err}")
        return None
    
    print(f"  Found {len(result)} swap events")
    return result

def decode_swap_event(log):
    """Decode a Token Mill swap event to extract volume."""
    # Token Mill Swap event:
    # event Swap(address indexed sender, bool indexed isBuy, uint256 baseTokenAmount, 
    #            uint256 quoteTokenAmount, uint256 fee, uint256 protocolFee, uint256 newPrice);
    
    # Data contains: baseTokenAmount, quoteTokenAmount, fee, protocolFee, newPrice (each 32 bytes)
    data = log.get("data", "0x")
    if len(data) < 2 + 32*5*2:
        return None
    
    try:
        # Extract values (32 bytes each, hex encoded = 64 chars)
        data_clean = data[2:]  # Remove 0x
        base_amount = int(data_clean[0:64], 16)
        quote_amount = int(data_clean[64:128], 16)
        fee = int(data_clean[128:192], 16)
        protocol_fee = int(data_clean[192:256], 16)
        new_price = int(data_clean[256:320], 16)
        
        # Quote amount is in WMON (18 decimals)
        quote_in_mon = quote_amount / 1e18
        
        return {
            "block": int(log.get("blockNumber", "0"), 16),
            "tx": log.get("transactionHash"),
            "base_amount": base_amount,
            "quote_amount_wei": quote_amount,
            "quote_amount_mon": quote_in_mon,
            "fee_wei": fee,
            "is_buy": log.get("topics", ["", ""])[1] == "0x0000000000000000000000000000000000000000000000000000000000000001"
        }
    except Exception as e:
        return None

def analyze_market(name, address, rpc_url, from_block, to_block):
    """Analyze swap events for a market."""
    print(f"\n{'='*60}")
    print(f"Analyzing {name}: {address}")
    
    logs = get_logs_single_call(rpc_url, address, from_block, to_block)
    if logs is None:
        return None
    
    swaps = []
    total_volume_mon = 0
    
    for log in logs:
        decoded = decode_swap_event(log)
        if decoded:
            swaps.append(decoded)
            total_volume_mon += decoded["quote_amount_mon"]
    
    print(f"  Decoded {len(swaps)} swaps")
    print(f"  Total volume: {total_volume_mon:.4f} MON")
    
    # Group by day
    # We need block timestamps for this - skip for now
    
    return {
        "name": name,
        "address": address,
        "total_swaps": len(swaps),
        "total_volume_mon": total_volume_mon,
        "swaps": swaps[:10]  # First 10 for sample
    }

def main():
    print("Quick Token Mill Volume Check")
    print("=" * 60)
    
    # Get current block
    for rpc_url in RPC_ENDPOINTS:
        result, err = rpc_call(rpc_url, "eth_blockNumber", [])
        if result:
            current_block = int(result, 16)
            print(f"Using RPC: {rpc_url}")
            print(f"Current block: {current_block}")
            break
    else:
        print("ERROR: All RPC endpoints failed")
        return
    
    # MON was created on Jan 21 (~block 49,000,000)
    # Query from Jan 20 to now
    from_block = 49_000_000
    to_block = current_block
    
    # Try with a smaller range first (last 500k blocks = ~2.5 days)
    test_from = current_block - 500_000
    
    print(f"\nTesting with recent range: {test_from} to {to_block}")
    
    mon_result = analyze_market("MON", MON_MARKET, rpc_url, test_from, to_block)
    booly_result = analyze_market("BOOLY", BOOLY_MARKET, rpc_url, test_from, to_block)
    
    # Now try full range
    print(f"\n\nTrying full range: {from_block} to {to_block}")
    print("(This may take longer or fail due to block range limits)")
    
    mon_full = analyze_market("MON (Full)", MON_MARKET, rpc_url, from_block, to_block)
    booly_full = analyze_market("BOOLY (Full)", BOOLY_MARKET, rpc_url, from_block, to_block)
    
    # Output results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rpc_endpoint": rpc_url,
        "recent_range": {
            "from_block": test_from,
            "to_block": to_block,
            "MON": mon_result,
            "BOOLY": booly_result
        },
        "full_range": {
            "from_block": from_block,
            "to_block": to_block,
            "MON": mon_full,
            "BOOLY": booly_full
        }
    }
    
    # Save results
    output_path = "docs/quick_volume_check.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\nResults saved to {output_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if mon_result and booly_result:
        print(f"Recent Range ({test_from} to {to_block}):")
        print(f"  MON: {mon_result['total_swaps']} swaps, {mon_result['total_volume_mon']:.4f} MON")
        print(f"  BOOLY: {booly_result['total_swaps']} swaps, {booly_result['total_volume_mon']:.4f} MON")
    
    if mon_full and booly_full:
        print(f"\nFull Range ({from_block} to {to_block}):")
        print(f"  MON: {mon_full['total_swaps']} swaps, {mon_full['total_volume_mon']:.4f} MON")
        print(f"  BOOLY: {booly_full['total_swaps']} swaps, {booly_full['total_volume_mon']:.4f} MON")

if __name__ == "__main__":
    main()
