#!/usr/bin/env python3
"""Fix camera sources in OBS"""
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

try:
    print("[*] Getting current sources...")

    # List all inputs in the Main scene
    items = ws.call(obs_requests.GetSceneItemList(sceneName="Main - Plant + You"))
    print(f"\nCurrent sources in Main scene:")
    for item in items.getSceneItems():
        print(f"  - {item['sourceName']}")

    print("\n[*] Removing 'Your Webcam' (Logitech duplicate)...")
    try:
        ws.call(obs_requests.RemoveInput(inputName="Your Webcam"))
        print("[OK] Removed!")
    except:
        print("[SKIP] Not found")

    print("\n[*] Adding your LAPTOP camera...")

    # Create video capture device (will auto-select first available)
    ws.call(obs_requests.CreateInput(
        sceneName="Main - Plant + You",
        inputName="Laptop Camera",
        inputKind="dshow_input",
        inputSettings={
            "video_device_id": ""  # Empty = first non-Logitech camera
        },
        sceneItemEnabled=True
    ))

    # Position in corner
    item_id = ws.call(obs_requests.GetSceneItemId(
        sceneName="Main - Plant + You",
        sourceName="Laptop Camera"
    )).getSceneItemId()

    ws.call(obs_requests.SetSceneItemTransform(
        sceneName="Main - Plant + You",
        sceneItemId=item_id,
        sceneItemTransform={
            "positionX": 1520.0,
            "positionY": 780.0,
            "scaleX": 0.3,
            "scaleY": 0.3
        }
    ))

    print("[OK] Laptop camera added and positioned!")
    print("\n[SUCCESS] Check OBS - you should see yourself in corner now!")
    print("\nIf still showing wrong camera:")
    print("  Right-click 'Laptop Camera' -> Properties -> Select correct device")

except Exception as e:
    print(f"[ERROR] {e}")

ws.disconnect()
