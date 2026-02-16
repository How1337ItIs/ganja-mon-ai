#!/usr/bin/env python3
import requests
import time
from datetime import datetime, timezone

MONAD_RPC = "https://rpc.monad.xyz"
# Market Contracts
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"
BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"

# Token Mill Swap Event
SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

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
    latest_resp = rpc("eth_blockNumber", [])
    high = int(latest_resp["result"], 16)
    low = max(0, high - 4000000) # Look back ~2-3 weeks
    
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

def fetch_logs(address, start_block, duration_hours, name):
    blocks_to_fetch = int(duration_hours * 3600 / 0.4)
    end_block = start_block + blocks_to_fetch
    print(f"\nScanning {name}: {start_block} -> {end_block} ({blocks_to_fetch} blocks)")
    
    chunk = 90
    current = start_block
    total_logs = []
    
    # Simple limit to avoid 1 hour wait
    max_requests = 200 
    req_count = 0
    
    while current < end_block and req_count < max_requests:
        to = min(current + chunk, end_block)
        resp = rpc("eth_getLogs", [{
            "address": address,
            "fromBlock": hex(current),
            "toBlock": hex(to),
            "topics": [SWAP_TOPIC]
        }])
        
        req_count += 1
        if "result" in resp:
            logs = resp["result"]
            if logs:
                print(f"  Found {len(logs)} swaps at {current}")
                total_logs.extend(logs)
        elif "error" in resp:
            print(f"  Err: {resp['error'].get('message', 'unknown')}")
            
        current = to + 1
        # time.sleep(0.01)

    print(f"  Total Swaps Found: {len(total_logs)}")
    return total_logs

def analyze_logs(logs):
    buy_vol = 0.0
    sell_vol = 0.0
    tx_count = len(logs)
    
    for log in logs:
        # data contains: int256 deltaBase, int256 deltaQuote, fees(4 uints)
        # 32 bytes * 6 = 192 bytes minimum data
        # We need to parse deltaQuote (2nd 32-byte word)
        try:
            data_hex = log["data"][2:]
            # Each word is 64 hex chars (32 bytes)
            # Word 0: deltaBase
            # Word 1: deltaQuote
            quote_hex = data_hex[64:128]
            # Convert signed 256-bit int
            val = int(quote_hex, 16)
            if val >= 2**255: val -= 2**256
            
            # If deltaQuote is negative, user GAVE quote (BUY base)
            # If deltaQuote is positive, user RECEIVED quote (SELL base)
            # Wait, usually: 
            # - Buy: User pays Quote (-), receives Base (+)
            # - Sell: User pays Base (-), receives Quote (+)
            # Let's assume quote dec = 18 (WMON)
            
            amount = abs(val) / 1e18
            
            if val > 0:
                sell_vol += amount # User received quote -> Sell
            else:
                buy_vol += amount # User paid quote -> Buy
                
        except Exception as e:
            print(f"Parse error: {e}")
            
    return buy_vol, sell_vol, tx_count

def main():
    # 1. MON Launch (Jan 20 20:48 UTC)
    t_launch = datetime(2026, 1, 20, 20, 48, tzinfo=timezone.utc)
    b_launch = get_block_by_time(t_launch)
    
    # 2. Reset Day (Jan 22 12:00 UTC - approx)
    t_reset = datetime(2026, 1, 22, 12, 0, tzinfo=timezone.utc)
    b_reset = get_block_by_time(t_reset)
    
    # 3. Epoch End (Jan 29 12:00 UTC)
    t_end = datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc)
    b_end = get_block_by_time(t_end)

    print("="*60)
    print("DATA GATHERING: MON vs BOOLY")
    print("="*60)
    
    # Scan MON Launch (2 hours)
    mon_launch_logs = fetch_logs(MON_MARKET, b_launch, 2, "MON Launch (2h)")
    m_buy, m_sell, m_tx = analyze_logs(mon_launch_logs)
    
    # Scan BOOLY Launch? No, scan Booly End Epoch (4h)
    # The wash trading happened 11:33-12:00 UTC Jan 29
    # Start scan at 11:00 UTC (1 hour before end)
    b_wash_start = b_end - int(3600/0.4) 
    booly_end_logs = fetch_logs(BOOLY_MARKET, b_wash_start, 1, "BOOLY End Epoch (1h)")
    b_buy, b_sell, b_tx = analyze_logs(booly_end_logs)
    
    # Scan MON End Epoch (1h) for comparison
    mon_end_logs = fetch_logs(MON_MARKET, b_wash_start, 1, "MON End Epoch (1h)")
    m_end_buy, m_end_sell, m_end_tx = analyze_logs(mon_end_logs)

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"MON Launch (2h):  {m_tx} Swaps | Vol: {m_buy+m_sell:,.2f} MON")
    print(f"MON End Epoch (1h): {m_end_tx} Swaps | Vol: {m_end_buy+m_end_sell:,.2f} MON")
    print(f"BOOLY End Epoch (1h): {b_tx} Swaps | Vol: {b_buy+b_sell:,.2f} MON")
    
    if b_tx > 0:
        print(f"\nBOOLY Wash Trading Analysis:")
        print(f"  {b_tx} Swaps in final hour")
        print(f"  Volume: {b_buy+b_sell:,.2f} MON")
        # Check unique senders
        senders = set()
        for log in booly_end_logs:
            senders.add("0x" + log["topics"][1][26:])
        print(f"  Unique Senders: {len(senders)}")
        if len(senders) < 5 and b_tx > 50:
             print("  ⚠️ HIGHLY SUSPICIOUS: Low unique sender count for high tx count")

if __name__ == "__main__":
    main()
