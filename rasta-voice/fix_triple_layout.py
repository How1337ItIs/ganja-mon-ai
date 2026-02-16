#!/usr/bin/env python3
"""Fix Triple View layout with proper positioning"""

from obswebsocket import obsws, requests as obs_requests

ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel')
ws.connect()

scene_name = "Guest: Triple View"

# Get scene items
response = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
items = response.getSceneItems()

# Create a mapping of source names to item IDs
sources = {}
for item in items:
    name = item.get('sourceName', '')
    item_id = item.get('sceneItemId', -1)
    sources[name] = item_id

print(f"Fixing layout for {scene_name}...\n")

# Define the layout: each column is 640px wide
layouts = [
    ("You Left", 0, 0, 640, 1080),      # Left column - your cam
    ("Mon Plant Cam", 640, 0, 640, 1080),   # Middle column - plant
    ("Guest Camera Triple", 1280, 0, 640, 1080),  # Right column - guest
    ("Sensor Bar", 0, 980, 1920, 100),  # Bottom overlay
]

for source_name, x, y, width, height in layouts:
    if source_name in sources:
        item_id = sources[source_name]

        transform = {
            'positionX': float(x),
            'positionY': float(y),
            'alignment': 5,  # Center
            'boundsType': 'OBS_BOUNDS_SCALE_INNER',
            'boundsAlignment': 0,
            'boundsWidth': float(width),
            'boundsHeight': float(height),
        }

        try:
            ws.call(obs_requests.SetSceneItemTransform(
                sceneName=scene_name,
                sceneItemId=item_id,
                sceneItemTransform=transform
            ))
            print(f"[OK] {source_name:20s} -> [{x:4d}, {y:4d}] {width}x{height}")
        except Exception as e:
            print(f"[ERROR] {source_name}: {e}")
    else:
        print(f"[SKIP] {source_name} not found in scene")

ws.disconnect()
print("\nLayout fixed!")
