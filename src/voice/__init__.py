"""
Voice Module
============

Real-time voice transformation pipeline control + universal Ganja Mon personality.
"""

from .manager import VoicePipelineManager, get_voice_manager, VoiceEvent, VoiceStatus
from .personality import (
    VOICE_CORE,
    PATOIS_GUIDE,
    VOICE_DELIVERY,
    IDENTITY_CORE,
    HARD_RULES,
    TOKEN_KNOWLEDGE,
    get_social_prompt,
    get_tweet_prompt,
    get_tts_prompt,
    get_telegram_core,
    strip_llm_artifacts,
    strip_hashtags,
    enforce_voice,
)

__all__ = [
    "VoicePipelineManager", "get_voice_manager", "VoiceEvent", "VoiceStatus",
    "VOICE_CORE", "PATOIS_GUIDE", "VOICE_DELIVERY",
    "IDENTITY_CORE", "HARD_RULES", "TOKEN_KNOWLEDGE",
    "get_social_prompt", "get_tweet_prompt", "get_tts_prompt", "get_telegram_core",
    "strip_llm_artifacts", "strip_hashtags", "enforce_voice",
]
