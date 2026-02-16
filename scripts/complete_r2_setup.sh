#!/bin/bash
# Complete R2 Setup Script
# =========================
# Run this AFTER enabling R2 in Cloudflare Dashboard

set -e

echo "=========================================="
echo "Ultimate Dub Playlist - R2 Complete Setup"
echo "=========================================="
echo ""

# Check if R2 is enabled
echo "📋 Step 1: Checking R2 access..."
if ! wrangler r2 bucket list &>/dev/null; then
    echo "❌ R2 not enabled or not authenticated"
    echo ""
    echo "Please:"
    echo "1. Go to: https://dash.cloudflare.com/a33a705d5aebbca59de7eb146029869a"
    echo "2. Enable R2 (if not already)"
    echo "3. Set API token: export CLOUDFLARE_API_TOKEN='055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO'"
    echo "   OR run: wrangler login"
    exit 1
fi

echo "✅ R2 access confirmed"
echo ""

# Set API token if not already set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    export CLOUDFLARE_API_TOKEN="055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"
    echo "✅ API token set"
fi

# Step 1: Create bucket
echo "📦 Step 2: Creating R2 bucket..."
if wrangler r2 bucket create grokmon-dub-tracks 2>&1 | grep -q "already exists"; then
    echo "ℹ️  Bucket already exists"
else
    echo "✅ Bucket created"
fi
echo ""

# Step 2: Upload tracks
echo "📤 Step 3: Uploading tracks (33 files, ~3 GB)..."
echo "This will take 5-10 minutes..."
cd "$(dirname "$0")/.."
python scripts/setup_cloudflare_r2_dub.py
echo ""

# Step 3: Deploy worker
echo "🚀 Step 4: Deploying streaming worker..."
wrangler deploy cloudflare-worker-dub-stream.js --name grokmon-dub-stream
echo ""

echo "=========================================="
echo "✅ Upload & Deployment Complete!"
echo "=========================================="
echo ""
echo "⚠️  FINAL STEP: Add route in Cloudflare Dashboard"
echo ""
echo "1. Go to: https://dash.cloudflare.com/a33a705d5aebbca59de7eb146029869a/grokandmon.com"
echo "2. Navigate: Workers & Pages → Routes → Add route"
echo "3. Configure:"
echo "   - Route: grokandmon.com/api/playlist/dub/stream/*"
echo "   - Worker: grokmon-dub-stream"
echo "4. Save"
echo ""
echo "🧪 Then test:"
echo "   curl https://grokandmon.com/api/playlist/list"
echo ""
