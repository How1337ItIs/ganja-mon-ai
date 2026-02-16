#!/usr/bin/env python3
"""Post a tweet immediately - no prompts"""

import os
from dotenv import load_dotenv
load_dotenv()

import tweepy

# Tweet text - EDIT THIS
TWEET = """🌱 Mon is live. Grok is watching. The world's first AI-autonomous cannabis grow begins now. #GrokAndMon #AICannabis"""

# Get credentials
client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

print(f"Posting: {TWEET}\n")

try:
    response = client.create_tweet(text=TWEET)
    tweet_id = response.data['id']
    print(f"✓ SUCCESS!")
    print(f"🔗 https://twitter.com/GanjaMonAI/status/{tweet_id}")
except Exception as e:
    print(f"✗ Error: {e}")
