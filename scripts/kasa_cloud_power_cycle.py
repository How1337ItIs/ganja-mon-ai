#!/usr/bin/env python3
"""Remote power cycle the Chromebook via Kasa cloud API.

Works from ANYWHERE — no LAN access needed. Uses TP-Link cloud to toggle
the smart plug the Chromebook is plugged into.

Usage:
    python scripts/kasa_cloud_power_cycle.py              # Power cycle (off 10s, back on)
    python scripts/kasa_cloud_power_cycle.py --status      # Check plug state
    python scripts/kasa_cloud_power_cycle.py --off         # Turn off only
    python scripts/kasa_cloud_power_cycle.py --on          # Turn on only
    python scripts/kasa_cloud_power_cycle.py --list        # List all plugs

Env vars:
    KASA_CLOUD_EMAIL, KASA_CLOUD_PASSWORD, KASA_CHROMEBOOK_DEVICE_ID
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

API_URL = "https://wap.tplinkcloud.com"
DEVICE_API_URL = "https://use1-wap.tplinkcloud.com"
TERMINAL_UUID = "grokmon-remote-admin-001"

POWER_CYCLE_OFF_SECONDS = 10


def api_call(url, payload):
    """Make a TP-Link cloud API call."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"API error: {e}")
        sys.exit(1)


def login(email, password):
    """Authenticate and return token."""
    result = api_call(API_URL, {
        "method": "login",
        "params": {
            "appType": "Kasa_Android",
            "cloudUserName": email,
            "cloudPassword": password,
            "terminalUUID": TERMINAL_UUID,
        }
    })
    if result.get("error_code") != 0:
        print(f"Login failed: {result.get('msg', 'unknown error')}")
        sys.exit(1)
    return result["result"]["token"]


def get_device_list(token):
    """List all devices on the account."""
    result = api_call(f"{DEVICE_API_URL}?token={token}", {
        "method": "getDeviceList"
    })
    return result.get("result", {}).get("deviceList", [])


def get_relay_state(token, device_id):
    """Get current relay state (on/off) of a plug."""
    result = api_call(f"{DEVICE_API_URL}?token={token}", {
        "method": "passthrough",
        "params": {
            "deviceId": device_id,
            "requestData": json.dumps({"system": {"get_sysinfo": {}}}),
        }
    })
    resp_data = json.loads(result["result"]["responseData"])
    info = resp_data["system"]["get_sysinfo"]
    return info


def set_relay_state(token, device_id, state):
    """Set relay state: 1=on, 0=off."""
    result = api_call(f"{DEVICE_API_URL}?token={token}", {
        "method": "passthrough",
        "params": {
            "deviceId": device_id,
            "requestData": json.dumps({
                "system": {"set_relay_state": {"state": state}}
            }),
        }
    })
    return result.get("error_code", -1) == 0


def main():
    email = os.getenv("KASA_CLOUD_EMAIL")
    password = os.getenv("KASA_CLOUD_PASSWORD")
    device_id = os.getenv("KASA_CHROMEBOOK_DEVICE_ID")

    if not email or not password:
        print("Set KASA_CLOUD_EMAIL and KASA_CLOUD_PASSWORD in .env")
        sys.exit(1)

    token = login(email, password)

    if "--list" in sys.argv:
        devices = get_device_list(token)
        for d in devices:
            print(f"  {d['alias']:10s} | {d['deviceId'][:20]}... | {d['deviceModel']} | status={d['status']}")
        return

    if not device_id:
        print("Set KASA_CHROMEBOOK_DEVICE_ID in .env")
        sys.exit(1)

    if "--status" in sys.argv:
        info = get_relay_state(token, device_id)
        state = "ON" if info["relay_state"] else "OFF"
        uptime = info.get("on_time", 0)
        print(f"Plug '{info['alias']}': {state} (uptime: {uptime}s, rssi: {info.get('rssi')}dBm)")
        return

    if "--off" in sys.argv:
        print("Turning OFF...")
        set_relay_state(token, device_id, 0)
        print("Plug is OFF. Chromebook will power down.")
        return

    if "--on" in sys.argv:
        print("Turning ON...")
        set_relay_state(token, device_id, 1)
        print("Plug is ON. Chromebook will boot.")
        return

    # Default: power cycle
    print(f"Power cycling Chromebook (off {POWER_CYCLE_OFF_SECONDS}s, then on)...")
    info = get_relay_state(token, device_id)
    if not info["relay_state"]:
        print("Plug is already OFF. Turning on...")
        set_relay_state(token, device_id, 1)
        print("Done. Chromebook should boot in ~60s.")
        return

    print("  Turning OFF...")
    set_relay_state(token, device_id, 0)
    print(f"  Waiting {POWER_CYCLE_OFF_SECONDS}s...")
    time.sleep(POWER_CYCLE_OFF_SECONDS)
    print("  Turning ON...")
    set_relay_state(token, device_id, 1)
    print("Done. Chromebook should boot and tunnels come up in ~90s.")


if __name__ == "__main__":
    main()
