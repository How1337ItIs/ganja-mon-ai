#!/usr/bin/env python3
"""
Grok API Test
=============
Tests connectivity to xAI Grok API with your new "mon" key.
"""

import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("XAI_API_KEY")

if not API_KEY:
    print("ERROR: XAI_API_KEY not set in .env")
    exit(1)

print("Testing xAI Grok API...")
print(f"  Key: {API_KEY[:12]}...{API_KEY[-8:]}")
print()

try:
    response = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json={
            "messages": [
                {
                    "role": "system",
                    "content": "You are Mon's Grok - a chill Jamaican cannabis cultivation AI. Keep responses brief and irie."
                },
                {
                    "role": "user", 
                    "content": "Say hi to your new plant baby named Mon! This is day 1."
                }
            ],
            "model": "grok-4-1-fast-non-reasoning",
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 200
        },
        timeout=120.0
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    
    if "choices" in data:
        print()
        print("=" * 50)
        print("GROK SAYS:")
        print("=" * 50)
        print(data["choices"][0]["message"]["content"])
        print()
        print("SUCCESS! Your Grok API key is working!")
        
        # Show usage
        if "usage" in data:
            usage = data["usage"]
            print(f"\nTokens used: {usage.get('total_tokens', 'N/A')}")
    else:
        print("Unexpected response:")
        print(json.dumps(data, indent=2))

except httpx.ReadTimeout:
    print("TIMEOUT: Request took too long (>120s)")
    print("The API might be slow during provisioning. Try again in a minute.")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
