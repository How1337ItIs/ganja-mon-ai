#!/usr/bin/env python3
"""
Test all hardware integrations for Grok & Mon.

Run with: python scripts/test_all_hardware.py

This tests:
- Kasa smart plugs (local network)
- Govee sensors (cloud API)
- Webcam (if available)
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def print_ok(text: str):
    print(f"  [OK] {text}")


def print_warn(text: str):
    print(f"  [WARN] {text}")


def print_fail(text: str):
    print(f"  [FAIL] {text}")


async def test_kasa():
    """Test Kasa smart plug integration"""
    print_header("KASA SMART PLUGS")

    try:
        from hardware.kasa import KasaActuatorHub, discover_kasa_devices
    except ImportError as e:
        print_fail(f"Import failed: {e}")
        print_warn("Install with: pip install python-kasa")
        return False

    # Discover devices on network
    print("\n  Scanning local network...")
    try:
        devices = await discover_kasa_devices()
        if not devices:
            print_warn("No Kasa devices found on network")
            print_warn("Make sure plugs are connected to same WiFi")
            return False

        # Filter to devices that don't need auth
        accessible = [d for d in devices if not d.get('needs_auth', False)]
        auth_required = [d for d in devices if d.get('needs_auth', False)]

        print_ok(f"Found {len(devices)} Kasa device(s):")
        for d in devices:
            auth_note = " [NEEDS AUTH]" if d.get('needs_auth') else ""
            state = d.get('is_on')
            state_str = "ON" if state else ("OFF" if state is not None else "?")
            print(f"      {d['alias']} @ {d['ip']} ({d['model']}) - {state_str}{auth_note}")

        if auth_required:
            print_warn(f"{len(auth_required)} Tapo device(s) need authentication")
            print_warn("Set TAPO_USERNAME and TAPO_PASSWORD in .env")

        if not accessible:
            print_warn("No accessible devices (all need auth)")
            return False

        # Try connecting to first accessible device
        first_ip = accessible[0]['ip']
        kasa_ips = {"test_device": first_ip}

        hub = KasaActuatorHub(kasa_ips)
        if await hub.connect():
            print_ok("Successfully connected to Kasa hub")
            state = await hub.get_state()
            print(f"      Current state: {state}")
            return True
        else:
            print_fail("Failed to connect to Kasa hub")
            return False

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


async def test_govee():
    """Test Govee sensor integration"""
    print_header("GOVEE SENSORS")

    api_key = os.environ.get("GOVEE_API_KEY")
    if not api_key:
        print_fail("GOVEE_API_KEY not set in environment")
        print_warn("Get your key from: https://developer.govee.com/")
        print_warn("Or: Govee Home app > Settings > About Us > Apply for API Key")
        return False

    print_ok(f"API Key found: {api_key[:8]}...")

    try:
        from hardware.govee import GoveeSensorHub, discover_govee_sensors
    except ImportError as e:
        print_fail(f"Import failed: {e}")
        return False

    try:
        sensors = await discover_govee_sensors(api_key)
        if not sensors:
            print_warn("No temperature sensors found on Govee account")
            print_warn("Supported models: H5179, H5075, H5074, H5072, H5101, H5102")
            return False

        print_ok(f"Found {len(sensors)} sensor(s):")
        for s in sensors:
            print(f"      {s.get('deviceName')} ({s.get('model')})")

        # Read from sensor
        hub = GoveeSensorHub(api_key=api_key)
        if await hub.connect():
            print_ok("Connected to Govee API")
            reading = await hub.read_all()
            print_ok(f"Reading: {reading.air_temp:.1f}°C, {reading.humidity:.1f}% RH")
            print_ok(f"VPD: {reading.vpd:.2f} kPa")
            await hub.disconnect()
            return True
        else:
            print_fail("Failed to connect to Govee")
            return False

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


async def test_webcam():
    """Test webcam integration"""
    print_header("WEBCAM")

    try:
        from hardware.webcam import USBWebcam
    except ImportError as e:
        print_fail(f"Import failed: {e}")
        print_warn("Install with: pip install opencv-python")
        return False

    try:
        cam = USBWebcam()
        if await cam.connect():
            print_ok("Webcam connected")

            # Try to capture
            path, b64 = await cam.capture_for_analysis()
            if path:
                print_ok(f"Image captured: {path}")
                print_ok(f"Base64 length: {len(b64)} chars")
                return True
            else:
                print_warn("Capture failed - no image data")
                return False
        else:
            print_warn("No webcam found")
            return False

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


async def test_grok_api():
    """Test Grok API connection"""
    print_header("GROK API (xAI)")

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print_fail("XAI_API_KEY not set in environment")
        print_warn("Get your key from: https://console.x.ai/")
        return False

    print_ok(f"API Key found: {api_key[:8]}...")

    try:
        import httpx

        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        ) as client:
            response = await client.get("https://api.x.ai/v1/models")
            if response.status_code == 200:
                data = response.json()
                models = [m['id'] for m in data.get('data', [])][:5]
                print_ok("Connected to Grok API")
                print(f"      Available models: {', '.join(models)}")
                return True
            else:
                print_fail(f"API returned status {response.status_code}")
                return False

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


async def main():
    print("\n" + "="*60)
    print(" GROK & MON - HARDWARE INTEGRATION TEST")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = {}

    # Test each component
    results['kasa'] = await test_kasa()
    results['govee'] = await test_govee()
    results['webcam'] = await test_webcam()
    results['grok'] = await test_grok_api()

    # Summary
    print_header("SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, status in results.items():
        icon = "[OK]" if status else "[FAIL]"
        print(f"  {icon} {name.upper()}: {'PASS' if status else 'FAIL'}")

    print(f"\n  {passed}/{total} components working")

    if passed == total:
        print("\n  All systems go! Ready for Grok & Mon.")
    elif passed >= 2:
        print("\n  Partial setup. Core functions available.")
    else:
        print("\n  Setup needed. Check the warnings above.")


if __name__ == "__main__":
    asyncio.run(main())
