#!/usr/bin/env python3
"""
Test Twitter/X Auto-Posting System
===================================

Run this after adding Twitter API keys to .env to verify everything works.

Usage:
    python test_twitter_posting.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from src.social.manager import MonSocialManager


async def test_twitter_setup():
    """Test the Twitter posting system"""

    print("=" * 60)
    print("Grok & Mon - Twitter/X Posting Test")
    print("=" * 60)

    manager = MonSocialManager()

    # Check configuration
    print("\n1. Checking Twitter API configuration...")
    stats = manager.get_stats()

    if stats["twitter_configured"]:
        print("   ✓ Twitter API credentials found!")
    else:
        print("   ✗ Twitter API NOT configured")
        print("\n   You need to add these to .env:")
        print("     TWITTER_API_KEY")
        print("     TWITTER_API_SECRET")
        print("     TWITTER_ACCESS_TOKEN")
        print("     TWITTER_ACCESS_SECRET")
        print("\n   Get them at: https://developer.twitter.com")
        return False

    # Test Grok post generation
    print("\n2. Testing Grok AI post generation...")
    try:
        post = await manager.xai.generate_mon_post(
            day=7,
            vpd=0.95,
            health="GOOD",
            stage="clone",
            event="Roots showing at clone collar!"
        )
        print(f"   ✓ Generated post:")
        print(f"     \"{post.text}\"")
    except Exception as e:
        print(f"   ✗ Grok generation failed: {e}")
        return False

    # Ask user if they want to post a test tweet
    print("\n3. Ready to post test tweet?")
    print(f"   Tweet: \"{post.text}\"")
    response = input("\n   Post this to X? (yes/no): ").strip().lower()

    if response == "yes":
        print("\n   Posting to X...")
        result = await manager.post_daily_update(
            day=7,
            vpd=0.95,
            health="GOOD",
            stage="clone",
            event="Roots showing at clone collar!",
            force=True  # Bypass rate limiting for test
        )

        if result.posted:
            print(f"   ✓ Posted successfully!")
            print(f"     Tweet ID: {result.tweet_id}")
            print(f"     URL: https://twitter.com/GrokAndMon/status/{result.tweet_id}")
        else:
            print(f"   ✗ Post failed: {result.error}")
            return False
    else:
        print("   Skipped actual posting")

    # Show stats
    print("\n4. System Stats:")
    print(f"   Twitter configured: {stats['twitter_configured']}")
    print(f"   Total posts: {stats['total_posts']}")
    print(f"   Last post: {stats['last_post'] or 'Never'}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    asyncio.run(test_twitter_setup())
