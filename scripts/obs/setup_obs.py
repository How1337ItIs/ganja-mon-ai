#!/usr/bin/env python3
"""
OBS Auto-Configuration via WebSocket
=====================================
Programmatically sets up all scenes for Grok & Mon launch stream.
"""

import asyncio
import sys

try:
    from obswebsocket import obsws, requests as obs_requests
except ImportError:
    print("Installing obs-websocket-py...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "obs-websocket-py"])
    from obswebsocket import obsws, requests as obs_requests


# OBS WebSocket credentials
# WSL to Windows: Use Windows host IP (not localhost)
import socket
import subprocess

# Host connection
WS_HOST = "localhost"  # Use localhost when running from Windows

WS_PORT = 4455
WS_PASSWORD = "h2LDVnmFYDUpSVel"  # Correct password from screenshot

# Camera URLs
PLANT_CAM_URL = "http://192.168.125.128:8000/api/webcam/stream"
SENSOR_BAR_URL = "http://192.168.125.128:8000/overlay/bar"
COMMENTARY_URL = "http://192.168.125.128:8000/overlay/commentary"
TOKEN_URL = "http://192.168.125.128:8000/overlay/token"


def setup_obs():
    """Configure OBS with all scenes"""
    print("[*] Connecting to OBS WebSocket...")

    try:
        ws = obsws(WS_HOST, WS_PORT, WS_PASSWORD)
        ws.connect()
        print("[OK] Connected to OBS!")

    except Exception as e:
        print(f"[X] Connection failed: {e}")
        print("\nMake sure:")
        print("  1. OBS is running")
        print("  2. WebSocket is enabled (Tools → WebSocket Server Settings)")
        print("  3. Password is correct")
        return

    try:
        print("\n[*] Creating scenes...")

        # Scene 1: Main (Plant + You PiP)
        print("  Creating 'Main - Plant + You'...")
        ws.call(obs_requests.CreateScene(sceneName="Main - Plant + You"))

        # Add plant webcam (background)
        ws.call(obs_requests.CreateInput(
            sceneName="Main - Plant + You",
            inputName="Mon Plant Cam",
            inputKind="browser_source",
            inputSettings={
                "url": PLANT_CAM_URL,
                "width": 1920,
                "height": 1080
            }
        ))

        # Add laptop webcam (corner)
        ws.call(obs_requests.CreateInput(
            sceneName="Main - Plant + You",
            inputName="Laptop Webcam",
            inputKind="dshow_input",  # Windows camera
            inputSettings={}
        ))

        # Position laptop cam in corner
        ws.call(obs_requests.SetSceneItemTransform(
            sceneName="Main - Plant + You",
            sceneItemId=ws.call(obs_requests.GetSceneItemId(
                sceneName="Main - Plant + You",
                sourceName="Laptop Webcam"
            )).getSceneItemId(),
            sceneItemTransform={
                "positionX": 1520,
                "positionY": 780,
                "scaleX": 0.3,
                "scaleY": 0.3
            }
        ))

        # Add sensor bar overlay
        ws.call(obs_requests.CreateInput(
            sceneName="Main - Plant + You",
            inputName="Sensor Bar",
            inputKind="browser_source",
            inputSettings={
                "url": SENSOR_BAR_URL,
                "width": 1920,
                "height": 60
            }
        ))

        # Position sensor bar at bottom
        ws.call(obs_requests.SetSceneItemTransform(
            sceneName="Main - Plant + You",
            sceneItemId=ws.call(obs_requests.GetSceneItemId(
                sceneName="Main - Plant + You",
                sourceName="Sensor Bar"
            )).getSceneItemId(),
            sceneItemTransform={
                "positionX": 0,
                "positionY": 1020
            }
        ))

        print("  [OK] Main scene created!")

        # Scene 2: Talking Head
        print("  Creating 'Talking Head'...")
        ws.call(obs_requests.CreateScene(sceneName="Talking Head"))

        ws.call(obs_requests.CreateInput(
            sceneName="Talking Head",
            inputName="Laptop Webcam Full",
            inputKind="dshow_input",
            inputSettings={}
        ))

        ws.call(obs_requests.CreateInput(
            sceneName="Talking Head",
            inputName="Commentary Overlay",
            inputKind="browser_source",
            inputSettings={
                "url": COMMENTARY_URL,
                "width": 600,
                "height": 300
            }
        ))

        print("  [OK] Talking Head created!")

        # Scene 3: Split Screen
        print("  Creating 'Split Screen'...")
        ws.call(obs_requests.CreateScene(sceneName="Split Screen"))

        ws.call(obs_requests.CreateInput(
            sceneName="Split Screen",
            inputName="You Left",
            inputKind="dshow_input",
            inputSettings={}
        ))

        ws.call(obs_requests.CreateInput(
            sceneName="Split Screen",
            inputName="Mon Right",
            inputKind="browser_source",
            inputSettings={
                "url": PLANT_CAM_URL,
                "width": 1920,
                "height": 1080
            }
        ))

        print("  [OK] Split Screen created!")

        # Scene 4: Plant Only
        print("  Creating 'Plant Only'...")
        ws.call(obs_requests.CreateScene(sceneName="Plant Only"))

        ws.call(obs_requests.CreateInput(
            sceneName="Plant Only",
            inputName="Mon Fullscreen",
            inputKind="browser_source",
            inputSettings={
                "url": PLANT_CAM_URL,
                "width": 1920,
                "height": 1080
            }
        ))

        ws.call(obs_requests.CreateInput(
            sceneName="Plant Only",
            inputName="All Overlays Bar",
            inputKind="browser_source",
            inputSettings={
                "url": SENSOR_BAR_URL,
                "width": 1920,
                "height": 60
            }
        ))

        print("  [OK] Plant Only created!")

        # Set current scene
        ws.call(obs_requests.SetCurrentProgramScene(sceneName="Main - Plant + You"))

        print("\n[SUCCESS] OBS CONFIGURED!")
        print("\nYou have 4 scenes:")
        print("  1. Main - Plant + You (default)")
        print("  2. Talking Head")
        print("  3. Split Screen")
        print("  4. Plant Only")
        print("\nSwitch scenes by clicking their names in OBS!")
        print("\nNext:")
        print("  1. Settings → Stream → Add YouTube key")
        print("  2. Click 'Start Streaming'")
        print("  3. GO LIVE! [READY]")

    except Exception as e:
        print(f"[X] Setup error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        ws.disconnect()
        print("\n[OK] Disconnected from OBS")


if __name__ == "__main__":
    setup_obs()
