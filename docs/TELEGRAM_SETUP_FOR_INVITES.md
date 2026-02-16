# How to get a Telegram API key, set up Telethon, and invite people to your group (with code)

A step-by-step guide so you can run a script (or give Claude/code access) to invite a list of people to your Telegram group using your **user account** (not a bot). Bots can’t add members; you need the **Telethon** library with your own API credentials and a logged-in session.

---

## 1. Get your Telegram API key (api_id + api_hash)

1. Open **https://my.telegram.org** in your browser.
2. Log in with your **phone number** (the one linked to your Telegram account). You’ll get a code in Telegram — enter it.
3. Click **“API development tools”**.
4. If asked, fill in **App title** and **Short name** (e.g. “My Invite Script”, “invites”). Leave **URL** and **Platform** empty if you want.
5. Click **“Create application”**.
6. You’ll see:
   - **App api_id** — a number like `12345678`
   - **App api_hash** — a long string like `a1b2c3d4e5f6...`

   **Keep these secret.** Don’t commit them to git or share them. You’ll put them in a `.env` file or pass them into your script.

---

## 2. Set up Python and Telethon

- **Python:** Make sure Python 3.8+ is installed (`python --version` or `python3 --version`).
- **Telethon:** Install in a virtual environment (recommended):

```bash
# Create a folder for the project
mkdir telegram-invites && cd telegram-invites

# Optional but recommended: virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Telethon
pip install telethon
```

---

## 3. First run: log in once (create the session)

Telethon needs to log in **as you** once. After that it saves a **session file** so the script can run without entering the code again.

Create a file `auth_once.py`:

```python
# auth_once.py — run this ONCE to log in and create the session file
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Replace with your values from my.telegram.org (or use env vars)
API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))   # e.g. 12345678
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")     # e.g. "a1b2c3d4..."
if API_ID == 0 or not API_HASH:
    raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH (from my.telegram.org)")

# Session file: same directory, name "my_account"
SESSION_NAME = "my_account"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def main():
    await client.start()
    # This will prompt for phone number and code (and 2FA password if you have it)
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username})")
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

- Replace `YOUR_API_ID` and `YOUR_API_HASH` with your real values, or set env vars:

  ```bash
  set TELEGRAM_API_ID=12345678
  set TELEGRAM_API_HASH=your_api_hash_here
  ```

  (On macOS/Linux use `export` instead of `set`.)

- Run:

  ```bash
  python auth_once.py
  ```

- When asked:
  - Enter your **phone number** (with country code, e.g. `+1234567890`).
  - Enter the **code** Telegram sends you.
  - If you have **2FA**, enter your cloud password.

After this, you’ll see a file like `my_account.session` in the same folder. **Keep it private** (don’t commit to git). From now on, your script can use this file to act as you without asking for the code again.

---

## 4. Script to invite people to your group

You need to be **admin** of the group (with permission to add users).  
**Supergroups/channels** use one method; **basic groups** use another. The script below uses the supergroup method; if your group is a basic group, see the note at the end.

Create `invite_to_group.py`:

```python
# invite_to_group.py — invite a list of users to your Telegram group
import asyncio
import os
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputUser
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, UserNotParticipantError

# Same as in auth_once.py — set these or use .env
API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
if API_ID == 0 or not API_HASH:
    raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH")
SESSION_NAME = "my_account"

# Your group: use @username or the group ID (e.g. -1001234567890 for supergroups)
GROUP = os.environ.get("TELEGRAM_GROUP", "@YourGroupUsername")  # or -1001234567890

# List of usernames (without @) or "username1, username2, ..." in one string
USERNAMES_STR = os.environ.get(
    "TELEGRAM_USERNAMES",
    "user1, user2, user3"
)
USERNAMES = [u.strip().lstrip("@") for u in USERNAMES_STR.split(",") if u.strip()]

async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    if not await client.is_user_authorized():
        print("Not logged in. Run auth_once.py first.")
        return

    for username in USERNAMES:
        try:
            # Resolve user and add to channel/group (supergroup)
            await client(InviteToChannelRequest(
                channel=GROUP,
                users=[username]
            ))
            print(f"Invited: {username}")
        except FloodWaitError as e:
            print(f"Rate limit: wait {e.seconds}s then retry.")
            await asyncio.sleep(e.seconds)
            # Retry this user
            await client(InviteToChannelRequest(channel=GROUP, users=[username]))
            print(f"Invited: {username}")
        except UserPrivacyRestrictedError:
            print(f"Skip (privacy): {username}")
        except Exception as e:
            print(f"Failed {username}: {e}")

        # Be nice to Telegram: short delay between invites
        await asyncio.sleep(2)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

- Set **GROUP** (or `TELEGRAM_GROUP`) to your group’s **@username** or its **numeric ID** (supergroups often look like `-1001234567890`).
- Set **USERNAMES** (or `TELEGRAM_USERNAMES`) to a comma-separated list of usernames (with or without `@`).

Run:

```bash
python invite_to_group.py
```

No login prompt should appear if `my_account.session` is there and still valid.

---

## 5. “Giving Claude (or any code) access” to Telegram

What this usually means:

1. **You** get the API key (Step 1) and run **auth_once.py** once on your machine (Step 3). That creates `my_account.session`.
2. You keep **api_id**, **api_hash**, and the **session file** secret (e.g. in `.env` and `.gitignore`).
3. Any script (written by you, Claude, or someone else) that uses the same **session name** + **api_id** + **api_hash** can then act as your account from that machine — including inviting people.

So “giving Claude code access” = **Claude writes the script**, and **you** run it on your computer (or a server you control) where the session file and env vars are set. You never give Claude your session file or api_hash; you only run the code in an environment where those are already configured.

**Security:**

- Don’t commit `*.session`, `.env`, or any file containing `API_ID`/`API_HASH`.
- Add to `.gitignore`: `*.session`, `.env`.
- Only run scripts you trust; they have full control of your Telegram account.

---

## 6. Optional: use a .env file

Create a `.env` in the same folder:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_GROUP=@YourGroupUsername
TELEGRAM_USERNAMES=user1, user2, user3
```

Then at the top of your scripts:

```python
from dotenv import load_dotenv
load_dotenv()
```

Install: `pip install python-dotenv`. Now you don’t need to put credentials in the script.

---

## 7. If your group is a basic group (not a supergroup)

If you get an error like “Cannot cast InputPeerChat to InputChannel”, your group is a **basic group**. Convert it to a **supergroup** (Group Info → Edit → Group Type → “Turn into supergroup”) and use the script above. Alternatively, for basic groups you’d use `AddChatUserRequest` instead of `InviteToChannelRequest` (different Telethon method); supergroups are simpler and support more members.

---

## Quick checklist for your friend

1. Get **api_id** and **api_hash** from https://my.telegram.org (API development tools).
2. Install Python 3.8+ and run: `pip install telethon`.
3. Run **auth_once.py** once (with his api_id/api_hash), log in with phone + code (+ 2FA if enabled).
4. Put his group (@username or ID) and list of usernames into **invite_to_group.py** (or `.env`).
5. Run **invite_to_group.py**; it will invite using his account. Keep `.session` and API keys out of git and only run the script on a trusted machine.

That’s it. After that, any “code that has access” just means code that runs in an environment where the same session and API credentials are available.
