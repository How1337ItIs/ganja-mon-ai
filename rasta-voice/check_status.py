#!/usr/bin/env python3
"""
VB-Cable Status Checker
Quickly check the current state of VB-Audio devices
"""

import sounddevice as sd
from pathlib import Path

print("=" * 60)
print("VB-CABLE STATUS CHECK")
print("=" * 60)
print()

# Get all audio devices
devices = sd.query_devices()
vb_devices = [(i, d) for i, d in enumerate(devices) if 'CABLE' in d['name'].upper() or 'VB-AUDIO' in d['name'].upper() or 'POINT' in d['name'].upper()]

if not vb_devices:
    print("[OK] STATUS: ALL CLEAR")
    print("     No VB-Audio devices found")
    print("     Ready for fresh installation!")
    print()
    print("Next step: Run install_vbaudio.ps1 as Administrator")
else:
    print(f"[INFO] STATUS: {len(vb_devices)} VB-Audio device(s) found")
    print()

    # Group by product
    cable_std = [d for d in vb_devices if 'CABLE Input' in d[1]['name'] or 'CABLE Output' in d[1]['name']]
    cable_16ch = [d for d in vb_devices if '16ch' in d[1]['name']]
    point = [d for d in vb_devices if 'Point' in d[1]['name']]

    if cable_16ch or point:
        print("[WARNING] Multiple VB-Audio products detected!")
        print("          This may cause conflicts and distortion")
        print()

    if cable_std:
        print("VB-Cable (Standard):")
        for idx, dev in cable_std:
            max_ch = dev['max_input_channels'] if dev['max_input_channels'] > 0 else dev['max_output_channels']
            dev_type = "INPUT" if dev['max_input_channels'] > 0 else "OUTPUT"
            print(f"  [{idx}] {dev['name']}")
            print(f"      Type: {dev_type}, Channels: {max_ch}, Sample Rate: {dev['default_samplerate']} Hz")

    if cable_16ch:
        print()
        print("VB-Cable (16-channel):")
        for idx, dev in cable_16ch:
            print(f"  [{idx}] {dev['name']}")

    if point:
        print()
        print("VB-Audio Point:")
        for idx, dev in point:
            print(f"  [{idx}] {dev['name']}")

    print()

    # Check if clean install
    if len(cable_std) == 2 and not cable_16ch and not point:
        print("[OK] LOOKS GOOD: Clean VB-Cable installation detected")
        print()
        print("Next step: Test audio quality")
        print("  venv/Scripts/python.exe test_vbcable.py --vb --sr 48000")
    else:
        print("[ERROR] NEEDS CLEANUP: Multiple/conflicting installations")
        print()
        print("Next step: Run uninstall_vbaudio.ps1 as Administrator")

print()
print("=" * 60)

# Check if test files exist
print()
print("AVAILABLE TOOLS:")
if Path("test_vbcable.py").exists():
    print("  [OK] test_vbcable.py - Audio device testing")
if Path("rasta_live.py").exists():
    print("  [OK] rasta_live.py - Main voice pipeline")
if Path("uninstall_vbaudio.ps1").exists():
    print("  [OK] uninstall_vbaudio.ps1 - Uninstaller script")
if Path("install_vbaudio.ps1").exists():
    print("  [OK] install_vbaudio.ps1 - Installer script")

print()
print("For full instructions: See VB_CABLE_FIX_STEPS.md")
print("=" * 60)
