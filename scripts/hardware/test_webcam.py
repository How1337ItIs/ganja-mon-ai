#!/usr/bin/env python3
"""Quick webcam test"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from hardware.webcam import list_cameras, USBWebcam
import asyncio

async def test():
    print("Webcam Test")
    print("=" * 40)

    # List cameras
    print("\nDiscovering cameras...")
    cameras = list_cameras()

    if not cameras:
        print("No cameras found!")
        return

    print(f"Found {len(cameras)} camera(s):")
    for cam in cameras:
        print(f"  [{cam['index']}] {cam['resolution']} @ {cam['fps']}fps ({cam['backend']})")

    # Test capture
    print("\nTesting capture...")
    webcam = USBWebcam(device_index=cameras[0]['index'])

    if await webcam.connect():
        print(f"Connected: {webcam.get_resolution()}")

        # Capture for analysis (returns bytes + base64)
        img_bytes, b64_str = await webcam.capture_for_analysis()
        print(f"Captured: {len(img_bytes)} bytes, base64 len: {len(b64_str)}")

        # Save test image
        from pathlib import Path
        test_path = Path("test_webcam_capture.jpg")
        test_path.write_bytes(img_bytes)
        print(f"Saved to: {test_path}")

        await webcam.disconnect()
    else:
        print("Failed to connect")

if __name__ == "__main__":
    asyncio.run(test())
