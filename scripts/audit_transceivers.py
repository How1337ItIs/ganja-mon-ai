"""Query on-chain transceiver peer relationships to verify which pairs are valid."""
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
        return f"ERROR: {result.get('error', 'empty result')}"
    except Exception as e:
        return f"ERROR: {e}"

# getWormholePeer(uint16 chainId) -> bytes32
# selector: keccak256("getWormholePeer(uint16)")[:4]
# We need to compute this - let's use a known selector
# Actually for NTT: getWormholePeer(uint16) = 0x1a90a219
import hashlib
sig = "getWormholePeer(uint16)"
# keccak256 - ethers uses keccak but Python doesn't have it natively
# Let's try the actual function - for Wormhole NTT transceivers
# The selector from the codebase: we know setWormholePeer is 0x7ab56403
# Let's compute getWormholePeer manually

# Use pysha3 or fallback
try:
    import sha3
    selector = sha3.keccak_256(sig.encode()).hexdigest()[:8]
except ImportError:
    # Fallback: try hashlib (Python 3.11+)
    try:
        h = hashlib.new('sha3_256')  # Note: Ethereum uses keccak256, NOT sha3_256
        # They're different! We need to hardcode the selector.
        selector = None
    except:
        selector = None

# Known selectors for Wormhole NTT:
# getWormholePeer(uint16) - let's try common ones
# Actually, from the Wormhole NTT source, the function is in WormholeTransceiver
# Let me just encode the chain ID and try the call with the right selector

# The interface is: function getWormholePeer(uint16 peerChainId) external view returns (bytes32)
# Let's compute via node.js or just try common selectors
# From ethers: ethers.id("getWormholePeer(uint16)").slice(0,10) = ???

# Let's just try to call it with different approaches

BASE_RPC = "https://base-rpc.publicnode.com"
MONAD_RPC = "https://monad.drpc.org"

# Monad chain ID in Wormhole = 48 = 0x0030
# Base chain ID in Wormhole = 30 = 0x001e

# First, let's check which transceivers are registered on each NTT Manager
# getTransceivers() -> address[]

# Try to get raw storage or use getTransceivers() 

# Let's try a different approach - check the NTT Manager's registered transceivers
# The function might be called differently in the NoRateLimiting variant
# Let's check: getTransceivers() returns an array

# Instead, let's check if each transceiver is registered by calling isTransceiverRegistered  
# or just try removeTransceiver to see what's there

# Actually simplest: call the NTT Manager and check if a specific transceiver is enabled
# function isTransceiver(address) -> bool
# Or get all at once

# For NTT v1.x: getTransceivers() -> address[]
# Selector for getTransceivers(): 0x9bd38e84

print("=" * 60)
print("TRANSCEIVER AUDIT")
print("=" * 60)

# getTransceivers selector - let me compute via simple method
# We need keccak256, but Python's hashlib has sha3_256 which is NOT keccak256
# They diverge after the padding. Let's just hardcode selectors we know:

# Call with these known selectors
# getTransceivers() - no args
# Let's try a few possible selectors
possible_selectors = {
    "getTransceivers()": "0x02b4e956",  # Guess 1
}

# Actually, let me just encode it properly. The Wormhole NTT uses:
# function getRegisteredTransceivers() external view returns (address[])
# OR
# function getTransceivers() external view returns (Transceiver[] memory)

# Let me try calling with the ABI from the bridge code
# The bridge code uses NTT_ABI which has 'transfer' and 'quoteDeliveryPrice'
# But not getTransceivers

# Alternative approach: just check the peer relationship via getWormholePeer
# on each transceiver directly

# For the peer check, I know from the codebase that setWormholePeer selector is 0x7ab56403
# getWormholePeer would be a view function. Let me try calling the transceivers
# with the peer query for the opposite chain

# Encoding: getWormholePeer(uint16 chainId) where chainId is padded to 32 bytes
# For Monad (48 = 0x30): 0x + selector + 0000000000000000000000000000000000000000000000000000000000000030
# For Base (30 = 0x1e): 0x + selector + 000000000000000000000000000000000000000000000000000000000000001e

# Let me try various selectors for getWormholePeer(uint16)
# keccak256("getWormholePeer(uint16)") - I'll try to compute it

# Use the pycryptodome approach if available  
try:
    from Crypto.Hash import keccak
    k = keccak.new(digest_bits=256)
    k.update(b"getWormholePeer(uint16)")
    sel_peer = k.hexdigest()[:8]
    print(f"getWormholePeer selector: 0x{sel_peer}")
    
    k2 = keccak.new(digest_bits=256)
    k2.update(b"getTransceivers()")
    sel_trans = k2.hexdigest()[:8]
    print(f"getTransceivers selector: 0x{sel_trans}")
except ImportError:
    # Hardcode: try the most likely selectors
    # From Wormhole NTT source on GitHub, getWormholePeer(uint16) selector
    # Let's just try calling with data that's the function signature
    # We can compute keccak using the Web3 way via external call
    print("No keccak library, computing via node.js...")
    import subprocess
    try:
        result = subprocess.run(
            ["node", "-e", 
             "const{keccak256,toUtf8Bytes}=require('ethers');console.log(keccak256(toUtf8Bytes('getWormholePeer(uint16)')).slice(0,10));console.log(keccak256(toUtf8Bytes('getTransceivers()')).slice(0,10))"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split('\n')
        sel_peer = lines[0][2:]  # Remove 0x
        sel_trans = lines[1][2:]
        print(f"getWormholePeer selector: 0x{sel_peer}")
        print(f"getTransceivers selector: 0x{sel_trans}")
    except Exception as e:
        print(f"Fallback failed: {e}")
        # Last resort hardcoded values from Wormhole source
        sel_peer = "1a90a219"
        sel_trans = "02b4e956"
        print(f"Using hardcoded selectors: peer=0x{sel_peer}, trans=0x{sel_trans}")

# Query peers
MONAD_WORMHOLE_ID = "0030"  # 48
BASE_WORMHOLE_ID = "001e"   # 30

monad_transceivers = {
    "OLD": "0xc659d68acfd464cb2399a0e9b857f244422e809d",
    "v2": "0x030D72714Df3cE0E83956f8a29Dd435A0DB89123",
    "v3": "0xF682dd650aDE9B5d550041C7502E7A3fc1A1B74A",
}

base_transceivers = {
    "T1": "0xf2ce259C1Ff7E517F8B5aC9ECF86c29de54FC1E4",
    "T2": "0x3e7bFF16795b96eABeC56A4aA2a26bb0BE488C2D",
}

print("\n--- Monad Transceivers -> What Base peer do they point to? ---")
for name, addr in monad_transceivers.items():
    # Query: getWormholePeer(30) on Monad
    call_data = f"0x{sel_peer}" + BASE_WORMHOLE_ID.zfill(64)
    result = eth_call(MONAD_RPC, addr, call_data)
    if not result.startswith("ERROR"):
        peer = "0x" + result[-40:]
        is_zero = all(c == '0' for c in result[2:])
        if is_zero:
            print(f"  {name} ({addr[:10]}...): NO PEER SET (empty)")
        else:
            print(f"  {name} ({addr[:10]}...): peers with Base {peer}")
    else:
        print(f"  {name} ({addr[:10]}...): {result}")

print("\n--- Base Transceivers -> What Monad peer do they point to? ---")
for name, addr in base_transceivers.items():
    # Query: getWormholePeer(48) on Base
    call_data = f"0x{sel_peer}" + MONAD_WORMHOLE_ID.zfill(64)
    result = eth_call(BASE_RPC, addr, call_data)
    if not result.startswith("ERROR"):
        peer = "0x" + result[-40:]
        is_zero = all(c == '0' for c in result[2:])
        if is_zero:
            print(f"  {name} ({addr[:10]}...): NO PEER SET (empty)")
        else:
            print(f"  {name} ({addr[:10]}...): peers with Monad {peer}")
    else:
        print(f"  {name} ({addr[:10]}...): {result}")

# Now check registered transceivers on the NTT Managers
print("\n--- NTT Manager Registered Transceivers ---")

# Base NTT Manager
call_data = f"0x{sel_trans}"
result = eth_call(BASE_RPC, "0xAED180F30c5bd9EBE5399271999bf72E843a1E09", call_data)
if not result.startswith("ERROR"):
    # Decode dynamic array: offset (32 bytes) + length (32 bytes) + addresses
    hex_data = result[2:]  # Remove 0x
    if len(hex_data) >= 128:
        offset = int(hex_data[:64], 16)
        data_start = offset * 2
        length = int(hex_data[data_start:data_start+64], 16)
        print(f"  Base NTT Manager has {length} registered transceivers:")
        for i in range(length):
            addr_hex = hex_data[data_start+64+i*64:data_start+64+(i+1)*64]
            addr = "0x" + addr_hex[-40:]
            print(f"    [{i}] {addr}")
    else:
        print(f"  Raw result: {result[:100]}...")
else:
    print(f"  Base NTT Manager: {result}")

# Monad NTT Manager
result = eth_call(MONAD_RPC, "0x81D87a80B2121763e035d0539b8Ad39777258396", call_data)
if not result.startswith("ERROR"):
    hex_data = result[2:]
    if len(hex_data) >= 128:
        offset = int(hex_data[:64], 16)
        data_start = offset * 2
        length = int(hex_data[data_start:data_start+64], 16)
        print(f"  Monad NTT Manager has {length} registered transceivers:")
        for i in range(length):
            addr_hex = hex_data[data_start+64+i*64:data_start+64+(i+1)*64]
            addr = "0x" + addr_hex[-40:]
            print(f"    [{i}] {addr}")
    else:
        print(f"  Raw result: {result[:100]}...")
else:
    print(f"  Monad NTT Manager: {result}")

print("\n" + "=" * 60)
