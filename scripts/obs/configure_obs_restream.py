#!/usr/bin/env python3
"""Configure OBS for Restream multi-platform"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Configuring OBS for Restream (YouTube + Twitch + X)...")

try:
    ws.call(obs_requests.SetStreamServiceSettings(
        streamServiceType="rtmp_custom",
        streamServiceSettings={
            "server": "rtmp://live.restream.io/live",
            "key": "re_11127151_25c9f8629fc7e29f64d6"
        }
    ))

    print("[OK] OBS configured for Restream!")
    print("\nServer: rtmp://live.restream.io/live")
    print("Key: re_11127151_25c9f8629fc7e29f64d6")
    print("\n[SUCCESS] When you add YouTube/Twitch/X to Restream,")
    print("clicking 'Start Streaming' will go live on ALL platforms!")
    print("\n[ACTION] Click 'Start Streaming' in OBS NOW!")

except Exception as e:
    print(f"[ERROR] {e}")

ws.disconnect()
