#!/bin/bash
# Quick R2 Setup Script for Dub Playlist
# =======================================

set -e

echo "=========================================="
echo "Ultimate Dub Playlist - R2 Setup"
echo "=========================================="
echo ""

# Check wrangler
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler not found. Installing..."
    npm install -g wrangler
    echo "✅ Wrangler installed"
    echo ""
    echo "⚠️  Please run 'wrangler login' first, then re-run this script"
    exit 1
fi

echo "✅ Wrangler found: $(wrangler --version)"
echo ""

# Step 1: Create R2 bucket
echo "📦 Step 1: Creating R2 bucket..."
if wrangler r2 bucket create grokmon-dub-tracks 2>&1 | grep -q "already exists"; then
    echo "ℹ️  Bucket already exists"
else
    echo "✅ Bucket created"
fi
echo ""

# Step 2: Upload tracks
echo "📤 Step 2: Uploading tracks..."
cd "$(dirname "$0")/.."
python scripts/setup_cloudflare_r2_dub.py
echo ""

# Step 3: Deploy worker
echo "🚀 Step 3: Deploying streaming worker..."
wrangler deploy cloudflare-worker-dub-stream.js --name grokmon-dub-stream
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Add route in Cloudflare Dashboard:"
echo "   1. Go to: Workers & Pages → Routes → Add route"
echo "   2. Pattern: grokandmon.com/api/playlist/dub/stream/*"
echo "   3. Worker: grokmon-dub-stream"
echo ""
echo "🧪 Test it:"
echo "   curl https://grokandmon.com/api/playlist/list"
echo ""
