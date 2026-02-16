#!/usr/bin/env python3
"""Configure OBS for YouTube streaming"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Configuring OBS for YouTube streaming...")

try:
    # Set stream settings for YouTube
    ws.call(obs_requests.SetStreamServiceSettings(
        streamServiceType="rtmp_common",
        streamServiceSettings={
            "service": "YouTube - RTMPS",
            "server": "rtmp://a.rtmp.youtube.com/live2",
            "key": "v5rm-w77f-qp9c-2yue-2e71"
        }
    ))

    print("[OK] YouTube stream configured!")
    print("\nServer: rtmp://a.rtmp.youtube.com/live2")
    print("Ready to go live!")
    print("\nNow click 'Start Streaming' in OBS!")

except Exception as e:
    print(f"[ERROR] {e}")
    print("\nManual setup:")
    print("1. OBS -> Settings -> Stream")
    print("2. Service: YouTube - RTMPS")
    print("3. Server: rtmp://a.rtmp.youtube.com/live2")
    print("4. Stream Key: [paste from YouTube]")
    print("5. Apply -> OK")

ws.disconnect()
