#!/usr/bin/env python3
"""
Query MON token volume across specific 4-hour windows to demonstrate LFJ's complicity.
Due to RPC limits (100 blocks), we sample specific high-activity windows instead of the full week.

Windows:
1. Launch Day Activity (Jan 21)
2. Pre-Reset Activity (Jan 23)
3. Post-Reset Activity (Jan 23)
4. Pre-End Activity (Jan 29)
"""
import requests
import time
from datetime import datetime, timezone, timedelta

MONAD_RPC = "https://rpc.monad.xyz"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
TOKEN_MILL_MARKET = "0x4AAC8F86203aDC88D127CCCA44f97c76b7CB0D2f"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    try:
        resp = requests.post(MONAD_RPC, json={
            "jsonrpc": "2.0", "method": method, "params": params, "id": 1
        }, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"RPC Error: {e}")
        return {}

def get_block_by_time(target_dt):
    """Binary search for block at timestamp"""
    # Get latest
    latest_resp = rpc("eth_blockNumber", [])
    high = int(latest_resp["result"], 16)
    low = high - 4000000 
    if low < 0: low = 0
    
    target_ts = target_dt.timestamp()
    
    print(f"Finding block for {target_dt}...")
    
    for i in range(20): 
        mid = (low + high) // 2
        resp = rpc("eth_getBlockByNumber", [hex(mid), False])
        if "result" not in resp or not resp["result"]:
            continue
            
        ts = int(resp["result"]["timestamp"], 16)
        if ts < target_ts:
            low = mid
        else:
            high = mid
            
        if high - low < 100:
            break
            
    return high

def get_window_logs(start_block, duration_hours=4):
    """Fetch logs for a duration (in blocks) starting from start_block"""
    # 0.4s block time -> 1 hour = 9000 blocks
    blocks_to_fetch = int(duration_hours * 3600 / 0.4) 
    end_block = start_block + blocks_to_fetch
    
    print(f"Fetching {duration_hours}h window: {start_block} to {end_block} ({blocks_to_fetch} blocks)")
    
    all_logs = []
    chunk_size = 90 # Safe under 100 limit
    current = start_block
    
    while current < end_block:
        to_block = min(current + chunk_size, end_block)
        try:
            resp = rpc("eth_getLogs", [{
                "address": MON_TOKEN,
                "fromBlock": hex(current),
                "toBlock": hex(to_block),
                "topics": [TRANSFER_TOPIC]
            }])
            
            if "result" in resp:
                all_logs.extend(resp["result"])
            elif "error" in resp:
                print(f"  RPC Error at {current}: {resp['error']['message']}")
                # If limited, try smaller chunk? 
                if "limit" in str(resp['error']).lower():
                    chunk_size = max(10, chunk_size // 2)
                    continue

        except Exception as e:
            print(f"  Net Error: {e}")
            
        current = to_block + 1
        # No sleep needed usually if sequential, but let's be nice
        # time.sleep(0.01) 
        
    return all_logs

def analyze_logs(logs, name):
    vol_bought = 0
    vol_sold = 0
    tx_count = 0
    unique_wallets = set()
    market_addr = TOKEN_MILL_MARKET.lower()
    
    for log in logs:
        if len(log["topics"]) < 3: continue
        src = "0x" + log["topics"][1][26:]
        dst = "0x" + log["topics"][2][26:]
        try:
            val = int(log["data"], 16) / 1e18
        except: continue
        
        # Filter for Market activity
        if src == market_addr:
            vol_bought += val
            unique_wallets.add(dst)
            tx_count += 1
        elif dst == market_addr:
            vol_sold += val
            unique_wallets.add(src)
            tx_count += 1
            
    print(f"\nANALYSIS: {name}")
    print(f"  Tx Count: {tx_count}")
    print(f"  Buy Vol:  {vol_bought:,.2f}")
    print(f"  Sell Vol: {vol_sold:,.2f}")
    print(f"  Active Wallets: {len(unique_wallets)}")
    return vol_bought + vol_sold

def main():
    # 1. Launch Day (Jan 21 18:00 UTC - just after typical US work start?)
    # Actually let's do Jan 21 12:00 UTC
    t1 = datetime(2026, 1, 21, 12, 0, tzinfo=timezone.utc)
    b1 = get_block_by_time(t1)
    
    # 2. Pre-Reset (Jan 23 08:00 UTC - Morning before reset)
    t2 = datetime(2026, 1, 23, 8, 0, tzinfo=timezone.utc)
    b2 = get_block_by_time(t2)
    
    # 3. Epoch End (Jan 29 08:00 UTC - Final run)
    t3 = datetime(2026, 1, 29, 8, 0, tzinfo=timezone.utc)
    b3 = get_block_by_time(t3)
    
    print("\n=== FETCHING DATA ===")
    logs1 = get_window_logs(b1, duration_hours=4)
    vol1 = analyze_logs(logs1, "Launch Window (Jan 21 12:00-16:00 UTC)")
    
    logs2 = get_window_logs(b2, duration_hours=4)
    vol2 = analyze_logs(logs2, "Pre-Reset Window (Jan 23 08:00-12:00 UTC)")
    
    logs3 = get_window_logs(b3, duration_hours=4)
    vol3 = analyze_logs(logs3, "Epoch End Window (Jan 29 08:00-12:00 UTC)")

if __name__ == "__main__":
    main()
