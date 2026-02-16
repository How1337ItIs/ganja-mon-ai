#!/usr/bin/env python3
"""Test post and immediately delete"""

import os
import time
from dotenv import load_dotenv
load_dotenv()

import tweepy

# Test tweet
TEST_TWEET = "🧪 Test tweet from Grok & Mon auto-posting system. Will delete in 5 seconds..."

print("=" * 60)
print("Test Post & Delete")
print("=" * 60)

# Create client
client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

print(f"\n1. Posting test tweet...")
print(f"   Text: {TEST_TWEET}")

try:
    # Post the tweet
    response = client.create_tweet(text=TEST_TWEET)
    tweet_id = response.data['id']

    print(f"\n✓ Tweet posted successfully!")
    print(f"   Tweet ID: {tweet_id}")
    print(f"   URL: https://twitter.com/GanjaMonAI/status/{tweet_id}")

    # Wait a moment
    print(f"\n2. Waiting 3 seconds before deleting...")
    time.sleep(3)

    # Delete the tweet
    print(f"\n3. Deleting tweet {tweet_id}...")
    client.delete_tweet(tweet_id)

    print(f"\n✓ Tweet deleted successfully!")
    print(f"\n" + "=" * 60)
    print("✓ TEST COMPLETE - Post & Delete both work!")
    print("=" * 60)
    print("\n🎉 Your Twitter auto-posting system is fully functional!")

except tweepy.Forbidden as e:
    print(f"\n✗ Error 403 Forbidden: {e}")
    print("\n⚠️  LIKELY ISSUE: App doesn't have write permissions")
    print("\nFIX:")
    print("1. Go to: https://developer.twitter.com/en/portal/dashboard")
    print("2. Click your app → Settings → User authentication settings")
    print("3. Click 'Set up' or 'Edit'")
    print("4. Change App permissions to 'Read and Write'")
    print("5. Save settings")
    print("6. Go to 'Keys and Tokens' tab")
    print("7. REGENERATE your Access Token & Secret (old ones won't work)")
    print("8. Update .env with the NEW tokens")

except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    print(f"   Type: {type(e).__name__}")
