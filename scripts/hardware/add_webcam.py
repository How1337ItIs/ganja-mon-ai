#!/usr/bin/env python3
"""Add laptop webcam to OBS"""
import sys
from obswebsocket import obsws, requests as obs_requests

WS_HOST = "localhost"
WS_PORT = 4455
WS_PASSWORD = "h2LDVnmFYDUpSVel"

print("[*] Connecting to OBS...")
ws = obsws(WS_HOST, WS_PORT, WS_PASSWORD)
ws.connect()
print("[OK] Connected!")

try:
    # Get available input kinds
    print("\n[*] Checking available camera types...")
    kinds = ws.call(obs_requests.GetInputKindList())
    print(f"Available kinds: {kinds.getInputKinds()[:10]}")

    # Try to add webcam to Main scene
    print("\n[*] Adding laptop webcam to 'Main - Plant + You' scene...")

    # Windows uses "dshow_input" for cameras
    ws.call(obs_requests.CreateInput(
        sceneName="Main - Plant + You",
        inputName="Your Webcam",
        inputKind="dshow_input",
        inputSettings={},
        sceneItemEnabled=True
    ))

    print("[OK] Webcam added!")

    # Get the scene item ID so we can position it
    print("[*] Positioning webcam in corner...")
    item_id = ws.call(obs_requests.GetSceneItemId(
        sceneName="Main - Plant + You",
        sourceName="Your Webcam"
    )).getSceneItemId()

    # Move to bottom-right corner and make smaller
    ws.call(obs_requests.SetSceneItemTransform(
        sceneName="Main - Plant + You",
        sceneItemId=item_id,
        sceneItemTransform={
            "positionX": 1520.0,
            "positionY": 780.0,
            "scaleX": 0.25,
            "scaleY": 0.25,
            "boundsWidth": 400.0,
            "boundsHeight": 300.0
        }
    ))

    print("[OK] Webcam positioned in bottom-right corner!")
    print("\n[SUCCESS] Your camera is now in the Main scene!")
    print("\nCheck OBS - you should see yourself in the corner!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

ws.disconnect()
print("[*] Done!")
