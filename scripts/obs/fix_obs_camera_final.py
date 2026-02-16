#!/usr/bin/env python3
"""Fix OBS to use laptop camera, not Logitech"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Getting available video devices...")

# Get all available cameras
inputs_response = ws.call(obs_requests.GetInputList(inputKind="dshow_input"))

print("\n[*] Current camera sources:")
for item in inputs_response.getInputs():
    print(f"  - {item['inputName']}")

print("\n[*] Removing duplicate Logitech sources...")

# Remove all existing webcam sources to start fresh
for name in ["Laptop Webcam", "Your Webcam", "Laptop Camera"]:
    try:
        ws.call(obs_requests.RemoveInput(inputName=name))
        print(f"  Removed: {name}")
    except:
        pass

print("\n[*] Adding YOUR laptop's built-in camera...")

# Add fresh video capture device
# Windows will auto-select first available camera (not Logitech if we specify)
ws.call(obs_requests.CreateInput(
    sceneName="Main - Plant + You",
    inputName="You (Laptop Cam)",
    inputKind="dshow_input",
    inputSettings={
        # Leave device_id empty - Windows will use default (integrated camera)
    },
    sceneItemEnabled=True
))

# Get the item ID
item_id = ws.call(obs_requests.GetSceneItemId(
    sceneName="Main - Plant + You",
    sourceName="You (Laptop Cam)"
)).getSceneItemId()

# Position in bottom-right corner, small
ws.call(obs_requests.SetSceneItemTransform(
    sceneName="Main - Plant + You",
    sceneItemId=item_id,
    sceneItemTransform={
        "positionX": 1520.0,
        "positionY": 780.0,
        "scaleX": 0.3,
        "scaleY": 0.3,
        "alignment": 5  # Center
    }
))

print("[OK] Camera added and positioned!")

print("\n[ACTION NEEDED]")
print("In OBS, right-click 'You (Laptop Cam)' -> Properties")
print("Device dropdown: Select 'Integrated Camera' or 'HP TrueVision' (NOT Logitech)")
print("Click OK")
print("\nYou should see yourself!")

ws.disconnect()
