#!/bin/bash
# Deploy Ganja Mon Translator to Cloudflare

# Check if logged in
npx wrangler whoami > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "⚠️  You are not logged in to Cloudflare."
  echo "👉 Please run: npx wrangler login"
  exit 1
fi

# Load API Key from rasta-voice/.env
if [ -f "rasta-voice/.env" ]; then
    export $(grep -v '^#' rasta-voice/.env | grep 'XAI_API_KEY' | xargs)
fi

if [ -z "$XAI_API_KEY" ]; then
  echo "❌ Error: XAI_API_KEY not found in rasta-voice/.env"
  exit 1
fi

echo "🌿 Deploying Ganja Mon Translator Worker..."
npx wrangler deploy -c wrangler-translator.toml

echo "🔑 Uploading XAI_API_KEY to Cloudflare..."
echo "$XAI_API_KEY" | npx wrangler secret put XAI_API_KEY -c wrangler-translator.toml

echo ""
echo "✅ Success! Access the dashboard here:"
echo "👉 https://grokandmon.com/ganjamontexttranslator"
