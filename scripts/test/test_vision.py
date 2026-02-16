#!/usr/bin/env python3
"""
Grok Vision Test Script
=======================
Tests the Grok vision API with a sample/test image.
Can use webcam capture or a provided image file.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()


async def test_vision_with_sample():
    """Test vision with a sample/generated image"""
    from ai.vision import GrokVision, create_vision_analyzer

    print("=" * 50)
    print("Grok Vision API Test")
    print("=" * 50)

    # Check API key
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("\n[ERROR] XAI_API_KEY not set!")
        print("Set it in .env file or export XAI_API_KEY='your-key'")
        return False

    print(f"\n[OK] XAI_API_KEY configured (ends with ...{api_key[-8:]})")

    # Create vision analyzer
    vision = create_vision_analyzer()
    print(f"[OK] Vision model: {vision.model}")

    # Check for test image or use webcam
    test_images = list(Path(".").glob("test*.jpg")) + list(Path(".").glob("test*.png"))

    image_data = None
    image_source = "none"

    if test_images:
        # Use existing test image
        image_path = test_images[0]
        print(f"\n[OK] Using test image: {image_path}")
        image_data = image_path.read_bytes()
        image_source = str(image_path)
    else:
        # Try webcam
        print("\n[INFO] No test image found. Trying webcam...")
        try:
            from hardware.webcam import USBWebcam, list_cameras

            cameras = list_cameras()
            if cameras:
                print(f"[OK] Found {len(cameras)} camera(s)")
                webcam = USBWebcam(device_index=cameras[0]['index'])
                if await webcam.connect():
                    image_data, _ = await webcam.capture_for_analysis()
                    await webcam.disconnect()

                    # Save for reference
                    Path("test_capture.jpg").write_bytes(image_data)
                    print("[OK] Captured image from webcam -> test_capture.jpg")
                    image_source = "webcam"
        except Exception as e:
            print(f"[WARN] Webcam not available: {e}")

    if not image_data:
        # Create a simple placeholder image for API test
        print("\n[INFO] Creating placeholder image for API test...")
        try:
            from PIL import Image
            import io

            # Create a simple green gradient (represents plant)
            img = Image.new('RGB', (640, 480), color=(34, 139, 34))  # Forest green

            # Add some variation
            for x in range(640):
                for y in range(480):
                    r = 34 + int(x * 0.05)
                    g = 139 + int(y * 0.1)
                    b = 34
                    if r > 255: r = 255
                    if g > 255: g = 255
                    img.putpixel((x, y), (r, min(g, 255), b))

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            image_data = buffer.getvalue()

            Path("test_placeholder.jpg").write_bytes(image_data)
            print("[OK] Created placeholder -> test_placeholder.jpg")
            image_source = "placeholder"
        except ImportError:
            print("[ERROR] PIL not available and no test image found")
            print("\nTo test with a real image:")
            print("  1. Place a test.jpg file in the project root")
            print("  2. Or connect a webcam and ensure /dev/video0 exists")
            return False

    # Run vision analysis
    print(f"\n[INFO] Sending to Grok Vision API...")
    print(f"       Image source: {image_source}")
    print(f"       Image size: {len(image_data)} bytes")

    try:
        analysis = await vision.analyze(
            image_data=image_data,
            growth_stage="vegetative",
            current_day=1,
            additional_context="This is a test image for API verification."
        )

        print("\n" + "=" * 50)
        print("VISION ANALYSIS RESULTS")
        print("=" * 50)

        print(f"\nOverall Health: {analysis.overall_health}")
        print(f"Confidence: {analysis.confidence:.0%}")
        print(f"Tokens Used: {analysis.tokens_used}")

        if analysis.detected_issues:
            print(f"\nDetected Issues ({len(analysis.detected_issues)}):")
            for issue in analysis.detected_issues:
                print(f"  - {issue.get('type', 'unknown')}: {issue.get('description', 'N/A')}")
                print(f"    Severity: {issue.get('severity', 'N/A')}")
        else:
            print("\nNo issues detected!")

        if analysis.observations:
            print(f"\nObservations ({len(analysis.observations)}):")
            for obs in analysis.observations:
                print(f"  - {obs}")

        if analysis.recommendations:
            print(f"\nRecommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")

        print("\n" + "=" * 50)
        print("[SUCCESS] Vision API test completed!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\n[ERROR] Vision analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_webcam_only():
    """Quick webcam test"""
    from hardware.webcam import list_cameras, USBWebcam

    print("Webcam Quick Test")
    print("=" * 40)

    cameras = list_cameras()
    if not cameras:
        print("No cameras found!")
        print("\nTroubleshooting:")
        print("  1. Connect USB webcam")
        print("  2. On WSL: Run scripts/setup_camera_windows.ps1 first")
        print("  3. Check: ls /dev/video*")
        return False

    print(f"Found {len(cameras)} camera(s):")
    for cam in cameras:
        print(f"  [{cam['index']}] {cam['resolution']} @ {cam['fps']}fps")

    webcam = USBWebcam(device_index=cameras[0]['index'])
    if await webcam.connect():
        print(f"\nConnected: {webcam.get_resolution()}")

        img_bytes, b64 = await webcam.capture_for_analysis()
        Path("test_webcam.jpg").write_bytes(img_bytes)
        print(f"Captured: {len(img_bytes)} bytes -> test_webcam.jpg")

        await webcam.disconnect()
        return True
    else:
        print("Failed to connect to webcam")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Grok Vision API")
    parser.add_argument("--webcam-only", action="store_true", help="Only test webcam, no API call")
    args = parser.parse_args()

    if args.webcam_only:
        success = asyncio.run(test_webcam_only())
    else:
        success = asyncio.run(test_vision_with_sample())

    sys.exit(0 if success else 1)
