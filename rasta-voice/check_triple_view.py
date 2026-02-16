#!/usr/bin/env python3
"""Check Triple View scene layout"""

from obswebsocket import obsws, requests as obs_requests

ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel')
ws.connect()

scene_name = "Guest: Triple View"
print(f"Scene: {scene_name}\n")

# Switch to it
ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))

# Get items
response = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
items = response.getSceneItems()

print(f"Sources in scene ({len(items)} total):")
for item in items:
    name = item.get('sourceName', 'Unknown')
    item_id = item.get('sceneItemId', -1)

    # Get transform
    transform_response = ws.call(obs_requests.GetSceneItemTransform(
        sceneName=scene_name,
        sceneItemId=item_id
    ))
    transform = transform_response.getSceneItemTransform()

    x = transform.get('positionX', 0)
    y = transform.get('positionY', 0)
    width = transform.get('width', 0)

    print(f"  [{int(x):4d}, {int(y):4d}] - {name} (width: {int(width)}px)")

print("\nExpected layout:")
print("  [   0,    0] - Your webcam (640px)")
print("  [ 640,    0] - Plant cam (640px)")
print("  [1280,    0] - Guest cam (640px)")
print("  [   0,  980] - Sensor bar (1920px)")

ws.disconnect()
