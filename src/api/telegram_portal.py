"""
Telegram Portal API - Generate Secure Invite Links
===================================================

Endpoint that verifies CAPTCHA and generates one-time Telegram invite links.

Usage:
    POST /api/telegram/invite
    Body: {"captcha_token": "xxx"}
    Returns: {"invite_link": "https://t.me/+xxx"}
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Get from environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # Your private group chat ID
HCAPTCHA_SECRET = os.environ.get("HCAPTCHA_SECRET_KEY")


class InviteRequest(BaseModel):
    captcha_token: str
    source: str = "web"


async def verify_hcaptcha(token: str) -> bool:
    """Verify hCaptcha token"""
    if not HCAPTCHA_SECRET:
        # Dev mode - skip verification
        return True

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://hcaptcha.com/siteverify",
            data={
                "secret": HCAPTCHA_SECRET,
                "response": token
            }
        )
        result = response.json()
        return result.get("success", False)


async def create_telegram_invite() -> str:
    """Create one-time invite link via Telegram Bot API"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(status_code=500, detail="Telegram not configured")

    async with httpx.AsyncClient() as client:
        # Create invite link that expires in 24 hours, max 1 use
        response = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createChatInviteLink",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "expire_date": int(time.time()) + 86400,  # 24 hours
                "member_limit": 1,  # One-time use
                "name": f"Portal {datetime.now().strftime('%Y%m%d_%H%M')}"
            }
        )

        data = response.json()

        if data.get("ok"):
            return data["result"]["invite_link"]
        else:
            raise HTTPException(status_code=500, detail="Telegram API error")


@router.post("/api/telegram/invite")
async def generate_invite(request: InviteRequest):
    """
    Generate secure one-time Telegram invite link.
    Requires CAPTCHA verification.
    """
    # Verify CAPTCHA
    captcha_valid = await verify_hcaptcha(request.captcha_token)

    if not captcha_valid:
        raise HTTPException(status_code=400, detail="CAPTCHA verification failed")

    # Generate invite link
    try:
        invite_link = await create_telegram_invite()
        return {
            "success": True,
            "invite_link": invite_link,
            "expires_in": "24 hours",
            "uses": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add this to your main app.py:
# from .telegram_portal import router as telegram_router
# app.include_router(telegram_router)
