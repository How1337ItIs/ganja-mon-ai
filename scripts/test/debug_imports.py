#!/usr/bin/env python3
"""Debug import issues"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")

# Test 1: Direct import
try:
    from hardware.webcam import USBWebcam
    print("[OK] hardware.webcam direct import works")
except ImportError as e:
    print(f"[FAIL] hardware.webcam direct import: {e}")

# Test 2: From brain package context
try:
    import brain
    print(f"[OK] brain package loaded from: {brain.__file__}")
except ImportError as e:
    print(f"[FAIL] brain package: {e}")

# Test 3: Check if cv2 is available
try:
    import cv2
    print(f"[OK] cv2/OpenCV available: {cv2.__version__}")
except ImportError as e:
    print(f"[FAIL] cv2: {e}")

# Test 4: Try importing hardware package
print("\nImporting hardware package...")
try:
    import hardware
    print(f"[OK] hardware package loaded")
except Exception as e:
    print(f"[FAIL] hardware package: {e}")

# Test 5: Try the exact relative import that agent.py does
print("\nSimulating brain/agent.py relative import...")
try:
    # Manually test the relative import path
    import importlib.util
    spec = importlib.util.find_spec("hardware.webcam")
    print(f"[OK] hardware.webcam spec found: {spec}")
except Exception as e:
    print(f"[FAIL] find_spec: {e}")

try:
    from brain import agent
    print(f"[OK] brain.agent loaded")
    print(f"  WEBCAM_AVAILABLE = {agent.WEBCAM_AVAILABLE}")
    print(f"  KASA_AVAILABLE = {agent.KASA_AVAILABLE}")
    print(f"  GOVEE_AVAILABLE = {agent.GOVEE_AVAILABLE}")
except Exception as e:
    print(f"[FAIL] brain.agent: {e}")
    import traceback
    traceback.print_exc()
