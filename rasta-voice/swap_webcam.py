#!/usr/bin/env python3
"""Replace You Left with You in Triple View scene"""

from obswebsocket import obsws, requests as obs_requests

ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel')
ws.connect()

scene_name = "Guest: Triple View"

# Remove "You Left"
try:
    response = ws.call(obs_requests.GetSceneItemId(
        sceneName=scene_name,
        sourceName="You Left"
    ))
    item_id = response.getSceneItemId()

    ws.call(obs_requests.RemoveSceneItem(
        sceneName=scene_name,
        sceneItemId=item_id
    ))
    print("[OK] Removed 'You Left'")
except Exception as e:
    print(f"Could not remove 'You Left': {e}")

# Add "You"
try:
    ws.call(obs_requests.CreateSceneItem(
        sceneName=scene_name,
        sourceName="You",
        sceneItemEnabled=True
    ))
    print("[OK] Added 'You'")

    # Get the new item ID
    response = ws.call(obs_requests.GetSceneItemId(
        sceneName=scene_name,
        sourceName="You"
    ))
    item_id = response.getSceneItemId()

    # Position on left third
    transform = {
        'positionX': 0.0,
        'positionY': 0.0,
        'alignment': 5,
        'boundsType': 'OBS_BOUNDS_SCALE_INNER',
        'boundsAlignment': 0,
        'boundsWidth': 640.0,
        'boundsHeight': 1080.0,
    }

    ws.call(obs_requests.SetSceneItemTransform(
        sceneName=scene_name,
        sceneItemId=item_id,
        sceneItemTransform=transform
    ))
    print("[OK] Positioned 'You' on left third (640x1080)")

except Exception as e:
    print(f"Error adding 'You': {e}")

ws.disconnect()
