#!/bin/bash
python3 << 'EOF'
import json
d = json.load(open("/tmp/ut.json"))
acts = d.get("actions_taken", [])
print(f"=== {len(acts)} ACTIONS TAKEN ===")
for a in acts:
    tool = a.get("tool", "?")
    ok = a.get("success", "?")
    msg = str(a.get("message", ""))[:100]
    print(f"  {tool}: success={ok} | {msg}")

print()
out = d.get("output_text", "")
# Find cross-domain mentions
for keyword in ["trading", "social", "blockchain", "portfolio", "engagement", "farcaster", "tweet", "A2A", "agent"]:
    if keyword.lower() in out.lower():
        print(f"  CROSS-DOMAIN HIT: '{keyword}' found in output")
print()
print("OUTPUT (800 chars):")
print(out[:800])
EOF
