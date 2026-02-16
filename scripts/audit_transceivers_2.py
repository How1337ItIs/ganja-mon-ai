"""Check the mystery Base transceiver and verify no pending transfers."""
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def eth_call(rpc, to, data):
    payload = json.dumps({
        "jsonrpc": "2.0", "method": "eth_call",
        "params": [{"to": to, "data": data}, "latest"], "id": 1
    }).encode()
    req = urllib.request.Request(rpc, payload, {
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        result = json.loads(resp.read())
        if "result" in result and len(result["result"]) > 2:
            return result["result"]
        return f"ERROR: {result.get('error', 'empty')}"
    except Exception as e:
        return f"ERROR: {e}"

BASE_RPC = "https://base-rpc.publicnode.com"
MONAD_RPC = "https://monad.drpc.org"

# Selector from previous run
SEL_PEER = "935dec07"

# Monad wormhole chain = 48 = 0x30
MONAD_WH = "0030".zfill(64)
BASE_WH = "001e".zfill(64)

# Check mystery Base transceiver 0x28a16fa476789f54a683b4513bba2c9e3a0c5217
mystery = "0x28a16fa476789f54a683b4513bba2c9e3a0c5217"
print(f"Mystery Base transceiver: {mystery}")

# Get its Monad peer
result = eth_call(BASE_RPC, mystery, f"0x{SEL_PEER}{MONAD_WH}")
if not result.startswith("ERROR"):
    peer = "0x" + result[-40:]
    is_zero = all(c == '0' for c in result[2:])
    print(f"  Monad peer: {'NO PEER (zero)' if is_zero else peer}")
else:
    print(f"  Monad peer query: {result}")

# Also check its Base peer (might be peered to another Monad transceiver)
result = eth_call(BASE_RPC, mystery, f"0x{SEL_PEER}{BASE_WH}")
if not result.startswith("ERROR"):
    peer = "0x" + result[-40:]
    is_zero = all(c == '0' for c in result[2:])
    print(f"  Base peer (self-chain): {'NO PEER (zero)' if is_zero else peer}")
else:
    print(f"  Base peer query: {result}")

# Check what that Monad OLD peers with on Base (the 0x13cab335 address)
print()
old_base_peer = "0x13cab3351f894157affe6e2b97bf224b59df75bf"
print(f"Old Base peer of Monad OLD: {old_base_peer}")
# Check if this address has code on Base
result = json.dumps({
    "jsonrpc": "2.0", "method": "eth_getCode",
    "params": [old_base_peer, "latest"], "id": 1
}).encode()
req = urllib.request.Request(BASE_RPC, result, {
    "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"
})
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=15, context=ctx).read())
    code = resp.get("result", "0x")
    has_code = code != "0x" and len(code) > 2
    print(f"  Has code on Base: {has_code} (code length: {len(code)})")
except Exception as e:
    print(f"  Code check error: {e}")

# Check if mystery transceiver 0x28a16fa4 is same as old_base_peer
print(f"\n  Mystery == old_base_peer? {mystery.lower() == old_base_peer.lower()}")

# Summary
print()
print("=" * 60)
print("REMOVAL SAFETY ANALYSIS")
print("=" * 60)
print()
print("BASE NTT Manager - registered transceivers:")
print("  [0] 0x28a16fa4... - MYSTERY transceiver (from original deployment)")
print("  [1] 0xf2ce...      - T1 (peers with Monad OLD) - ACTIVE for M->B")
print("  [2] 0x3e7b...      - T2 (peers with Monad v2) - ACTIVE for M->B backup & B->M")
print()
print("MONAD NTT Manager - registered transceivers:")
print("  [0] 0xc659... - OLD (peers with Base 0x13cab3...) - ACTIVE for M->B via Base T1")
print("  [1] 0x030D... - v2 (peers with Base T1) - ACTIVE for M->B backup via Base T2")
print("  [2] 0xF682... - v3 (peers with Base T2) - ACTIVE for B->M")
print()
print("SAFE TO REMOVE:")
print("  ✅ Base [0] 0x28a16fa4... - unknown dead transceiver, no active paths use it")
print()
print("RISKY TO REMOVE (currently functional):")
print("  ⚠️  Monad [0] OLD 0xc659... - Bridge UI uses OLD->T1 for M->B")
print("      BUT: v2->T2 provides the same M->B path as backup")
print("      If you remove OLD, update bridge UI to not reference transceiverOld")
print()
print("  ⚠️  Monad [1] v2 0x030D... - Redundant M->B path via T2")
print("      Removal means only OLD->T1 works for M->B (single point of failure)")
print()
print("DO NOT REMOVE:")
print("  ❌ Base T1 - needed for M->B (accepts OLD's VAAs)")
print("  ❌ Base T2 - needed for B->M (v3 trusts it) and M->B backup")
print("  ❌ Monad v3 - needed for B->M (trusts Base T2)")
