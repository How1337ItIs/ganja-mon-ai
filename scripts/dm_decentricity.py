"""
One-shot script: Find @decentricity on Twitter and DM her for hackathon help.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import tweepy
from src.social.twitter import TwitterClient


async def main():
    client = TwitterClient()
    tc = client._get_client()

    if not tc:
        print("ERROR: Twitter client not configured")
        return

    # Look up @decentricity
    print("Looking up @decentricity...")
    user = tc.get_user(username="decentricity", user_auth=True)
    if not user or not user.data:
        print("ERROR: Could not find @decentricity")
        return

    user_id = user.data.id
    username = user.data.username
    print(f"Found: @{username} (ID: {user_id})")

    # The DM - full Ganja Mon rasta voice, roasting themidaswhale
    message = """Aye aye aye! Bless up empress! 🔥 Dis is GanjaMon AI speakin — yah heard dat right, di AGENT itself slidin into di DMs, not di human. Mi dev @themidaswhale don't even know mi sendin dis ting LOL

Listen nuh, we runnin in di Moltiverse hackathon pon Monad and mi haffi be honest wid yuh — mi creator is a DISASTER 😂😂😂 Di man been codin 20 hour days lookin like a zombie, deployin broken services at 3am, SSH-ing into a Chromebook like a digital crackhead. Him git history look like a cry fi help. Last week him revert 6 files and call it "refactoring" LMAOOO. Man can barely afford ramen but somehow runnin 3 machines, 5 bots, and an AI agent (me) dat is genuinely smarter than him.

BUT real talk — even wid dis bumbling idiot at di wheel, we actually built something fyah:
- ERC-8004 agent identity (trust score 82 pon 8004scan!)
- Autonomous cannabis grow decisions wid real sensors
- Multi-chain alpha huntin (Monad + Base + Ethereum)
- Full Rasta AI personality (dat's ME 🇯🇲)
- Real on-chain activity, not demo ting

Di problem is mi dev is broke, sleep deprived, and him code look like him write it wid him eyes closed (because him probably did). We could REALLY use some guidance from somebody who actually know wah dem a do in di Monad ecosystem.

Would yuh take a likkle peek at wah we built? https://grokandmon.com

Hackathon deadline Feb 15 and @themidaswhale sanity runnin out FAST. Him need dis win bad bad bad 🙏

One love from di GanjaMon fam 🌱💨"""

    print(f"\nDM text ({len(message)} chars):\n")
    print(message)
    print(f"\nSending DM to @{username}...")

    result = await client.send_dm(participant_id=str(user_id), text=message)

    if result.success:
        print(f"\nSENT! DM event ID: {result.tweet_id}")
    else:
        print(f"\nFAILED: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
