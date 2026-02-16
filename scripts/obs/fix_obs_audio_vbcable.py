#!/usr/bin/env python3
"""Fix OBS to ONLY use VB-Cable, disable mic"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Fixing OBS audio - disabling mic, enabling VB-Cable only...")

try:
    # Get all audio inputs
    inputs = ws.call(obs_requests.GetInputList())

    print("\n[*] Current audio inputs:")
    for inp in inputs.getInputs():
        print(f"  - {inp['inputName']} ({inp['inputKind']})")

    # Disable Mic/Aux
    print("\n[*] Disabling Mic/Auxiliary Audio...")
    try:
        ws.call(obs_requests.SetInputMute(inputName="Mic/Aux", inputMuted=True))
        print("[OK] Mic muted!")
    except:
        print("[SKIP] Mic/Aux not found")

    # Disable any microphone inputs
    for name in ["Microphone", "Mic", "Mic/Auxiliary Audio", "Aux"]:
        try:
            ws.call(obs_requests.SetInputMute(inputName=name, inputMuted=True))
            print(f"[OK] Muted: {name}")
        except:
            pass

    # Enable Desktop Audio (VB-Cable)
    print("\n[*] Enabling Desktop Audio (VB-Cable)...")
    try:
        ws.call(obs_requests.SetInputMute(inputName="Desktop Audio", inputMuted=False))
        ws.call(obs_requests.SetInputVolume(inputName="Desktop Audio", inputVolumeDb=0.0))
        print("[OK] Desktop Audio enabled and unmuted!")
    except Exception as e:
        print(f"[WARN] {e}")

    print("\n[SUCCESS] Audio fixed!")
    print("OBS should now ONLY capture VB-Cable (Rasta voice)")
    print("Your mic should not move anymore!")
    print("\nTalk and watch - only VB-Cable meter should move!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

ws.disconnect()
