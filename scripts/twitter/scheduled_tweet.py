#!/usr/bin/env python3
"""Schedule a tweet for 3:20 PST with image"""

import os
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

import tweepy

# Tweet text - Rasta persona, no hashtags
TWEET = """Irie bredren! Goin live in one hour at 4:20 - might as well tune in, watch Mon grow, and hear some big tings comin. Bless up"""

# Image path
IMAGE_PATH = r"C:\Users\natha\Downloads\ganjafy_1769553386535.png"

# Target time: 3:20 PM PST (UTC-8)
TARGET_HOUR = 15
TARGET_MINUTE = 20
PST = timezone(timedelta(hours=-8))

def wait_until_target():
    """Wait until 3:20 PM PST"""
    while True:
        now = datetime.now(PST)
        if now.hour == TARGET_HOUR and now.minute >= TARGET_MINUTE:
            return
        if now.hour > TARGET_HOUR:
            return  # Already past target time

        remaining = (TARGET_HOUR * 60 + TARGET_MINUTE) - (now.hour * 60 + now.minute)
        print(f"[{now.strftime('%H:%M:%S')}] Waiting... {remaining} minutes until 3:20 PM PST")
        time.sleep(30)

def post_tweet():
    """Post the tweet with image"""
    # Auth for media upload (v1.1 API)
    auth = tweepy.OAuth1UserHandler(
        os.getenv("TWITTER_API_KEY"),
        os.getenv("TWITTER_API_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_SECRET")
    )
    api = tweepy.API(auth)

    # V2 client for posting
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
    )

    print(f"\nUploading image: {IMAGE_PATH}")
    media = api.media_upload(filename=IMAGE_PATH)
    print(f"Media ID: {media.media_id}")

    print(f"\nPosting tweet:\n{TWEET}\n")
    response = client.create_tweet(text=TWEET, media_ids=[media.media_id])
    tweet_id = response.data['id']

    print(f"SUCCESS!")
    print(f"https://twitter.com/GanjaMonAI/status/{tweet_id}")
    return tweet_id

if __name__ == "__main__":
    print("=" * 50)
    print("Scheduled Tweet - 3:20 PM PST")
    print("=" * 50)
    print(f"\nTweet: {TWEET}")
    print(f"Image: {IMAGE_PATH}")
    print()

    wait_until_target()

    now = datetime.now(PST)
    print(f"\n[{now.strftime('%H:%M:%S')}] TIME TO POST!")

    try:
        post_tweet()
    except Exception as e:
        print(f"ERROR: {e}")
