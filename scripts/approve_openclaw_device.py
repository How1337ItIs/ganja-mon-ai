#!/usr/bin/env python3
"""Approve pending OpenClaw device pairing."""
import json
import uuid
import time

PENDING = "/home/natha/.openclaw/devices/pending.json"
PAIRED = "/home/natha/.openclaw/devices/paired.json"

# Read pending
with open(PENDING) as f:
    pending = json.load(f)

if not pending:
    print("No pending devices.")
    exit(0)

# Read existing paired (if any)
try:
    with open(PAIRED) as f:
        paired = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    paired = {}

# Move all pending entries to paired
for req_id, req in pending.items():
    token = str(uuid.uuid4())
    paired[req_id] = {
        "deviceId": req_id,
        "deviceName": req.get("hostname", "chromebook-cli"),
        "platform": req.get("platform", "linux"),
        "clientId": req.get("clientId", "cli"),
        "role": "operator",
        "roles": ["operator"],
        "scopes": req.get("scopes", ["operator.admin", "operator.approvals", "operator.pairing"]),
        "token": token,
        "pairedAt": int(time.time() * 1000),
    }
    print(f"Paired device {req_id} with token {token}")

# Write paired
with open(PAIRED, "w") as f:
    json.dump(paired, f, indent=2)

# Clear pending
with open(PENDING, "w") as f:
    json.dump({}, f, indent=2)

print("Done! Restart gateway for changes to take effect.")
