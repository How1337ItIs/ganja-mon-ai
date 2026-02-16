#!/bin/bash
#
# Update Webcam Cache in Cloudflare KV
# =====================================
# Fetches latest webcam image from origin and stores in KV namespace
#
# Run this manually or via cron every 30-60 seconds

set -e

CLOUDFLARE_API_TOKEN="055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"
ACCOUNT_ID="a33a705d5aebbca59de7eb146029869a"
NAMESPACE_ID="5fb7f823abbe468cb8a8e25b1211e9c2"
ORIGIN_URL="http://192.168.125.128:8000"

# Fetch webcam image from origin (via Chromebook SSH)
echo "[*] Fetching webcam image from origin..."
sshpass -p 'c1@ud3__' ssh natha@chromebook.lan "curl -s http://localhost:8000/api/webcam/latest" > /tmp/webcam_latest.jpg

if [ ! -s /tmp/webcam_latest.jpg ]; then
    echo "[!] Failed to fetch webcam image"
    exit 1
fi

echo "[*] Image size: $(ls -lh /tmp/webcam_latest.jpg | awk '{print $5}')"

# Upload to KV namespace
echo "[*] Uploading to Cloudflare KV..."
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/storage/kv/namespaces/$NAMESPACE_ID/values/webcam_latest" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: image/jpeg" \
  --data-binary @/tmp/webcam_latest.jpg > /dev/null

# Update timestamp
TIMESTAMP=$(date +%s)000  # JavaScript timestamp (milliseconds)
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/storage/kv/namespaces/$NAMESPACE_ID/values/last_update" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: text/plain" \
  --data "$TIMESTAMP" > /dev/null

echo "[✓] Webcam cache updated successfully"
echo "[*] Test: curl -I https://grokandmon.com/api/webcam/latest"
