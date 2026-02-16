"""
Configuration
=============

Typed configuration from .env via Pydantic BaseSettings.
Single source of truth for all config values.

Usage:
    settings = get_settings()
    print(settings.xai_api_key)
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration loaded from .env at startup."""

    # --- xAI Grok API ---
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    xai_model: str = Field(default="grok-4.1-fast", alias="XAI_MODEL")
    xai_vision_model: str = Field(default="grok-4", alias="XAI_VISION_MODEL")

    # --- Hardware ---
    govee_api_key: str = Field(default="", alias="GOVEE_API_KEY")
    govee_device_model: str = Field(default="H5179", alias="GOVEE_DEVICE_MODEL")
    govee_device_id: str = Field(default="", alias="GOVEE_DEVICE_ID")
    govee_co2_device_id: str = Field(default="", alias="GOVEE_CO2_DEVICE_ID")
    ecowitt_ip: str = Field(default="", alias="ECOWITT_IP")
    kasa_light_ip: str = Field(default="", alias="KASA_LIGHT_IP")
    kasa_exhaust_ip: str = Field(default="", alias="KASA_EXHAUST_IP")
    kasa_pump_ip: str = Field(default="", alias="KASA_PUMP_IP")

    # --- Orchestrator ---
    sensor_interval_seconds: int = Field(default=120, alias="SENSOR_INTERVAL_SECONDS")
    ai_interval_seconds: int = Field(default=1800, alias="AI_INTERVAL_SECONDS")
    plant_name: str = Field(default="Mon", alias="PLANT_NAME")

    # --- Web server ---
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # --- Social ---
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="3584948806", alias="TELEGRAM_CHAT_ID")
    farcaster_fid: int = Field(default=2696987, alias="FID")

    # --- Trading agent ---
    min_confidence_to_trade: float = Field(default=0.15, alias="MIN_CONFIDENCE_TO_TRADE")
    reasoner_provider: str = Field(default="auto", alias="REASONER_PROVIDER")

    # --- Email ---
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    agent_email: str = Field(default="agent@grokandmon.com", alias="AGENT_EMAIL")

    # --- Blockchain ---
    private_key: str = Field(default="", alias="PRIVATE_KEY")
    monad_rpc: str = Field(default="https://monad-mainnet.chainstacklabs.com", alias="MONAD_RPC")
    base_rpc: str = Field(default="https://base.publicrpc.com", alias="BASE_RPC")

    # --- IPFS / Pinata ---
    pinata_jwt: str = Field(default="", alias="PINATA_JWT")

    # --- Cloudflare ---
    cloudflare_api_token: str = Field(default="", alias="CLOUDFLARE_API_TOKEN")
    cloudflare_account_id: str = Field(default="", alias="CLOUDFLARE_ACCOUNT_ID")

    # --- Allium ---
    allium_api_key: str = Field(default="", alias="ALLIUM_API_KEY")

    # --- Gemini (Nano Banana art generation) ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # --- GrowRing NFT contracts ---
    growring_address: str = Field(default="", alias="GROWRING_ADDRESS")
    grow_oracle_address: str = Field(default="", alias="GROW_ORACLE_ADDRESS")
    grow_auction_address: str = Field(default="", alias="GROW_AUCTION_ADDRESS")
    grow_start_date: str = Field(default="2026-02-01", alias="GROW_START_DATE")

    # --- $GANJA Token ---
    ganja_token_address: str = Field(
        default="0x86C5F6342Dc1F7322AEcf1Cb540075E99e177777",
        alias="GANJA_TOKEN_ADDRESS",
    )
    mon_token_address: str = Field(
        default="0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b",
        alias="MON_TOKEN_ADDRESS",
    )
    ganja_burn_address: str = Field(
        default="0x000000000000000000000000000000000000dEaD",
        alias="GANJA_BURN_ADDRESS",
    )
    ganja_burn_ratio: float = Field(default=0.5, alias="GANJA_BURN_RATIO")

    model_config = {
        "env_file": str(Path(__file__).parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings()
