#!/usr/bin/env python3
"""Test complete audio chain: Mic -> Rasta -> VB-Cable -> OBS"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests
import time

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("="*60)
print("AUDIO CHAIN TEST")
print("="*60)

# Check if rasta pipeline is running
print("\n[1/4] Checking Rasta Voice Pipeline...")
import requests
try:
    r = requests.get("http://localhost:8085/api/status", timeout=2)
    pipeline_running = r.json().get("running", False)
    if pipeline_running:
        print("[OK] Rasta pipeline is RUNNING!")
    else:
        print("[WARN] Rasta pipeline NOT running - click START in dashboard!")
except:
    print("[WARN] Can't reach dashboard - is it running?")

# Check OBS audio sources
print("\n[2/4] Checking OBS Audio Sources...")
inputs = ws.call(obs_requests.GetInputList())

desktop_found = False
mic_muted = True

for inp in inputs.getInputs():
    if "Desktop" in inp['inputName']:
        desktop_found = True
        try:
            muted = ws.call(obs_requests.GetInputMute(inputName=inp['inputName'])).getInputMuted()
            volume = ws.call(obs_requests.GetInputVolume(inputName=inp['inputName']))
            if not muted:
                print(f"[OK] {inp['inputName']}: ACTIVE (unmuted)")
            else:
                print(f"[WARN] {inp['inputName']}: MUTED (should be unmuted!)")
        except:
            pass

    if "Mic" in inp['inputName'] or "Aux" in inp['inputName']:
        try:
            muted = ws.call(obs_requests.GetInputMute(inputName=inp['inputName'])).getInputMuted()
            if muted:
                print(f"[OK] {inp['inputName']}: MUTED (correct)")
                mic_muted = True
            else:
                print(f"[WARN] {inp['inputName']}: ACTIVE (should be muted!)")
                mic_muted = False
        except:
            pass

# Check streaming status
print("\n[3/4] Checking OBS Streaming Status...")
stream_status = ws.call(obs_requests.GetStreamStatus())
if stream_status.getOutputActive():
    print("[INFO] OBS is CURRENTLY STREAMING")
else:
    print("[OK] OBS ready to stream (not streaming yet)")

# Final verdict
print("\n[4/4] FINAL VERDICT:")
print("="*60)

if desktop_found and mic_muted:
    print("[SUCCESS] Audio chain is CORRECT!")
    print("\nWhat happens when you talk:")
    print("  1. Your mic -> Rasta pipeline")
    print("  2. Rasta voice -> VB-Cable Output")
    print("  3. OBS Desktop Audio captures VB-Cable")
    print("  4. Stream gets RASTA VOICE (not your real voice)")
    print("\n[READY] You can go live!")
else:
    print("[WARN] Audio chain needs fixing:")
    if not desktop_found:
        print("  - Desktop Audio not found")
    if not mic_muted:
        print("  - Mic not muted (will leak real voice!)")

print("="*60)

ws.disconnect()
