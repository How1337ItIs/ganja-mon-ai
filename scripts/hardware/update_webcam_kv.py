#!/usr/bin/env python3
"""
Update Cloudflare KV with latest webcam image
Run this on the Chromebook via cron every minute
"""
import requests
import time

# Configuration
CLOUDFLARE_API_TOKEN = "055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"
ACCOUNT_ID = "a33a705d5aebbca59de7eb146029869a"
NAMESPACE_ID = "5fb7f823abbe468cb8a8e25b1211e9c2"
ORIGIN_URL = "http://localhost:8000/api/webcam/latest"

def update_webcam_cache():
    """Fetch webcam image and upload to KV"""
    try:
        # Fetch webcam image from origin
        print("[*] Fetching webcam image from origin...")
        response = requests.get(ORIGIN_URL, timeout=5)
        response.raise_for_status()
        image_data = response.content
        print(f"[*] Image size: {len(image_data)} bytes")

        # Upload to KV
        print("[*] Uploading to Cloudflare KV...")
        kv_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{NAMESPACE_ID}/values/webcam_latest"
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "image/jpeg"
        }

        kv_response = requests.put(kv_url, headers=headers, data=image_data)
        kv_response.raise_for_status()

        # Update timestamp
        timestamp = str(int(time.time() * 1000))  # JavaScript timestamp
        ts_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{NAMESPACE_ID}/values/last_update"
        ts_headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "text/plain"
        }

        ts_response = requests.put(ts_url, headers=ts_headers, data=timestamp)
        ts_response.raise_for_status()

        print("[✓] Webcam cache updated successfully!")
        return True

    except Exception as e:
        print(f"[!] Error updating cache: {e}")
        return False

if __name__ == "__main__":
    success = update_webcam_cache()
    exit(0 if success else 1)
