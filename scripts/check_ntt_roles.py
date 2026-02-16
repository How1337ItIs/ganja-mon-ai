"""Check NTT contract roles before multisig migration."""
import urllib.request
import json
import ssl

# Disable SSL verification for simplicity
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def eth_call(rpc_url, to, data, label=""):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "eth_call", 
        "params": [{"to": to, "data": data}, "latest"],
        "id": 1
    }).encode()
    req = urllib.request.Request(rpc_url, payload, {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        result = json.loads(resp.read())
        if "result" in result:
            return result["result"]
        else:
            return f"ERROR: {result.get('error', 'unknown')}"
    except Exception as e:
        return f"ERROR: {e}"

# Function selectors
OWNER = "0x8da5cb5b"          # owner()
PAUSER = "0x9fd0506d"         # pauser()  
TOTAL_SUPPLY = "0x18160ddd"   # totalSupply()
# isPaused selector = keccak256("isPaused()") = 0xb187bd26
IS_PAUSED = "0xb187bd26"

BASE_RPC = "https://base-mainnet.g.alchemy.com/v2/demo"
# Fallback RPCs
BASE_RPCS = [
    "https://base-mainnet.g.alchemy.com/v2/demo",
    "https://base.llamarpc.com",
    "https://base-rpc.publicnode.com",
]
MONAD_RPCS = [
    "https://rpc.monad.xyz/monad",
    "https://monad.drpc.org",
]

def try_rpcs(rpcs, to, data, label=""):
    for rpc in rpcs:
        result = eth_call(rpc, to, data, label)
        if not result.startswith("ERROR"):
            return result
    return result  # Return last error

# Contract addresses
BASE_NTT_MANAGER = "0xAED180F30c5bd9EBE5399271999bf72E843a1E09"
BASE_MON_TOKEN = "0xE390612D7997B538971457cfF29aB4286cE97BE2"
MONAD_NTT_MANAGER = "0x81D87a80B2121763e035d0539b8Ad39777258396"

print("=" * 60)
print("NTT CONTRACT ROLE AUDIT")
print("=" * 60)

print("\n--- BASE NTT Manager ---")
r = try_rpcs(BASE_RPCS, BASE_NTT_MANAGER, OWNER)
if not r.startswith("ERROR"):
    print(f"  Owner:  0x{r[-40:]}")
else:
    print(f"  Owner:  {r}")

r = try_rpcs(BASE_RPCS, BASE_NTT_MANAGER, PAUSER)
if not r.startswith("ERROR"):
    addr = r[-40:]
    is_zero = all(c == '0' for c in addr)
    print(f"  Pauser: 0x{addr}" + (" ⚠️  (ZERO ADDRESS - no pauser set!)" if is_zero else ""))
else:
    print(f"  Pauser: {r}")

r = try_rpcs(BASE_RPCS, BASE_NTT_MANAGER, IS_PAUSED)
if not r.startswith("ERROR"):
    paused = int(r, 16) != 0
    print(f"  Paused: {paused}")

print("\n--- BASE MON Token ---")
r = try_rpcs(BASE_RPCS, BASE_MON_TOKEN, OWNER)
if not r.startswith("ERROR"):
    print(f"  Owner:  0x{r[-40:]}")
else:
    print(f"  Owner:  {r}")

r = try_rpcs(BASE_RPCS, BASE_MON_TOKEN, TOTAL_SUPPLY)
if not r.startswith("ERROR"):
    supply = int(r, 16)
    print(f"  Supply: {supply / 10**18:,.2f} MON (on Base)")
else:
    print(f"  Supply: {r}")

print("\n--- MONAD NTT Manager ---")
r = try_rpcs(MONAD_RPCS, MONAD_NTT_MANAGER, OWNER)
if not r.startswith("ERROR"):
    print(f"  Owner:  0x{r[-40:]}")
else:
    print(f"  Owner:  {r}")

r = try_rpcs(MONAD_RPCS, MONAD_NTT_MANAGER, PAUSER)
if not r.startswith("ERROR"):
    addr = r[-40:]
    is_zero = all(c == '0' for c in addr)
    print(f"  Pauser: 0x{addr}" + (" ⚠️  (ZERO ADDRESS - no pauser set!)" if is_zero else ""))
else:
    print(f"  Pauser: {r}")

r = try_rpcs(MONAD_RPCS, MONAD_NTT_MANAGER, IS_PAUSED)
if not r.startswith("ERROR"):
    paused = int(r, 16) != 0
    print(f"  Paused: {paused}")

print("\n" + "=" * 60)
print("Your EOA: 0x794c94f1b5e455c1dba27bb28c6085db0fe544f9")
print("(from earlier successful Base query)")
print("=" * 60)
