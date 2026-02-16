#!/usr/bin/env python3
"""
Add Window Capture of browser to OBS
This captures your ACTUAL browser window so you can interact with it
"""

from obswebsocket import obsws, requests as obs_requests

WS_HOST = "localhost"
WS_PORT = 4455
WS_PASSWORD = "h2LDVnmFYDUpSVel"

SOURCE_NAME = "BrowserWindowCapture"

def add_window_capture():
    print("[*] Connecting to OBS...")
    ws = obsws(WS_HOST, WS_PORT, WS_PASSWORD)
    ws.connect()
    print("[OK] Connected!\n")
    
    # Get current scene
    current = ws.call(obs_requests.GetCurrentProgramScene())
    current_scene = current.getSceneName()
    print(f"Current scene: {current_scene}\n")
    
    # Remove old browser source if exists
    try:
        ws.call(obs_requests.RemoveInput(inputName="GrokMonWebsite"))
        print("[*] Removed old browser source")
    except:
        pass
    
    # Create Window Capture source
    print(f"[*] Creating window capture '{SOURCE_NAME}'...")
    try:
        result = ws.call(obs_requests.CreateInput(
            sceneName=current_scene,
            inputName=SOURCE_NAME,
            inputKind="window_capture",  # Window capture, not browser
            inputSettings={
                "cursor": True,  # Show mouse cursor
                "method": 2,     # Windows 10+ optimized
            }
        ))
        print(f"[OK] Created window capture!")
        print("\n" + "="*50)
        print("NEXT STEPS:")
        print("="*50)
        print("1. Open Chrome/Edge and go to grokandmon.com")
        print("2. In OBS Sources, right-click 'BrowserWindowCapture'")
        print("3. Click 'Properties'")
        print("4. In 'Window' dropdown, select your browser window")
        print("5. Click OK")
        print("\nNow you can control the browser and viewers see it!")
        print("="*50)
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"[!] Window capture already exists")
            print("    Just configure it in OBS Properties")
        else:
            print(f"[X] Error: {e}")
    
    # Position it
    try:
        item_id_result = ws.call(obs_requests.GetSceneItemId(
            sceneName=current_scene,
            sourceName=SOURCE_NAME
        ))
        item_id = item_id_result.getSceneItemId()
        
        ws.call(obs_requests.SetSceneItemEnabled(
            sceneName=current_scene,
            sceneItemId=item_id,
            sceneItemEnabled=True
        ))
        
        ws.call(obs_requests.SetSceneItemTransform(
            sceneName=current_scene,
            sceneItemId=item_id,
            sceneItemTransform={
                "positionX": 1350,
                "positionY": 30,
                "scaleX": 0.35,
                "scaleY": 0.35
            }
        ))
        print("\n[OK] Positioned in top-right corner")
        
    except Exception as e:
        print(f"[!] Position error (configure manually): {e}")
    
    ws.disconnect()
    print("\n[DONE]")

if __name__ == "__main__":
    add_window_capture()
