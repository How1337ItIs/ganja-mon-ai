#!/usr/bin/env python3
"""
Stream Announcement Tweet Scheduler
===================================

Schedules tweets for the 4:20 EST stream on Twitch and X.
Run this and it will post automatically at the scheduled times.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# Direct import to avoid scheduler dependency
import importlib.util
spec = importlib.util.spec_from_file_location("twitter", Path(__file__).parent / "src" / "social" / "twitter.py")
twitter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twitter_module)
TwitterClient = twitter_module.TwitterClient

# Tweet content - Rasta voice, no hashtags, links in reply
PRESTREAM_TWEET = """Bredren! We goin live inna 5 minutes seen?

Grok & Mon - di world's first AI growin ganja autonomous.

Di plant vibes right, di AI reasonin proper. Come watch di ting unfold at 4:20.

Jah bless"""

PRESTREAM_REPLY = """Links fi di stream:

Twitch: twitch.tv/grokandmon
X/Twitter: right here @ganjamonai

Come reason wit us!"""

STREAM_START_TWEET = """WE LIVE NOW bredren!

Di AI runnin tings. Di plant growin irie. Come check di vibes.

Grok & Mon - where technology meet di herb.

4:20 and we blazin."""

STREAM_START_REPLY = """Watch di stream:

Twitch: twitch.tv/grokandmon
X: You already here fam!

Pull up and reason wit di rasta AI!"""


async def post_tweet(text: str, description: str, reply_to: str = None):
    """Post a tweet and report result. Returns tweet_id on success."""
    client = TwitterClient()

    if not client._configured:
        print(f"[MOCK] {description}: {text[:50]}...")
        return "mock_id_" + datetime.now().strftime("%H%M%S")

    try:
        tweepy_client = client._get_client()

        # Run in thread pool
        loop = asyncio.get_event_loop()
        if reply_to:
            response = await loop.run_in_executor(
                None,
                lambda: tweepy_client.create_tweet(text=text, in_reply_to_tweet_id=reply_to)
            )
        else:
            response = await loop.run_in_executor(
                None,
                lambda: tweepy_client.create_tweet(text=text)
            )

        tweet_id = response.data.get("id") if response.data else None

        if tweet_id:
            print(f"[POSTED] {description}")
            print(f"  Tweet ID: {tweet_id}")
            print(f"  URL: https://twitter.com/ganjamonai/status/{tweet_id}")
            return tweet_id
        else:
            print(f"[FAILED] {description}: No tweet ID returned")
            return None

    except Exception as e:
        print(f"[FAILED] {description}: {e}")
        return None


async def post_tweet_with_reply(main_text: str, reply_text: str, description: str):
    """Post a tweet and then reply to it with links"""
    print(f"\n[POSTING] {description}...")

    # Post main tweet
    tweet_id = await post_tweet(main_text, f"{description} (main)")

    if tweet_id:
        # Wait a moment then post reply
        await asyncio.sleep(2)
        await post_tweet(reply_text, f"{description} (reply)", reply_to=tweet_id)
        return True

    return False


async def run_scheduled_tweets():
    """Run the tweet scheduler"""

    # Target times (EST)
    now = datetime.now()
    today = now.date()

    # 4:15 PM EST for pre-stream
    prestream_time = datetime.combine(today, datetime.strptime("16:15", "%H:%M").time())

    # 4:20 PM EST for stream start
    stream_time = datetime.combine(today, datetime.strptime("16:20", "%H:%M").time())

    print("=" * 60)
    print("STREAM TWEET SCHEDULER")
    print("=" * 60)
    print(f"Current time: {now.strftime('%I:%M %p')}")
    print(f"Pre-stream tweet scheduled: {prestream_time.strftime('%I:%M %p')}")
    print(f"Stream start tweet scheduled: {stream_time.strftime('%I:%M %p')}")
    print("=" * 60)

    prestream_posted = False
    stream_posted = False

    # If times already passed, post immediately
    if now >= prestream_time and not prestream_posted:
        print("\n[!] Pre-stream time already passed - posting now...")
        prestream_posted = await post_tweet_with_reply(PRESTREAM_TWEET, PRESTREAM_REPLY, "Pre-stream announcement")

    if now >= stream_time and not stream_posted:
        print("\n[!] Stream time already passed - posting now...")
        stream_posted = await post_tweet_with_reply(STREAM_START_TWEET, STREAM_START_REPLY, "Stream start announcement")

    if prestream_posted and stream_posted:
        print("\n[DONE] All tweets posted!")
        return

    print("\nWaiting for scheduled times...")
    print("(Press Ctrl+C to cancel)\n")

    while not (prestream_posted and stream_posted):
        now = datetime.now()

        # Check pre-stream time
        if not prestream_posted and now >= prestream_time:
            print(f"\n[{now.strftime('%I:%M %p')}] Pre-stream time reached!")
            prestream_posted = await post_tweet_with_reply(PRESTREAM_TWEET, PRESTREAM_REPLY, "Pre-stream announcement")

        # Check stream time
        if not stream_posted and now >= stream_time:
            print(f"\n[{now.strftime('%I:%M %p')}] Stream time reached!")
            stream_posted = await post_tweet_with_reply(STREAM_START_TWEET, STREAM_START_REPLY, "Stream start announcement")

        # Show countdown
        if not prestream_posted:
            delta = prestream_time - now
            mins = int(delta.total_seconds() / 60)
            print(f"\r  Pre-stream in {mins} minutes...    ", end="", flush=True)
        elif not stream_posted:
            delta = stream_time - now
            mins = int(delta.total_seconds() / 60)
            print(f"\r  Stream start in {mins} minutes...  ", end="", flush=True)

        await asyncio.sleep(10)  # Check every 10 seconds

    print("\n\n[DONE] All tweets posted successfully!")


async def post_now():
    """Post both tweets immediately (for testing)"""
    print("Posting both tweets NOW...")
    await post_tweet_with_reply(PRESTREAM_TWEET, PRESTREAM_REPLY, "Pre-stream (immediate)")
    await asyncio.sleep(5)
    await post_tweet_with_reply(STREAM_START_TWEET, STREAM_START_REPLY, "Stream start (immediate)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Post immediately instead of waiting")
    parser.add_argument("--preview", action="store_true", help="Preview tweets without posting")
    args = parser.parse_args()

    if args.preview:
        print("=" * 60)
        print("TWEET PREVIEW - Rasta Style")
        print("=" * 60)
        print("\n[4:15 PM] PRE-STREAM TWEET:")
        print("-" * 40)
        print(PRESTREAM_TWEET)
        print(f"\n({len(PRESTREAM_TWEET)} chars)")
        print("\n  [REPLY with links]:")
        print("  " + PRESTREAM_REPLY.replace("\n", "\n  "))
        print(f"\n  ({len(PRESTREAM_REPLY)} chars)")
        print("\n[4:20 PM] STREAM START TWEET:")
        print("-" * 40)
        print(STREAM_START_TWEET)
        print(f"\n({len(STREAM_START_TWEET)} chars)")
        print("\n  [REPLY with links]:")
        print("  " + STREAM_START_REPLY.replace("\n", "\n  "))
        print(f"\n  ({len(STREAM_START_REPLY)} chars)")
    elif args.now:
        asyncio.run(post_now())
    else:
        asyncio.run(run_scheduled_tweets())
