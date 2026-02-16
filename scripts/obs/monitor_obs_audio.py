#!/usr/bin/env python3
"""Monitor OBS audio levels in real-time"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests
import time

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("="*60)
print("OBS AUDIO LEVEL MONITOR")
print("="*60)
print("\nSay something in Rasta voice now...")
print("(Watch the levels below)\n")

try:
    for i in range(10):
        # Get audio levels
        try:
            # Get Desktop Audio level
            desktop_vol = ws.call(obs_requests.GetInputVolume(inputName="Desktop Audio"))
            desktop_db = desktop_vol.getInputVolumeDb()

            # Get Mic level
            try:
                mic_vol = ws.call(obs_requests.GetInputVolume(inputName="Mic/Aux"))
                mic_db = mic_vol.getInputVolumeDb()
            except:
                mic_db = -100  # Silent/muted

            # Display
            desktop_bar = "█" * max(0, min(50, int((desktop_db + 60) / 60 * 50)))
            mic_bar = "█" * max(0, min(50, int((mic_db + 60) / 60 * 50)))

            print(f"\r[Desktop/VB-Cable] {desktop_bar} {desktop_db:.1f}dB | [Mic] {mic_bar} {mic_db:.1f}dB", end="", flush=True)

            time.sleep(0.5)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            break

    print("\n\n" + "="*60)
    print("If Desktop Audio bar moved: VB-Cable is working! ✅")
    print("If Mic bar moved: Mic is leaking through! ❌")
    print("="*60)

except KeyboardInterrupt:
    print("\n[STOPPED]")

ws.disconnect()
