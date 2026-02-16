#!/usr/bin/env python3
"""Fix webcam in Triple View scene"""

from obswebsocket import obsws, requests as obs_requests

OBS_HOST = 'localhost'
OBS_PORT = 4455
OBS_PASSWORD = 'h2LDVnmFYDUpSVel'

ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
ws.connect()

print("Finding available video sources...\n")

# Get all inputs
inputs_response = ws.call(obs_requests.GetInputList())
inputs = inputs_response.getInputs()

print("Available video sources:")
for input_item in inputs:
    kind = input_item.get('inputKind', '')
    name = input_item.get('inputName', '')
    if 'video' in kind.lower() or 'camera' in kind.lower() or 'capture' in kind.lower():
        print(f"  - {name} ({kind})")

print("\nLooking for webcam sources...")
webcam_sources = []
for input_item in inputs:
    kind = input_item.get('inputKind', '')
    name = input_item.get('inputName', '')
    if 'dshow' in kind.lower() or 'v4l2' in kind.lower() or ('video' in kind.lower() and 'capture' in name.lower()):
        webcam_sources.append(name)
        print(f"  Found: {name}")

if webcam_sources:
    webcam_name = webcam_sources[0]
    print(f"\nUsing webcam: {webcam_name}")

    # Add to Triple View scene
    scene_name = "Guest: Triple View"
    try:
        ws.call(obs_requests.CreateSceneItem(
            sceneName=scene_name,
            sourceName=webcam_name,
            sceneItemEnabled=True
        ))
        print(f"[OK] Added {webcam_name} to {scene_name}")

        # Get the scene item ID
        response = ws.call(obs_requests.GetSceneItemId(
            sceneName=scene_name,
            sourceName=webcam_name
        ))
        item_id = response.getSceneItemId()

        # Position it on the left (first third)
        transform = {
            'positionX': 0,
            'positionY': 0,
            'scaleX': 640.0 / 1920.0,
            'scaleY': 1.0,
            'alignment': 5,
            'boundsType': 'OBS_BOUNDS_SCALE_INNER',
            'boundsWidth': 640,
            'boundsHeight': 1080,
        }

        ws.call(obs_requests.SetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=item_id,
            sceneItemTransform=transform
        ))
        print(f"[OK] Positioned webcam on left third")

    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print("\n[ERROR] No webcam sources found!")
    print("You may need to add a Video Capture Device in OBS first.")

ws.disconnect()
