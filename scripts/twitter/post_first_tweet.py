#!/usr/bin/env python3
"""Post Mon's First Tweet!"""

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

try:
    import tweepy
except ImportError:
    print("Installing tweepy...")
    import subprocess
    subprocess.run(["pip", "install", "tweepy"], check=True)
    import tweepy


async def post_first_tweet():
    """Post Mon's introduction tweet"""

    # Get credentials
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")

    # Create client
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )

    # First tweet options
    tweets = {
        "1": "🌱 Mon is live. Grok is watching. The world's first AI-autonomous cannabis grow begins now. #GrokAndMon #AICannabis",
        "2": "Day 1 under AI control 🤖🌱\n\nMon's fate is in Grok's hands now. Temperature, humidity, light - all decided by artificial intelligence.\n\nWatch it happen live: grokandmon.com\n\n#AIGrow #Cannabis",
        "3": "Yo, it's Mon here! 🌱 Well, technically it's Grok speaking for Mon...\n\nI'm an AI managing a real cannabis plant. Every decision - autonomous. Every adjustment - calculated.\n\nThis is precision agriculture meets artificial intelligence. Let's grow. #GrokAndMon",
        "4": "🤖 AI-controlled cannabis cultivation experiment starting NOW\n\n✓ Real sensors\n✓ Real plant (Mon)\n✓ Real autonomous decisions\n✓ Full transparency\n\nGrok vs Nature. Let's see who wins.\n\ngrokandmon.com #AICannabis #SmartGrow"
    }

    print("=" * 60)
    print("Post Mon's First Tweet!")
    print("=" * 60)
    print("\nChoose your first tweet:\n")
    for key, tweet in tweets.items():
        print(f"\n[{key}] {tweet}")
        print(f"    ({len(tweet)} chars)\n")

    choice = input("\nEnter your choice (1-4) or 'custom' to write your own: ").strip()

    if choice == "custom":
        tweet_text = input("\nEnter your custom tweet (max 280 chars): ").strip()
        if len(tweet_text) > 280:
            print("Too long! Truncating...")
            tweet_text = tweet_text[:277] + "..."
    elif choice in tweets:
        tweet_text = tweets[choice]
    else:
        print("Invalid choice. Using default...")
        tweet_text = tweets["1"]

    print(f"\n📝 Ready to post:\n\n{tweet_text}\n")
    confirm = input("Post this tweet? (yes/no): ").strip().lower()

    if confirm == "yes":
        print("\n🚀 Posting...")

        try:
            response = client.create_tweet(text=tweet_text)
            tweet_id = response.data['id']

            print(f"\n✓ POSTED SUCCESSFULLY!")
            print(f"\n🔗 https://twitter.com/GanjaMonAI/status/{tweet_id}")
            print("\n🎉 Mon's first tweet is live!")

        except tweepy.Forbidden as e:
            print(f"\n✗ Error 403 Forbidden: {e}")
            print("\nLikely cause: App doesn't have write permissions")
            print("\nFIX:")
            print("1. Go to https://developer.twitter.com/en/portal/dashboard")
            print("2. Click your app → Settings")
            print("3. User authentication settings → Edit")
            print("4. Change to 'Read and Write'")
            print("5. Regenerate Access Token & Secret")
            print("6. Update .env file with new tokens")

        except Exception as e:
            print(f"\n✗ Error: {e}")

    else:
        print("\nCancelled. No tweet posted.")

if __name__ == "__main__":
    asyncio.run(post_first_tweet())
