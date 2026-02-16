#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Test for Ultimate Dub Playlist
=======================================
Tests the playlist functionality on the production website.
"""
import asyncio
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

PRODUCTION_URL = "https://grokandmon.com"

async def test_playlist():
    """Test playlist functionality in browser."""
    print("=" * 60)
    print("Testing Ultimate Dub Playlist on Production")
    print("=" * 60)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Collect console errors
        console_errors = []
        page.on('console', lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == 'error' else None)
        
        try:
            # Test 1: Load homepage
            print("Test 1: Loading homepage...")
            response = await page.goto(PRODUCTION_URL, wait_until='domcontentloaded', timeout=30000)
            print(f"   Status: {response.status}")
            
            if not response.ok:
                print(f"   FAILED Failed to load: HTTP {response.status}")
                return False
            
            print("   OK Homepage loaded")
            await page.wait_for_timeout(2000)  # Wait for JS to load
            
            # Test 2: Check for playlist selector
            print("\nTest 2: Checking for playlist selector...")
            selector = page.locator('#playlist-selector, #playlist-select')
            count = await selector.count()
            
            if count > 0:
                print("   OK Playlist selector found")
                # Try to interact with it
                try:
                    await selector.click()
                    await page.wait_for_timeout(500)
                    print("   OK Playlist selector is interactive")
                except Exception as e:
                    print(f"   ⚠️  Selector found but not interactive: {e}")
            else:
                print("   ⚠️  Playlist selector not found (may be hidden or not loaded)")
            
            # Test 3: Test API endpoints
            print("\nTest 3: Testing API endpoints...")
            
            # Test playlist list
            api_response = await page.request.get(f"{PRODUCTION_URL}/api/playlist/list")
            if api_response.ok:
                try:
                    data = await api_response.json()
                    playlists = data.get('playlists', [])
                    print(f"   OK Playlist list API: {len(playlists)} playlists found")
                    for pl in playlists:
                        print(f"      - {pl.get('name', 'Unknown')} ({pl.get('track_count', 0)} tracks)")
                except Exception as e:
                    text = await api_response.text()
                    print(f"   WARNING API returned non-JSON (first 200 chars): {text[:200]}")
                    print(f"   This might mean the API route isn't deployed yet")
            else:
                print(f"   FAILED Playlist list API failed: HTTP {api_response.status}")
            
            # Test ultimate dub playlist
            dub_response = await page.request.get(f"{PRODUCTION_URL}/api/playlist/ultimate_dub")
            if dub_response.ok:
                try:
                    data = await dub_response.json()
                    tracks = data.get('tracks', [])
                    print(f"   OK Ultimate dub playlist API: {len(tracks)} tracks")
                    
                    # Check first track URL
                    if tracks:
                        first_track = tracks[0]
                        track_url = first_track.get('url', '')
                        print(f"   First track URL: {track_url}")
                        
                        # Test streaming endpoint
                        if track_url:
                            stream_url = f"{PRODUCTION_URL}{track_url}" if track_url.startswith('/') else track_url
                            print(f"   Testing stream: {stream_url[:80]}...")
                            stream_response = await page.request.get(stream_url, headers={'Range': 'bytes=0-1023'})
                            if stream_response.ok or stream_response.status == 206:
                                print(f"   OK Stream working: HTTP {stream_response.status}")
                            else:
                                print(f"   WARNING Stream response: HTTP {stream_response.status}")
                except Exception as e:
                    text = await dub_response.text()
                    print(f"   WARNING API returned non-JSON: {text[:200]}")
            else:
                print(f"   WARNING Ultimate dub playlist API: HTTP {dub_response.status}")
            
            # Test 4: Check for Webamp player
            print("\n🎛️  Test 4: Checking for Webamp player...")
            webamp_container = page.locator('#webamp-container')
            count = await webamp_container.count()
            
            if count > 0:
                print("   OK Webamp container found")
            else:
                print("   ⚠️  Webamp container not found")
            
            # Test 5: Screenshot
            print("\nTest 5: Taking screenshot...")
            screenshot_path = Path(__file__).parent.parent / "research" / "dub_playlist_test_screenshot.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   OK Screenshot saved: {screenshot_path}")
            
            # Report console errors
            if console_errors:
                print(f"\n⚠️  Console errors ({len(console_errors)}):")
                for error in console_errors[:5]:  # Show first 5
                    print(f"   - {error}")
            else:
                print("\nOK No console errors")
            
            print("\n" + "=" * 60)
            print("OK Browser test complete!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\nFAILED Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_playlist())
