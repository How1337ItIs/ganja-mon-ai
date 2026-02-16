#!/usr/bin/env python3
"""Quick test to verify the dashboard server works."""

import requests
import time
import subprocess
import sys
from pathlib import Path

def test_dashboard():
    """Test if dashboard is running and responding."""
    port = 8086
    url = f"http://localhost:{port}"
    
    print(f"Testing dashboard at {url}...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{url}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Health endpoint works!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
        
        # Test main page
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print("✅ Main page loads!")
            if "Ganja Mon Translator" in response.text:
                print("✅ HTML content looks correct!")
            else:
                print("⚠️  HTML content might be wrong")
        else:
            print(f"❌ Main page returned {response.status_code}")
            return False
        
        print("\n✅ Dashboard is working!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {url}")
        print("   Is the server running? Start it with:")
        print("   python grok_translate_dashboard.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if not test_dashboard():
        sys.exit(1)
