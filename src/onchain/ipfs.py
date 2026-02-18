"""
IPFS Pinning via Pinata
========================

Pins images and metadata to IPFS using the Pinata v2 API.
Returns IPFS URIs (ipfs://...) for on-chain storage.
"""

import json
import logging
from pathlib import Path

import httpx

from src.core.config import get_settings

logger = logging.getLogger(__name__)

PINATA_UPLOAD_API = "https://uploads.pinata.cloud/v3/files"


async def pin_image(image_path: Path, name: str) -> str:
    """Pin an image file to IPFS via Pinata v2 API.

    Args:
        image_path: Path to the image file
        name: Descriptive name for the pin

    Returns:
        IPFS URI string (ipfs://...)
    """
    settings = get_settings()
    if not settings.pinata_jwt:
        logger.warning("PINATA_JWT not set, returning placeholder URI")
        return f"ipfs://placeholder-{name}"

    suffix = image_path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp"}.get(suffix, "image/png")

    async with httpx.AsyncClient(timeout=120) as client:
        with open(image_path, "rb") as f:
            response = await client.post(
                PINATA_UPLOAD_API,
                headers={"Authorization": f"Bearer {settings.pinata_jwt}"},
                files={"file": (f"{name}{suffix}", f, mime)},
                data={"name": name, "network": "public"},
            )
            response.raise_for_status()
            result = response.json()

    cid = result["data"]["cid"]
    uri = f"ipfs://{cid}"
    logger.info(f"Pinned {name} -> {uri}")
    return uri


async def pin_metadata(metadata: dict, name: str) -> str:
    """Pin JSON metadata to IPFS via Pinata v2 API.

    Args:
        metadata: The metadata dictionary (follows OpenSea/ERC-721 standard)
        name: Descriptive name for the pin

    Returns:
        IPFS URI string (ipfs://...)
    """
    settings = get_settings()
    if not settings.pinata_jwt:
        logger.warning("PINATA_JWT not set, returning placeholder URI")
        return f"ipfs://placeholder-meta-{name}"

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(metadata, tmp)
        tmp_path = tmp.name

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(tmp_path, "rb") as f:
                response = await client.post(
                    PINATA_UPLOAD_API,
                    headers={"Authorization": f"Bearer {settings.pinata_jwt}"},
                    files={"file": (f"{name}.json", f, "application/json")},
                    data={"name": name, "network": "public"},
                )
                response.raise_for_status()
                result = response.json()
    finally:
        import os
        os.unlink(tmp_path)

    cid = result["data"]["cid"]
    uri = f"ipfs://{cid}"
    logger.info(f"Pinned metadata {name} -> {uri}")
    return uri


def ipfs_to_gateway(ipfs_uri: str, gateway: str = "https://gateway.pinata.cloud/ipfs/") -> str:
    """Convert an IPFS URI to an HTTP gateway URL for display."""
    if ipfs_uri.startswith("ipfs://"):
        return gateway + ipfs_uri[7:]
    return ipfs_uri
