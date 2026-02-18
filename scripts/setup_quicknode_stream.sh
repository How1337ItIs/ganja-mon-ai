#!/bin/bash
# Setup QuickNode Streams for GrowRing Events on Monad
#
# Prerequisites:
# 1. QuickNode account with API key
# 2. Monad Mainnet endpoint on QuickNode
# 3. QUICKNODE_API_KEY set in .env
#
# Usage: ./scripts/setup_quicknode_stream.sh
#
# This creates a Stream that monitors all 3 GrowRing contracts on Monad
# and forwards matching events to our Cloudflare Worker webhook.

set -euo pipefail

# Load environment
source "$(dirname "$0")/../.env" 2>/dev/null || true

if [ -z "${QUICKNODE_API_KEY:-}" ]; then
  echo "ERROR: QUICKNODE_API_KEY not set in .env"
  echo "Get your API key from: https://dashboard.quicknode.com/api-keys"
  exit 1
fi

API_BASE="https://api.quicknode.com/streams/rest/v1"
WEBHOOK_URL="https://grokandmon.com/webhook/quicknode-stream"

# Base64 encode the filter function
FILTER_B64=$(base64 -w0 < "$(dirname "$0")/../cloudflare/quicknode-stream-filter.js")

echo "Creating QuickNode Stream for GrowRing events on Monad..."

RESPONSE=$(curl -s -X POST "${API_BASE}/streams" \
  -H "x-api-key: ${QUICKNODE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"GrowRing Events - Monad Mainnet\",
    \"network\": \"monad-mainnet\",
    \"dataset\": \"block_with_receipts\",
    \"filter_function\": \"${FILTER_B64}\",
    \"region\": \"us-east-1\",
    \"dataset_batch_size\": 1,
    \"include_stream_metadata\": true,
    \"destination\": {
      \"url\": \"${WEBHOOK_URL}\",
      \"compression\": \"none\",
      \"headers\": {
        \"Content-Type\": \"application/json\"
      },
      \"max_retry\": 3,
      \"retry_interval_sec\": 30,
      \"post_timeout_sec\": 30
    },
    \"status\": \"active\"
  }")

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Extract stream ID
STREAM_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
echo ""
echo "Stream ID: ${STREAM_ID}"
echo "Webhook: ${WEBHOOK_URL}"
echo ""
echo "Monitor at: https://dashboard.quicknode.com/streams"
echo ""
echo "Event signatures being watched:"
echo "  MilestoneMinted: 0xef2e64b382d24fff9ba66c43a7b16c65379eba5f3586b31bc014ccebd2e91f1c"
echo "  GrowStateUpdated: 0xc7d6f7db626b33182a5a7193002ea098ea96e9859ad0aef9206090309eea2af3"
echo "  Transfer (ERC-721): 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
echo "  AuctionCreated: 0xa9c8dfcda5664a5a124c713e386da27de87432d5b668e79458501eb296389ba7"
echo ""
echo "Contracts monitored:"
echo "  GrowRing:   0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b"
echo "  GrowOracle: 0xc532820dE55363633263f6a95Fa0762eD86E8425"
echo "  GrowAuction: 0xc07cA3A855b9623Db3aA733b86DAF2fa8EA9A5A4"
