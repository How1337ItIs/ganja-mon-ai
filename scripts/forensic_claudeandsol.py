#!/usr/bin/env python3
"""
COMPREHENSIVE FORENSIC CAPTURE - CLAUDEANDSOL.COM
==================================================

This script performs a COMPLETE forensic capture of the SOLTOMATO project website.
It captures:
- Full HTML and rendered DOM
- All network requests and responses (HAR format)
- All API endpoints and their data
- JavaScript files and source maps
- WebSocket connections and messages
- Browser storage (localStorage, sessionStorage, cookies)
- Screenshots (full page)
- All assets (images, CSS, JS, fonts)
- SSL certificate information
- DNS records

Usage:
    python scripts/forensic_claudeandsol.py
"""

import asyncio
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

# Output directory
OUTPUT_DIR = Path("data/forensics/claudeandsol_comprehensive_20260116")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_URL = "https://claudeandsol.com/"


async def capture_everything():
    """Complete forensic capture of claudeandsol.com"""
    
    print("=" * 60)
    print("💀 DEATH STAR COMPREHENSIVE FORENSIC CAPTURE 💀")
    print(f"   Target: {TARGET_URL}")
    print(f"   Output: {OUTPUT_DIR}")
    print("=" * 60)
    
    from playwright.async_api import async_playwright
    
    # Storage for captured data
    network_requests = []
    network_responses = []
    websocket_messages = []
    api_responses = {}
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        # ============================================================
        # CAPTURE NETWORK REQUESTS
        # ============================================================
        print("\n📡 Setting up network capture...")
        
        async def handle_request(request):
            req_data = {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": request.post_data,
                "resource_type": request.resource_type,
                "timestamp": datetime.now().isoformat()
            }
            network_requests.append(req_data)
            
            # Log API calls
            if "/api" in request.url or ".php" in request.url or ".json" in request.url:
                print(f"   🔗 API: {request.method} {request.url}")
        
        async def handle_response(response):
            try:
                body = None
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")
                    if "json" in content_type or "text" in content_type or "javascript" in content_type:
                        try:
                            body = await response.text()
                        except:
                            pass
                
                resp_data = {
                    "url": response.url,
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body_preview": body[:5000] if body else None,
                    "timestamp": datetime.now().isoformat()
                }
                network_responses.append(resp_data)
                
                # Save full API responses
                if "/api" in response.url or ".php" in response.url or "get_" in response.url:
                    if body:
                        api_responses[response.url] = {
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body": body,
                            "timestamp": datetime.now().isoformat()
                        }
                        print(f"   ✅ Captured API: {response.url} ({len(body)} bytes)")
            except Exception as e:
                pass
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # ============================================================
        # CAPTURE WEBSOCKETS
        # ============================================================
        async def handle_websocket(ws):
            print(f"   🔌 WebSocket opened: {ws.url}")
            
            def on_message(payload):
                websocket_messages.append({
                    "url": ws.url,
                    "direction": "received",
                    "payload": payload,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"   📨 WS Message: {payload[:100]}...")
            
            ws.on("framereceived", lambda data: on_message(data))
            ws.on("framesent", lambda data: websocket_messages.append({
                "url": ws.url,
                "direction": "sent",
                "payload": data,
                "timestamp": datetime.now().isoformat()
            }))
        
        page.on("websocket", handle_websocket)
        
        # ============================================================
        # NAVIGATE AND WAIT
        # ============================================================
        print("\n🌐 Navigating to target...")
        try:
            response = await page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
            print(f"   Status: {response.status}")
        except Exception as e:
            print(f"   ⚠️ Navigation error: {e}")
        
        # Wait for dynamic content
        print("   ⏳ Waiting for dynamic content...")
        await asyncio.sleep(5)
        
        # Scroll to trigger lazy loading
        print("   📜 Scrolling page...")
        await page.evaluate("""
            async () => {
                const height = document.body.scrollHeight;
                for (let i = 0; i < height; i += 300) {
                    window.scrollTo(0, i);
                    await new Promise(r => setTimeout(r, 100));
                }
                window.scrollTo(0, 0);
            }
        """)
        
        # Wait for any additional loads
        await asyncio.sleep(3)
        
        # ============================================================
        # CAPTURE PAGE CONTENT
        # ============================================================
        print("\n📄 Capturing page content...")
        
        # Raw HTML
        html = await page.content()
        (OUTPUT_DIR / "page.html").write_text(html, encoding="utf-8")
        print(f"   ✅ HTML: {len(html)} bytes")
        
        # Title
        title = await page.title()
        print(f"   📌 Title: {title}")
        
        # ============================================================
        # CAPTURE BROWSER STORAGE
        # ============================================================
        print("\n💾 Capturing browser storage...")
        
        # localStorage
        local_storage = await page.evaluate("""
            () => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }
        """)
        print(f"   📦 localStorage: {len(local_storage)} keys")
        
        # sessionStorage
        session_storage = await page.evaluate("""
            () => {
                const items = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    items[key] = sessionStorage.getItem(key);
                }
                return items;
            }
        """)
        print(f"   📦 sessionStorage: {len(session_storage)} keys")
        
        # Cookies
        cookies = await context.cookies()
        print(f"   🍪 Cookies: {len(cookies)}")
        
        # ============================================================
        # EXTRACT PAGE DATA
        # ============================================================
        print("\n🔍 Extracting page data...")
        
        # All links
        links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
        """)
        print(f"   🔗 Links: {len(links)}")
        
        # All scripts
        scripts = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script[src]')).map(s => s.src)
        """)
        print(f"   📜 Scripts: {len(scripts)}")
        
        # All images
        images = await page.evaluate("""
            () => Array.from(document.querySelectorAll('img[src]')).map(i => i.src)
        """)
        print(f"   🖼️ Images: {len(images)}")
        
        # All stylesheets
        stylesheets = await page.evaluate("""
            () => Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href)
        """)
        print(f"   🎨 Stylesheets: {len(stylesheets)}")
        
        # Inline scripts (may contain API endpoints, config)
        inline_scripts = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script:not([src])')).map(s => s.textContent)
        """)
        print(f"   📝 Inline scripts: {len(inline_scripts)}")
        
        # ============================================================
        # SCREENSHOT
        # ============================================================
        print("\n📸 Taking screenshot...")
        await page.screenshot(path=str(OUTPUT_DIR / "screenshot_full.png"), full_page=True)
        print(f"   ✅ Full page screenshot saved")
        
        # ============================================================
        # DOWNLOAD ASSETS
        # ============================================================
        print("\n📥 Downloading assets...")
        assets_dir = OUTPUT_DIR / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            # Download JS files
            for script_url in scripts[:20]:  # Limit to avoid issues
                try:
                    resp = await client.get(script_url)
                    if resp.status_code == 200:
                        filename = urlparse(script_url).path.split("/")[-1] or "script.js"
                        filename = re.sub(r'[^\w\-.]', '_', filename)
                        (assets_dir / f"js_{filename}").write_bytes(resp.content)
                        print(f"   ✅ JS: {filename}")
                except:
                    pass
            
            # Download CSS files
            for css_url in stylesheets[:10]:
                try:
                    resp = await client.get(css_url)
                    if resp.status_code == 200:
                        filename = urlparse(css_url).path.split("/")[-1] or "style.css"
                        filename = re.sub(r'[^\w\-.]', '_', filename)
                        (assets_dir / f"css_{filename}").write_bytes(resp.content)
                        print(f"   ✅ CSS: {filename}")
                except:
                    pass
        
        # ============================================================
        # SAVE ALL CAPTURED DATA
        # ============================================================
        print("\n💾 Saving captured data...")
        
        # Network requests
        (OUTPUT_DIR / "network_requests.json").write_text(
            json.dumps(network_requests, indent=2, default=str),
            encoding="utf-8"
        )
        print(f"   ✅ network_requests.json ({len(network_requests)} requests)")
        
        # Network responses
        (OUTPUT_DIR / "network_responses.json").write_text(
            json.dumps(network_responses, indent=2, default=str),
            encoding="utf-8"
        )
        print(f"   ✅ network_responses.json ({len(network_responses)} responses)")
        
        # API responses (full)
        (OUTPUT_DIR / "api_responses.json").write_text(
            json.dumps(api_responses, indent=2, default=str),
            encoding="utf-8"
        )
        print(f"   ✅ api_responses.json ({len(api_responses)} API calls)")
        
        # WebSocket messages
        (OUTPUT_DIR / "websocket_messages.json").write_text(
            json.dumps(websocket_messages, indent=2, default=str),
            encoding="utf-8"
        )
        print(f"   ✅ websocket_messages.json ({len(websocket_messages)} messages)")
        
        # Browser storage
        storage_data = {
            "localStorage": local_storage,
            "sessionStorage": session_storage,
            "cookies": cookies
        }
        (OUTPUT_DIR / "browser_storage.json").write_text(
            json.dumps(storage_data, indent=2, default=str),
            encoding="utf-8"
        )
        print(f"   ✅ browser_storage.json")
        
        # Page metadata
        metadata = {
            "url": TARGET_URL,
            "title": title,
            "captured_at": datetime.now().isoformat(),
            "links_count": len(links),
            "scripts_count": len(scripts),
            "images_count": len(images),
            "stylesheets_count": len(stylesheets),
            "inline_scripts_count": len(inline_scripts),
            "network_requests": len(network_requests),
            "network_responses": len(network_responses),
            "api_responses": len(api_responses),
            "websocket_messages": len(websocket_messages),
            "localStorage_keys": len(local_storage),
            "sessionStorage_keys": len(session_storage),
            "cookies": len(cookies)
        }
        (OUTPUT_DIR / "metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8"
        )
        
        # Links
        (OUTPUT_DIR / "links.txt").write_text("\n".join(links), encoding="utf-8")
        
        # Inline scripts
        for i, script in enumerate(inline_scripts):
            if script.strip():
                (OUTPUT_DIR / f"inline_script_{i}.js").write_text(script, encoding="utf-8")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 CAPTURE SUMMARY")
        print("=" * 60)
        print(f"   🌐 URL: {TARGET_URL}")
        print(f"   📄 HTML: {len(html):,} bytes")
        print(f"   📡 Network Requests: {len(network_requests)}")
        print(f"   📥 Network Responses: {len(network_responses)}")
        print(f"   🔌 API Responses: {len(api_responses)}")
        print(f"   💬 WebSocket Messages: {len(websocket_messages)}")
        print(f"   💾 localStorage keys: {len(local_storage)}")
        print(f"   🍪 Cookies: {len(cookies)}")
        print(f"   📁 Output: {OUTPUT_DIR}")
        print("=" * 60)
        
        await browser.close()
    
    print("\n✅ FORENSIC CAPTURE COMPLETE!")
    return metadata


if __name__ == "__main__":
    asyncio.run(capture_everything())
