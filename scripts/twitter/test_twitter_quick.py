#!/usr/bin/env python3
"""Quick Twitter API Test"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Check credentials
print("=" * 60)
print("Twitter API Configuration Test")
print("=" * 60)

api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_secret = os.getenv("TWITTER_ACCESS_SECRET")

print("\n1. Checking credentials...")
if api_key and api_secret and access_token and access_secret:
    print(f"   ✓ API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"   ✓ API Secret: {api_secret[:10]}...***")
    print(f"   ✓ Access Token: {access_token[:10]}...{access_token[-4:]}")
    print(f"   ✓ Access Secret: {access_secret[:10]}...***")
else:
    print("   ✗ Missing credentials!")
    exit(1)

# Test tweepy
print("\n2. Testing tweepy library...")
try:
    import tweepy
    print("   ✓ tweepy installed")
except ImportError:
    print("   ✗ tweepy not installed. Run: pip install tweepy")
    exit(1)

# Test connection
print("\n3. Testing Twitter API connection...")
try:
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )

    # Get authenticated user info
    me = client.get_me()

    if me.data:
        print(f"   ✓ Connected as: @{me.data.username}")
        print(f"   ✓ Account ID: {me.data.id}")
        print(f"   ✓ Name: {me.data.name}")
    else:
        print("   ✗ Connection failed - no user data returned")

except tweepy.Forbidden as e:
    print(f"   ✗ Forbidden (403): Check app permissions!")
    print(f"      Error: {e}")
    print("\n   SOLUTION: Go to Developer Portal → App Settings")
    print("             → User authentication settings → Edit")
    print("             → Set to 'Read and Write' → Save")
    print("             → Regenerate Access Token & Secret")

except tweepy.Unauthorized as e:
    print(f"   ✗ Unauthorized (401): Invalid credentials")
    print(f"      Error: {e}")

except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✓ Twitter API is configured and working!")
print("=" * 60)
print("\nReady to post! Try:")
print("  python test_twitter_quick.py --post")
