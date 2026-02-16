"""
ERC-8004 Agent Registry Metadata Parser

Decodes and parses agent metadata from various URI formats:
- Base64-encoded data URIs (with optional gzip compression)
- IPFS URIs
- HTTP/HTTPS URLs
- Inline JSON
- Empty/unknown formats

Handles real-world variations in field naming and structure from 8004scan.io registry data.
"""

import base64
import gzip
import json
from typing import Any
from web3 import Web3


def decode_agent_uri(uri: str) -> tuple[bool, list[str], dict | None]:
    """
    Decode agentURI from any format.

    Returns:
        (success: bool, warnings: list[str], metadata: dict | None)
    """
    warnings = []

    if not uri or uri.strip() == "":
        return False, ["Empty URI"], None

    uri = uri.strip()

    # Inline JSON (starts with { or [)
    if uri.startswith("{") or uri.startswith("["):
        try:
            metadata = json.loads(uri)
            return True, [], metadata
        except json.JSONDecodeError as e:
            return False, [f"Invalid inline JSON: {e}"], None

    # data: URI
    if uri.startswith("data:"):
        try:
            # Parse data URI format: data:[<mediatype>][;base64],<data>
            if ";base64," not in uri:
                return False, ["data: URI missing base64 encoding"], None

            header, encoded_data = uri.split(";base64,", 1)

            # Decode base64
            try:
                decoded_bytes = base64.b64decode(encoded_data)
            except Exception as e:
                return False, [f"Base64 decode failed: {e}"], None

            # Check for gzip compression (enc=gzip in header)
            if "enc=gzip" in header:
                try:
                    decoded_bytes = gzip.decompress(decoded_bytes)
                    warnings.append("Decompressed gzip content")
                except Exception as e:
                    return False, [f"Gzip decompression failed: {e}"], None

            # Parse JSON
            try:
                metadata = json.loads(decoded_bytes.decode('utf-8'))
                return True, warnings, metadata
            except json.JSONDecodeError as e:
                return False, warnings + [f"JSON parse failed: {e}"], None

        except Exception as e:
            return False, [f"data: URI parse error: {e}"], None

    # IPFS URI
    if uri.startswith("ipfs://"):
        return False, ["IPFS URI requires gateway fetch"], None

    # HTTP/HTTPS URI
    if uri.startswith("http://") or uri.startswith("https://"):
        return False, ["HTTP URI requires fetch"], None

    # Unknown format
    return False, [f"Unknown URI format: {uri[:50]}..."], None


def extract_agent_metadata(reg_file: dict) -> dict:
    """
    Extract structured metadata from agent registration file.

    Handles real-world variations:
    - type/name OR protocol for service protocol
    - url/endpoint for service URL
    - x402Support/x402support (case-insensitive)

    Returns standardized metadata dict.
    """
    metadata = {
        "name": reg_file.get("name", "Unknown Agent"),
        "description": reg_file.get("description", ""),
        "x402Support": False,
        "services": [],
        "mcpEndpoint": None,
        "a2aEndpoint": None,
        "image": reg_file.get("image"),
        "active": reg_file.get("active", True),
        "supportedTrust": reg_file.get("supportedTrust", [])
    }

    # Extract x402 support (case-insensitive)
    for key in ["x402Support", "x402support", "X402Support"]:
        if key in reg_file:
            metadata["x402Support"] = bool(reg_file[key])
            break

    # Extract services with fallback field handling
    services_raw = reg_file.get("services", [])
    for svc in services_raw:
        if not isinstance(svc, dict):
            continue

        # Extract protocol (type/name OR protocol field)
        protocol = svc.get("protocol") or svc.get("type") or svc.get("name")

        # Extract endpoint (url OR endpoint field)
        endpoint = svc.get("endpoint") or svc.get("url")

        if protocol and endpoint:
            service_entry = {
                "protocol": protocol,
                "endpoint": endpoint
            }
            metadata["services"].append(service_entry)

            # Set specific endpoint shortcuts
            if protocol.upper() == "MCP":
                metadata["mcpEndpoint"] = endpoint
            elif protocol.upper() == "A2A":
                metadata["a2aEndpoint"] = endpoint

    # Fallback: check top-level mcpEndpoint/a2aEndpoint
    if not metadata["mcpEndpoint"] and "mcpEndpoint" in reg_file:
        metadata["mcpEndpoint"] = reg_file["mcpEndpoint"]
    if not metadata["a2aEndpoint"] and "a2aEndpoint" in reg_file:
        metadata["a2aEndpoint"] = reg_file["a2aEndpoint"]

    return metadata


def metadata_to_data_uri(metadata: dict) -> str:
    """
    Encode metadata dict to base64 data URI.

    Returns: data:application/json;base64,<encoded>
    """
    json_bytes = json.dumps(metadata, separators=(',', ':')).encode('utf-8')
    encoded = base64.b64encode(json_bytes).decode('utf-8')
    return f"data:application/json;base64,{encoded}"


def decode_erc8004_event(log: dict) -> tuple[bool, list[str], dict | None]:
    """
    Parse ERC-8004 Transfer or URIUpdated event log.

    Args:
        log: Event log dict with topics and data

    Returns:
        (success: bool, warnings: list[str], parsed_data: dict | None)

        parsed_data contains:
        - agentId: int
        - ownerAddress: str (checksummed)
        - agentURI: str (if URIUpdated or Transfer with URI in data)
    """
    TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    URI_UPDATED_TOPIC = "0x6bb7ff708619ba0610cba295a58592e0451dee2622938c8755667688daf3529b"

    warnings = []

    try:
        topics = log.get("topics", [])
        data = log.get("data", "0x")

        if not topics:
            return False, ["No topics in log"], None

        event_sig = topics[0] if isinstance(topics[0], str) else Web3.to_hex(topics[0])

        # Transfer event: topics[0]=sig, topics[1]=from, topics[2]=to, topics[3]=tokenId
        # URIUpdated: topics[0]=sig, topics[1]=tokenId, data=uri

        result = {}

        if event_sig.lower() == TRANSFER_TOPIC.lower():
            # Extract agentId (tokenId) from topics[3]
            if len(topics) < 4:
                return False, ["Transfer event missing tokenId"], None

            token_id_hex = topics[3] if isinstance(topics[3], str) else Web3.to_hex(topics[3])
            result["agentId"] = int(token_id_hex, 16)

            # Extract owner (to address) from topics[2]
            owner_hex = topics[2] if isinstance(topics[2], str) else Web3.to_hex(topics[2])
            # Remove padding and checksum
            owner_addr = "0x" + owner_hex[-40:]
            result["ownerAddress"] = Web3.to_checksum_address(owner_addr)

            # Try to decode URI from data field (some implementations include it)
            if data and data != "0x":
                try:
                    decoded_data = Web3.to_bytes(hexstr=data)
                    # ABI decode string (offset + length + data)
                    if len(decoded_data) >= 64:
                        str_offset = int.from_bytes(decoded_data[0:32], 'big')
                        str_length = int.from_bytes(decoded_data[32:64], 'big')
                        if str_length > 0 and len(decoded_data) >= 64 + str_length:
                            uri_bytes = decoded_data[64:64+str_length]
                            result["agentURI"] = uri_bytes.decode('utf-8', errors='ignore')
                except Exception as e:
                    warnings.append(f"Could not decode URI from data: {e}")

            return True, warnings, result

        elif event_sig.lower() == URI_UPDATED_TOPIC.lower():
            # Extract agentId from topics[1]
            if len(topics) < 2:
                return False, ["URIUpdated event missing tokenId"], None

            token_id_hex = topics[1] if isinstance(topics[1], str) else Web3.to_hex(topics[1])
            result["agentId"] = int(token_id_hex, 16)

            # Decode URI from data
            if data and data != "0x":
                try:
                    decoded_data = Web3.to_bytes(hexstr=data)
                    # ABI decode string
                    if len(decoded_data) >= 64:
                        str_offset = int.from_bytes(decoded_data[0:32], 'big')
                        str_length = int.from_bytes(decoded_data[32:64], 'big')
                        if str_length > 0 and len(decoded_data) >= 64 + str_length:
                            uri_bytes = decoded_data[64:64+str_length]
                            result["agentURI"] = uri_bytes.decode('utf-8', errors='ignore')
                except Exception as e:
                    return False, [f"Failed to decode URI: {e}"], None

            return True, warnings, result

        else:
            return False, [f"Unknown event signature: {event_sig}"], None

    except Exception as e:
        return False, [f"Event parsing error: {e}"], None


def categorize_agent(metadata: dict) -> dict:
    """
    Return boolean categories for agent metadata.

    Args:
        metadata: Extracted metadata dict from extract_agent_metadata()

    Returns:
        Dict with boolean flags:
        - isEmpty: No useful data
        - isBase64: Was base64 encoded
        - isHttp: Uses HTTP endpoint
        - isIpfs: Uses IPFS URI
        - isParseable: Successfully parsed
        - isSpecCompliant: Has required fields
        - isX402: Supports x402 payments
        - isMcp: Has MCP endpoint
        - isA2A: Has A2A endpoint
        - isActive: Agent marked active
    """
    categories = {
        "isEmpty": False,
        "isBase64": False,  # Would need to track from decode_agent_uri
        "isHttp": False,
        "isIpfs": False,
        "isParseable": True,  # If we got metadata, it parsed
        "isSpecCompliant": False,
        "isX402": metadata.get("x402Support", False),
        "isMcp": metadata.get("mcpEndpoint") is not None,
        "isA2A": metadata.get("a2aEndpoint") is not None,
        "isActive": metadata.get("active", True)
    }

    # Check for emptiness
    if not metadata.get("name") or metadata["name"] == "Unknown Agent":
        if not metadata.get("services") and not metadata.get("description"):
            categories["isEmpty"] = True

    # Check endpoints for HTTP/IPFS
    for svc in metadata.get("services", []):
        endpoint = svc.get("endpoint", "")
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            categories["isHttp"] = True
        if endpoint.startswith("ipfs://"):
            categories["isIpfs"] = True

    # Spec compliance: name + description + at least one service
    if metadata.get("name") and metadata.get("description") and metadata.get("services"):
        categories["isSpecCompliant"] = True

    return categories
