#!/usr/bin/env python3
"""
Setup OBS scenes for remote guest streaming via VDO.Ninja
Creates three scene layouts:
1. Side-by-Side (Plant + Guest)
2. Guest PiP (Picture-in-Picture overlay)
3. Triple View (Your cam + Plant + Guest)
"""

import sys
from obswebsocket import obsws, requests as obs_requests

OBS_HOST = 'localhost'
OBS_PORT = 4455
OBS_PASSWORD = 'h2LDVnmFYDUpSVel'

# Canvas size
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

def connect_obs():
    """Connect to OBS WebSocket"""
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
    try:
        ws.connect()
        print("[OK] Connected to OBS")
        return ws
    except Exception as e:
        print(f"[ERROR] Failed to connect to OBS: {e}")
        print("Make sure OBS is running and WebSocket server is enabled!")
        print("In OBS: Tools -> WebSocket Server Settings -> Enable WebSocket Server")
        sys.exit(1)

def create_scene_if_not_exists(ws, scene_name):
    """Create scene if it doesn't exist"""
    try:
        ws.call(obs_requests.CreateScene(sceneName=scene_name))
        print(f"[OK] Created scene: {scene_name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"  Scene already exists: {scene_name}")
        else:
            print(f"[ERROR] Error creating scene {scene_name}: {e}")

def add_browser_source(ws, scene_name, source_name, url, width, height, x, y):
    """Add a browser source to a scene"""
    try:
        # Create browser source input
        settings = {
            'url': url,
            'width': width,
            'height': height,
            'fps': 30,
            'reroute_audio': True,
            'restart_when_active': True,
            'shutdown': True
        }

        ws.call(obs_requests.CreateInput(
            sceneName=scene_name,
            inputName=source_name,
            inputKind='browser_source',
            inputSettings=settings,
            sceneItemEnabled=True
        ))
        print(f"  [OK] Added browser source: {source_name}")

        # Get the scene item ID
        response = ws.call(obs_requests.GetSceneItemId(
            sceneName=scene_name,
            sourceName=source_name
        ))
        item_id = response.getSceneItemId()

        # Set position and size
        transform = {
            'positionX': x,
            'positionY': y,
            'scaleX': 1.0,
            'scaleY': 1.0,
            'alignment': 5,  # Center
            'boundsType': 'OBS_BOUNDS_NONE',
            'boundsWidth': width,
            'boundsHeight': height,
        }

        ws.call(obs_requests.SetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=item_id,
            sceneItemTransform=transform
        ))

    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"  Source already exists: {source_name}")
        else:
            print(f"  [ERROR] Error adding browser source: {e}")

def add_existing_source(ws, scene_name, source_name, x, y, width, height):
    """Add an existing source to a scene with positioning"""
    try:
        ws.call(obs_requests.CreateSceneItem(
            sceneName=scene_name,
            sourceName=source_name,
            sceneItemEnabled=True
        ))
        print(f"  [OK] Added source: {source_name}")

        # Get the scene item ID
        response = ws.call(obs_requests.GetSceneItemId(
            sceneName=scene_name,
            sourceName=source_name
        ))
        item_id = response.getSceneItemId()

        # Calculate scale based on desired size
        # Assuming source is 1920x1080, calculate scale needed
        scale_x = width / 1920.0
        scale_y = height / 1080.0

        # Set position and size
        transform = {
            'positionX': x,
            'positionY': y,
            'scaleX': scale_x,
            'scaleY': scale_y,
            'alignment': 5,  # Center
            'boundsType': 'OBS_BOUNDS_SCALE_INNER',
            'boundsWidth': width,
            'boundsHeight': height,
        }

        ws.call(obs_requests.SetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=item_id,
            sceneItemTransform=transform
        ))

    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"  Source already in scene: {source_name}")
        else:
            print(f"  [ERROR] Error adding source: {e}")

def setup_side_by_side_scene(ws):
    """Create Side-by-Side scene: Plant (left) + Guest (right)"""
    scene_name = "Guest: Side-by-Side"
    print(f"\nCreating {scene_name}...")

    create_scene_if_not_exists(ws, scene_name)

    # Plant cam - left half
    add_existing_source(
        ws, scene_name,
        source_name="Mon Plant Cam",  # Assuming this exists from CLAUDE.md
        x=0, y=0,
        width=960, height=1080
    )

    # Guest cam - right half (VDO.Ninja placeholder)
    add_browser_source(
        ws, scene_name,
        source_name="Guest Camera (VDO.Ninja)",
        url="https://vdo.ninja/?view=PASTE_YOUR_VIEW_ID_HERE",
        width=960, height=1080,
        x=960, y=0
    )

    # Sensor bar at bottom
    add_existing_source(
        ws, scene_name,
        source_name="Sensor Bar",
        x=0, y=980,
        width=1920, height=100
    )

def setup_pip_scene(ws):
    """Create Picture-in-Picture scene: Plant fullscreen + Guest overlay"""
    scene_name = "Guest: PiP Overlay"
    print(f"\nCreating {scene_name}...")

    create_scene_if_not_exists(ws, scene_name)

    # Plant cam - fullscreen background
    add_existing_source(
        ws, scene_name,
        source_name="Mon Plant Cam",
        x=0, y=0,
        width=1920, height=1080
    )

    # Guest cam - small overlay bottom-right
    add_browser_source(
        ws, scene_name,
        source_name="Guest Camera PiP",
        url="https://vdo.ninja/?view=PASTE_YOUR_VIEW_ID_HERE",
        width=480, height=360,
        x=1400, y=680
    )

    # Sensor bar at bottom
    add_existing_source(
        ws, scene_name,
        source_name="Sensor Bar",
        x=0, y=980,
        width=1920, height=100
    )

def setup_triple_scene(ws):
    """Create Triple View scene: Your cam + Plant + Guest"""
    scene_name = "Guest: Triple View"
    print(f"\nCreating {scene_name}...")

    create_scene_if_not_exists(ws, scene_name)

    # Each camera gets 1/3 width = 640px
    third_width = 640

    # Your laptop webcam - left
    add_existing_source(
        ws, scene_name,
        source_name="Video Capture Device",  # Default webcam source name
        x=0, y=0,
        width=third_width, height=1080
    )

    # Plant cam - center
    add_existing_source(
        ws, scene_name,
        source_name="Mon Plant Cam",
        x=third_width, y=0,
        width=third_width, height=1080
    )

    # Guest cam - right
    add_browser_source(
        ws, scene_name,
        source_name="Guest Camera Triple",
        url="https://vdo.ninja/?view=PASTE_YOUR_VIEW_ID_HERE",
        width=third_width, height=1080,
        x=third_width * 2, y=0
    )

    # Sensor bar at bottom
    add_existing_source(
        ws, scene_name,
        source_name="Sensor Bar",
        x=0, y=980,
        width=1920, height=100
    )

def main():
    print("=" * 60)
    print("OBS Guest Streaming Setup")
    print("=" * 60)

    ws = connect_obs()

    try:
        # Create all three scenes
        setup_side_by_side_scene(ws)
        setup_pip_scene(ws)
        setup_triple_scene(ws)

        print("\n" + "=" * 60)
        print("[OK] Setup complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Go to https://vdo.ninja/?director=GanjaMonStream")
        print("2. Click 'Invite Guests' and send link to your friend")
        print("3. Copy the 'View Stream' link")
        print("4. In OBS, edit these sources and paste the VDO.Ninja view link:")
        print("   - 'Guest Camera (VDO.Ninja)' in 'Guest: Side-by-Side' scene")
        print("   - 'Guest Camera PiP' in 'Guest: PiP Overlay' scene")
        print("   - 'Guest Camera Triple' in 'Guest: Triple View' scene")
        print("\n5. Test by switching between scenes in OBS!")

    except Exception as e:
        print(f"\n[ERROR] Error during setup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ws.disconnect()
        print("\nDisconnected from OBS")

if __name__ == "__main__":
    main()
