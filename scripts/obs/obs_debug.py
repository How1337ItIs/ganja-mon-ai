#!/usr/bin/env python3
"""Debug OBS - show current scene and all sources"""

from obswebsocket import obsws, requests as obs_requests

WS_HOST = "localhost"
WS_PORT = 4455
WS_PASSWORD = "h2LDVnmFYDUpSVel"

def debug_obs():
    print("[*] Connecting to OBS...")
    ws = obsws(WS_HOST, WS_PORT, WS_PASSWORD)
    ws.connect()
    print("[OK] Connected!\n")
    
    # Get current scene
    current = ws.call(obs_requests.GetCurrentProgramScene())
    current_scene = current.getSceneName()
    print(f"=== CURRENT SCENE: {current_scene} ===\n")
    
    # List all scenes
    scenes = ws.call(obs_requests.GetSceneList())
    print("ALL SCENES:")
    for scene in scenes.getScenes():
        marker = " <-- ACTIVE" if scene['sceneName'] == current_scene else ""
        print(f"  - {scene['sceneName']}{marker}")
    
    # List sources in current scene
    print(f"\nSOURCES IN '{current_scene}':")
    items = ws.call(obs_requests.GetSceneItemList(sceneName=current_scene))
    for item in items.getSceneItemList():
        enabled = "✓" if item.get('sceneItemEnabled', True) else "✗"
        print(f"  [{enabled}] {item['sourceName']} (ID: {item['sceneItemId']})")
    
    # Check if our browser source exists anywhere
    print("\n[*] Searching for 'Grok and Mon Website' source...")
    try:
        settings = ws.call(obs_requests.GetInputSettings(inputName="Grok and Mon Website"))
        print(f"  Found! URL: {settings.getInputSettings().get('url', 'N/A')}")
    except:
        print("  NOT FOUND as a global input")
    
    ws.disconnect()
    print("\n[OK] Done")

if __name__ == "__main__":
    debug_obs()
