#!/usr/bin/env python3
"""
Post CoinGecko Verification Tweet
Ticket: CL3101260003
"""

import os
import sys
from dotenv import load_dotenv
import tweepy

# Load environment variables
load_dotenv()

def post_verification_tweet():
    """Post the CoinGecko verification tweet"""
    
    # Verification tweet text
    tweet_text = """🌿 Ganja Mon ($MON) CoinGecko Listing Application

We've submitted our listing request to @coingecko!

Request ID: CL3101260003

$MON is the first AI-autonomous cannabis cultivation system on blockchain, powered by @xai's Grok.

🔗 Website: https://grokandmon.com
📊 DexScreener: https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
📜 Contract: 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b

#GrokAndMon #Monad #CoinGecko"""

    print("=" * 60)
    print("CoinGecko Verification Tweet")
    print("=" * 60)
    print("\nTweet text:")
    print("-" * 60)
    print(tweet_text)
    print("-" * 60)
    print(f"\nCharacter count: {len(tweet_text)}")
    
    # Get credentials from environment
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("\n❌ ERROR: Missing Twitter credentials in .env file")
        print("Required:")
        print("  - TWITTER_API_KEY")
        print("  - TWITTER_API_SECRET")
        print("  - TWITTER_ACCESS_TOKEN")
        print("  - TWITTER_ACCESS_SECRET")
        return False
    
    try:
        # Initialize Tweepy client (v2 API)
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        print("\n✅ Twitter client initialized")
        print("📤 Posting tweet...")
        
        # Post the tweet
        response = client.create_tweet(text=tweet_text)
        
        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/ganjamonai/status/{tweet_id}"
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Tweet posted!")
        print("=" * 60)
        print(f"\nTweet ID: {tweet_id}")
        print(f"Tweet URL: {tweet_url}")
        print("\n📌 NEXT STEPS:")
        print("1. Go to Twitter and PIN this tweet to your profile")
        print("2. Share in Telegram: https://t.me/ganjamonai")
        print("3. Wait 5-7 business days for CoinGecko review")
        print("\n" + "=" * 60)
        
        return True
        
    except tweepy.TweepyException as e:
        print(f"\n❌ ERROR posting tweet: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = post_verification_tweet()
    sys.exit(0 if success else 1)
