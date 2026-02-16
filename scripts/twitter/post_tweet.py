#!/usr/bin/env python3
"""
Post a tweet using the Twitter API v2.

Usage:
    python3 post_tweet.py "Tweet text here"
    python3 post_tweet.py --text "Tweet text here"
    python3 post_tweet.py --text "Tweet text" --image /path/to/image.png

Environment variables required:
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

Exit codes:
    0 = success (prints tweet URL)
    1 = error (prints error message)
"""
import os
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="Post a tweet")
    parser.add_argument("text", nargs="?", help="Tweet text (positional)")
    parser.add_argument("--text", "-t", dest="text_opt", help="Tweet text (flag)")
    parser.add_argument("--image", "-i", help="Path to image file")
    args = parser.parse_args()

    text = args.text_opt or args.text
    if not text:
        print("ERROR: No tweet text provided", file=sys.stderr)
        sys.exit(1)

    if len(text) > 280:
        print(f"ERROR: Tweet is {len(text)} chars (max 280)", file=sys.stderr)
        sys.exit(1)

    # Check env vars
    required = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    try:
        import tweepy
    except ImportError:
        print("ERROR: tweepy not installed. Run: pip install tweepy", file=sys.stderr)
        sys.exit(1)

    # Auth
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
    )

    media_ids = None

    # Upload image if provided
    if args.image:
        if not os.path.exists(args.image):
            print(f"ERROR: Image file not found: {args.image}", file=sys.stderr)
            sys.exit(1)
        auth = tweepy.OAuth1UserHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET"),
        )
        api = tweepy.API(auth)
        media = api.media_upload(filename=args.image)
        media_ids = [media.media_id]

    # Post tweet
    response = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = response.data["id"]
    url = f"https://x.com/GanjaMonAI/status/{tweet_id}"

    result = {"success": True, "tweet_id": tweet_id, "url": url, "text": text}
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

