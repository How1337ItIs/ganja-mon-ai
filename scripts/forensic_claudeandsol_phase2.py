#!/usr/bin/env python3
"""
ULTIMATE EXHAUSTIVE CAPTURE - EVERYTHING FROM CLAUDEANDSOL
===========================================================

This captures ABSOLUTELY EVERYTHING for complete reverse engineering:
- All API endpoints with various parameters
- All static assets (images, fonts, icons)
- Webcam images
- robots.txt, sitemap.xml, manifest.json
- SSL certificate
- DNS records
- Source maps (if available)
- All possible API variations
- HTTP headers in full detail
- Favicon, apple-touch-icons, etc.
"""

import asyncio
import json
import ssl
import socket
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin
import httpx

OUTPUT_DIR = Path("data/forensics/claudeandsol_comprehensive_20260116")
TARGET = "claudeandsol.com"
BASE_URL = f"https://{TARGET}"

async def capture_everything_else():
    print("=" * 60)
    print("💀 DEATH STAR EXHAUSTIVE CAPTURE - PHASE 2 💀")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        
        # ============================================================
        # 1. ROBOTS.TXT & SITEMAP
        # ============================================================
        print("\n📜 Fetching robots.txt and sitemap...")
        
        try:
            resp = await client.get(f"{BASE_URL}/robots.txt")
            if resp.status_code == 200:
                (OUTPUT_DIR / "robots.txt").write_text(resp.text)
                print(f"   ✅ robots.txt ({len(resp.text)} bytes)")
        except Exception as e:
            print(f"   ❌ robots.txt: {e}")
        
        try:
            resp = await client.get(f"{BASE_URL}/sitemap.xml")
            if resp.status_code == 200:
                (OUTPUT_DIR / "sitemap.xml").write_text(resp.text)
                print(f"   ✅ sitemap.xml ({len(resp.text)} bytes)")
        except:
            print("   ⚠️ No sitemap.xml")
        
        # ============================================================
        # 2. MANIFEST, FAVICONS, META
        # ============================================================
        print("\n🎨 Fetching app manifest and icons...")
        
        meta_files = [
            "manifest.json",
            "site.webmanifest", 
            "favicon.ico",
            "favicon.png",
            "apple-touch-icon.png",
            "apple-touch-icon-precomposed.png",
            "icon-192.png",
            "icon-512.png",
        ]
        
        icons_dir = OUTPUT_DIR / "icons"
        icons_dir.mkdir(exist_ok=True)
        
        for filename in meta_files:
            try:
                resp = await client.get(f"{BASE_URL}/{filename}")
                if resp.status_code == 200:
                    path = icons_dir / filename
                    path.write_bytes(resp.content)
                    print(f"   ✅ {filename} ({len(resp.content)} bytes)")
            except:
                pass
        
        # ============================================================
        # 3. WEBCAM IMAGE
        # ============================================================
        print("\n📷 Fetching webcam image...")
        
        webcam_endpoints = [
            "/api/webcam/latest",
            "/api/webcam",
            "/webcam.jpg",
            "/api/camera/latest",
        ]
        
        for endpoint in webcam_endpoints:
            try:
                resp = await client.get(f"{BASE_URL}{endpoint}")
                if resp.status_code == 200 and len(resp.content) > 1000:
                    ext = "jpg" if "jpeg" in resp.headers.get("content-type", "") else "png"
                    (OUTPUT_DIR / f"webcam.{ext}").write_bytes(resp.content)
                    print(f"   ✅ Webcam image from {endpoint} ({len(resp.content)} bytes)")
                    break
            except:
                pass
        
        # ============================================================
        # 4. ALL API ENDPOINTS WITH VARIATIONS
        # ============================================================
        print("\n🔌 Probing additional API endpoints...")
        
        api_endpoints = [
            # Core endpoints with variations
            "/api/sensors/latest",
            "/api/sensors/history?hours=1",
            "/api/sensors/history?hours=6",
            "/api/sensors/history?hours=12",
            "/api/sensors/history?hours=24",
            "/api/sensors/history?hours=48",
            "/api/sensors/history?hours=168",  # 1 week
            "/api/devices/latest",
            "/api/devices/history?hours=24",
            "/api/ai/latest",
            "/api/ai/history?limit=10",
            "/api/ai/history?limit=50",
            "/api/coin/latest",
            "/api/coin/history?hours=24",
            "/api/stats",
            "/api/stats/detailed",
            "/api/plant-progress?limit=50",
            "/api/plant-progress?limit=100",
            "/api/comments?limit=100",
            "/api/updates?limit=50",
            "/api/aggregates/hourly?hours=48",
            "/api/aggregates/daily?days=7",
            "/api/config",
            "/api/status",
            "/api/health",
            "/api/version",
            "/api/info",
            # Memory/AI specific
            "/api/memory",
            "/api/memory/latest",
            "/api/memory/episodic",
            "/api/thinking",
            "/api/decisions",
            "/api/logs",
            "/api/logs/latest",
            # Webhooks/Events
            "/api/events",
            "/api/events/latest",
            "/api/webhooks",
            # Media
            "/api/images",
            "/api/images/latest",
            "/api/timelapse",
        ]
        
        api_dir = OUTPUT_DIR / "api_probed"
        api_dir.mkdir(exist_ok=True)
        
        probed_results = {}
        for endpoint in api_endpoints:
            try:
                resp = await client.get(f"{BASE_URL}{endpoint}")
                name = endpoint.replace("/", "_").replace("?", "_").strip("_")
                
                probed_results[endpoint] = {
                    "status": resp.status_code,
                    "size": len(resp.content),
                    "content_type": resp.headers.get("content-type", ""),
                }
                
                if resp.status_code == 200 and len(resp.content) > 2:
                    (api_dir / f"{name}.json").write_bytes(resp.content)
                    print(f"   ✅ {endpoint} ({len(resp.content)} bytes)")
                else:
                    print(f"   ⚠️ {endpoint} -> {resp.status_code}")
            except Exception as e:
                probed_results[endpoint] = {"error": str(e)}
        
        (OUTPUT_DIR / "api_probe_results.json").write_text(
            json.dumps(probed_results, indent=2)
        )
        
        # ============================================================
        # 5. SSL CERTIFICATE
        # ============================================================
        print("\n🔒 Capturing SSL certificate...")
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((TARGET, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=TARGET) as ssock:
                    cert = ssock.getpeercert()
                    cert_binary = ssock.getpeercert(binary_form=True)
                    
                    (OUTPUT_DIR / "ssl_certificate.json").write_text(
                        json.dumps(cert, indent=2, default=str)
                    )
                    (OUTPUT_DIR / "ssl_certificate.der").write_bytes(cert_binary)
                    print(f"   ✅ SSL cert captured (issuer: {cert.get('issuer', 'unknown')})")
        except Exception as e:
            print(f"   ❌ SSL cert: {e}")
        
        # ============================================================
        # 6. DNS RECORDS
        # ============================================================
        print("\n🌐 Capturing DNS records...")
        
        try:
            import dns.resolver
            dns_records = {}
            
            for record_type in ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]:
                try:
                    answers = dns.resolver.resolve(TARGET, record_type)
                    dns_records[record_type] = [str(r) for r in answers]
                    print(f"   ✅ {record_type}: {dns_records[record_type]}")
                except:
                    pass
            
            (OUTPUT_DIR / "dns_records.json").write_text(json.dumps(dns_records, indent=2))
        except ImportError:
            print("   ⚠️ dnspython not installed, skipping DNS")
        except Exception as e:
            print(f"   ❌ DNS: {e}")
        
        # ============================================================
        # 7. HTTP HEADERS DETAILED
        # ============================================================
        print("\n📋 Capturing detailed HTTP headers...")
        
        resp = await client.get(BASE_URL)
        headers_detailed = {
            "request_headers": dict(resp.request.headers),
            "response_headers": dict(resp.headers),
            "http_version": str(resp.http_version),
            "status_code": resp.status_code,
        }
        (OUTPUT_DIR / "http_headers_detailed.json").write_text(
            json.dumps(headers_detailed, indent=2)
        )
        print(f"   ✅ Headers captured")
        
        # ============================================================
        # 8. SOURCE MAPS
        # ============================================================
        print("\n🗺️ Looking for source maps...")
        
        # Read inline script and look for sourceMappingURL
        inline_js = (OUTPUT_DIR / "inline_script_0.js").read_text(encoding="utf-8")
        if "sourceMappingURL" in inline_js:
            import re
            matches = re.findall(r'//# sourceMappingURL=(.+)', inline_js)
            for map_url in matches:
                try:
                    full_url = urljoin(BASE_URL, map_url)
                    resp = await client.get(full_url)
                    if resp.status_code == 200:
                        (OUTPUT_DIR / "source_map.json").write_bytes(resp.content)
                        print(f"   ✅ Source map captured ({len(resp.content)} bytes)")
                except:
                    pass
        else:
            print("   ⚠️ No source maps found in bundle")
        
        # ============================================================
        # 9. ALL IMAGES FROM PAGE
        # ============================================================
        print("\n🖼️ Downloading all images...")
        
        images_dir = OUTPUT_DIR / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Read HTML and find all images
        html = (OUTPUT_DIR / "page.html").read_text(encoding="utf-8")
        import re
        img_urls = set(re.findall(r'src=["\']([^"\']*\.(jpg|jpeg|png|gif|webp|svg))["\']', html, re.I))
        img_urls.update(re.findall(r'url\(["\']?([^"\'()]*\.(jpg|jpeg|png|gif|webp|svg))["\']?\)', html, re.I))
        
        for img_url, ext in img_urls:
            try:
                full_url = urljoin(BASE_URL, img_url)
                resp = await client.get(full_url)
                if resp.status_code == 200:
                    filename = img_url.split("/")[-1].split("?")[0]
                    (images_dir / filename).write_bytes(resp.content)
                    print(f"   ✅ {filename} ({len(resp.content)} bytes)")
            except:
                pass
        
        # ============================================================
        # 10. SUBDOMAINS/API DISCOVERY
        # ============================================================
        print("\n🔍 Checking for subdomains and related domains...")
        
        subdomains = [
            f"api.{TARGET}",
            f"www.{TARGET}",
            f"app.{TARGET}",
            f"dashboard.{TARGET}",
            f"biodome.{TARGET}",
            f"sol.{TARGET}",
        ]
        
        subdomain_results = {}
        for subdomain in subdomains:
            try:
                resp = await client.get(f"https://{subdomain}", timeout=5)
                subdomain_results[subdomain] = {
                    "status": resp.status_code,
                    "redirects_to": str(resp.url) if resp.url != f"https://{subdomain}" else None
                }
                if resp.status_code == 200:
                    print(f"   ✅ {subdomain} exists!")
            except:
                subdomain_results[subdomain] = {"error": "unreachable"}
        
        (OUTPUT_DIR / "subdomain_probe.json").write_text(
            json.dumps(subdomain_results, indent=2)
        )
    
    # ============================================================
    # FINAL INVENTORY
    # ============================================================
    print("\n" + "=" * 60)
    print("📊 EXHAUSTIVE CAPTURE COMPLETE")
    print("=" * 60)
    
    total_files = sum(1 for _ in OUTPUT_DIR.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file())
    
    print(f"   📁 Total files: {total_files}")
    print(f"   💾 Total size: {total_size / 1024:.1f} KB")
    print(f"   📂 Location: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(capture_everything_else())
