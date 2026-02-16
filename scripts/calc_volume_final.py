#!/usr/bin/env python3
import requests
import time

MONAD_RPC = "https://rpc.monad.xyz"
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"
MON_TOKEN = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"

BOOLY_MARKET = "0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f"
MON_MARKET = "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B"

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def rpc(method, params):
    try:
        return requests.post(MONAD_RPC, json={
            "jsonrpc": "2.0", "method": method, "params": params, "id": 1
        }, timeout=5).json()
    except:
        return {}

def scan_volume(token_addr, market_addr, start, end, name):
    print(f"Scanning {name} ({start}-{end})...")
    chunk = 90
    curr = start
    total_vol = 0.0
    tx_count = 0
    wallets = set()
    market_addr = market_addr.lower()
    
    while curr < end:
        to = min(curr + chunk, end)
        resp = rpc("eth_getLogs", [{
            "address": token_addr,
            "fromBlock": hex(curr),
            "toBlock": hex(to),
            "topics": [TRANSFER_TOPIC]
        }])
        
        if "result" in resp:
            for log in resp["result"]:
                if len(log["topics"]) < 3: continue
                src = "0x" + log["topics"][1][26:].lower()
                dst = "0x" + log["topics"][2][26:].lower()
                
                # Check if Market involved
                is_market = (src == market_addr or dst == market_addr)
                
                if is_market:
                    try:
                        val = int(log["data"], 16) / 1e18
                        total_vol += val
                        tx_count += 1
                        if src == market_addr: wallets.add(dst)
                        else: wallets.add(src)
                    except: pass
        curr = to + 1

    print(f"  {name}: {tx_count} Market Txs | Vol: {total_vol:,.2f} | Wallets: {len(wallets)}")
    return total_vol, tx_count, len(wallets)

def main():
    # 1. Wash Window (Jan 29 11:33-12:00 UTC)
    end_wash = 51879038
    start_wash = end_wash - 4000
    
    # 2. Launch Window (Jan 20 20:48 + 2h)
    # Block ~50016745
    start_launch = 50016745
    end_launch = start_launch + 18000 # 2 hours
    
    print("=== FINAL VOLUME CALCULATION ===")
    
    # BOOLY Wash
    b_vol, b_tx, b_wal = scan_volume(BOOLY_TOKEN, BOOLY_MARKET, start_wash, end_wash, "BOOLY End Epoch")
    
    # MON End Epoch
    m_vol, m_tx, m_wal = scan_volume(MON_TOKEN, MON_MARKET, start_wash, end_wash, "MON End Epoch")
    
    # MON Launch (Lost Volume)
    ml_vol, ml_tx, ml_wal = scan_volume(MON_TOKEN, MON_MARKET, start_launch, end_launch, "MON Launch (Lost)")
    
    print("\nSUMMARY:")
    print(f"BOOLY Wash Vol: {b_vol:,.2f} ({b_tx} txs, {b_wal} wallets)")
    print(f"MON End Vol:    {m_vol:,.2f} ({m_tx} txs, {m_wal} wallets)")
    print(f"MON Lost Vol:   {ml_vol:,.2f} ({ml_tx} txs, {ml_wal} wallets)")
    
    if m_vol > 0:
        print(f"Ratio (Booly/Mon End): {b_vol/m_vol:.2f}x")
    if b_vol > 0:
        print(f"If Lost Vol added: MON would be {m_vol + ml_vol:,.2f} vs BOOLY {b_vol:,.2f}")

if __name__ == "__main__":
    main()
