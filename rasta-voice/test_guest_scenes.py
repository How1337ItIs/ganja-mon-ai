#!/usr/bin/env python3
"""Test the guest streaming scenes in OBS"""

from obswebsocket import obsws, requests as obs_requests

OBS_HOST = 'localhost'
OBS_PORT = 4455
OBS_PASSWORD = 'h2LDVnmFYDUpSVel'

def test_scenes():
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
    ws.connect()
    print("Connected to OBS\n")

    scenes = [
        "Guest: Side-by-Side",
        "Guest: PiP Overlay",
        "Guest: Triple View"
    ]

    for scene_name in scenes:
        print(f"Testing scene: {scene_name}")

        # Switch to scene
        ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))
        print(f"  [OK] Switched to {scene_name}")

        # Get scene items
        try:
            response = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
            items = response.getSceneItems()
            print(f"  [OK] Scene has {len(items)} sources:")
            for item in items:
                source_name = item.get('sourceName', 'Unknown')
                enabled = item.get('sceneItemEnabled', False)
                status = "[ON]" if enabled else "[OFF]"
                print(f"      {status} {source_name}")
        except Exception as e:
            print(f"  [ERROR] Could not get scene items: {e}")

        print()

    # Get current scene
    current = ws.call(obs_requests.GetCurrentProgramScene())
    print(f"Current scene: {current.getCurrentProgramSceneName()}")

    ws.disconnect()

if __name__ == "__main__":
    test_scenes()
