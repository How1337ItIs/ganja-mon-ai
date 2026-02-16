"""
IPFS Pinning via Pinata
========================

Pins images and metadata to IPFS using the Pinata API.
Returns IPFS URIs (ipfs://...) for on-chain storage.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

import httpx

from src.core.config import get_settings

logger = logging.getLogger(__name__)

PINATA_API = "https://api.pinata.cloud"


async def pin_image(image_path: Path, name: str) -> str:
    """Pin an image file to IPFS via Pinata.

    Args:
        image_path: Path to the image file
        name: Descriptive name for the pin

    Returns:
        IPFS URI string (ipfs://Qm...)
    """
    settings = get_settings()
    if not settings.pinata_jwt:
        logger.warning("PINATA_JWT not set, returning placeholder URI")
        return f"ipfs://placeholder-{name}"

    async with httpx.AsyncClient(timeout=120) as client:
        with open(image_path, "rb") as f:
            files = {"file": (f"{name}.png", f, "image/png")}
            headers = {"Authorization": f"Bearer {settings.pinata_jwt}"}
            metadata = json.dumps({"name": name, "keyvalues": {"project": "growring"}})

            response = await client.post(
                f"{PINATA_API}/pinning/pinFileToIPFS",
                files=files,
                data={"pinataMetadata": metadata},
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

    ipfs_hash = result["IpfsHash"]
    uri = f"ipfs://{ipfs_hash}"
    logger.info(f"📌 Pinned {name} → {uri}")
    return uri


async def pin_metadata(metadata: dict, name: str) -> str:
    """Pin JSON metadata to IPFS via Pinata.

    Args:
        metadata: The metadata dictionary (follows OpenSea/ERC-721 standard)
        name: Descriptive name for the pin

    Returns:
        IPFS URI string (ipfs://Qm...)
    """
    settings = get_settings()
    if not settings.pinata_jwt:
        logger.warning("PINATA_JWT not set, returning placeholder URI")
        return f"ipfs://placeholder-meta-{name}"

    async with httpx.AsyncClient(timeout=60) as client:
        headers = {
            "Authorization": f"Bearer {settings.pinata_jwt}",
            "Content-Type": "application/json",
        }
        payload = {
            "pinataContent": metadata,
            "pinataMetadata": {"name": name, "keyvalues": {"project": "growring"}},
        }

        response = await client.post(
            f"{PINATA_API}/pinning/pinJSONToIPFS",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

    ipfs_hash = result["IpfsHash"]
    uri = f"ipfs://{ipfs_hash}"
    logger.info(f"📌 Pinned metadata {name} → {uri}")
    return uri


def ipfs_to_gateway(ipfs_uri: str, gateway: str = "https://gateway.pinata.cloud/ipfs/") -> str:
    """Convert an IPFS URI to an HTTP gateway URL for display."""
    if ipfs_uri.startswith("ipfs://"):
        return gateway + ipfs_uri[7:]
    return ipfs_uri
