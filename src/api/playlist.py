"""
Playlist API Endpoints
======================

Serves playlist metadata and handles large file streaming for the ultimate dub playlist.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote, unquote
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/playlist", tags=["playlist"])

# Paths
WEB_DIR = Path(__file__).parent.parent / "web"
MUSIC_DIR = WEB_DIR / "music"
DUB_PLAYLIST_DIR = Path(__file__).parent.parent.parent / "research" / "dub_playlist" / "dub_mixes"

# Cloudflare R2 configuration (optional)
# Set USE_R2_DUB=true to use R2 instead of local files
USE_R2 = os.environ.get("USE_R2_DUB", "true").lower() == "true"  # Default to R2
R2_BUCKET_NAME = os.environ.get("R2_DUB_BUCKET", "grokmon-dub-tracks")
# R2 tracks served via Cloudflare Worker at /api/playlist/dub/stream/*
R2_STREAM_URL = "/api/playlist/dub/stream"  # Worker route


def get_playlist_json(playlist_name: str = "trenchtown") -> Dict:
    """Load playlist JSON file."""
    playlist_path = MUSIC_DIR / f"{playlist_name}_playlist.json"
    
    if not playlist_path.exists():
        # Fallback to default playlist.json
        playlist_path = MUSIC_DIR / "playlist.json"
    
    if not playlist_path.exists():
        raise HTTPException(status_code=404, detail=f"Playlist '{playlist_name}' not found")
    
    with open(playlist_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_dub_tracks() -> List[Dict]:
    """
    Get dub track metadata.
    First tries to load from pre-generated JSON file (for R2 deployment).
    Falls back to scanning local directory if JSON doesn't exist.
    """
    # Try loading from pre-generated JSON first (for R2 deployment)
    dub_json_path = MUSIC_DIR / "ultimate_dub_playlist.json"
    if dub_json_path.exists():
        try:
            with open(dub_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tracks = data.get("tracks", [])
                # Ensure URLs use R2 stream path
                for track in tracks:
                    track["url"] = f"{R2_STREAM_URL}/{track['file']}"
                logger.info(f"Loaded {len(tracks)} tracks from ultimate_dub_playlist.json")
                return tracks
        except Exception as e:
            logger.warning(f"Failed to load dub playlist JSON: {e}")

    # Fall back to scanning local directory
    tracks = []

    if not DUB_PLAYLIST_DIR.exists():
        return tracks

    # Get all MP3 files
    mp3_files = sorted(DUB_PLAYLIST_DIR.glob("*.mp3"))

    for i, file_path in enumerate(mp3_files, 1):
        # Extract metadata from filename
        filename = file_path.stem

        # Try to parse artist - title format
        if " - " in filename:
            parts = filename.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = "Various Artists"
            title = filename

        # Get file size
        file_size = file_path.stat().st_size

        tracks.append({
            "id": i,
            "file": file_path.name,
            "title": title,
            "artist": artist,
            "album": "Ultimate Chill Dub Reggae",
            "genre": "Dub Reggae",
            "vibe": "heady",
            "size_mb": round(file_size / (1024 * 1024), 2),
            "url": f"{R2_STREAM_URL}/{file_path.name}" if USE_R2 else f"/api/playlist/dub/stream/{file_path.name}"
        })

    return tracks


@router.get("/list")
async def list_playlists():
    """List all available playlists."""
    playlists = []
    
    # Default Trenchtown playlist
    if (MUSIC_DIR / "playlist.json").exists():
        with open(MUSIC_DIR / "playlist.json", 'r', encoding='utf-8') as f:
            trenchtown = json.load(f)
            playlists.append({
                "id": "trenchtown",
                "name": trenchtown.get("name", "Trenchtown Trenches Dub"),
                "description": trenchtown.get("description", ""),
                "track_count": len(trenchtown.get("tracks", [])),
                "theme": trenchtown.get("theme", "trenchtown")
            })
    
    # Ultimate Dub playlist
    dub_tracks = scan_dub_tracks()
    if dub_tracks:
        playlists.append({
            "id": "ultimate_dub",
            "name": "Ultimate Chill Dub Reggae",
            "description": "8+ hours of the headiest, chillest dub bangers - from King Tubby to modern interpretations",
            "track_count": len(dub_tracks),
            "theme": "dub",
            "duration_hours": "8+",
            "size_gb": round(sum(t["size_mb"] for t in dub_tracks) / 1024, 2)
        })
    
    return {"playlists": playlists}


@router.get("/{playlist_id}")
async def get_playlist(playlist_id: str):
    """Get playlist metadata and track list."""
    
    if playlist_id == "ultimate_dub":
        # Generate ultimate dub playlist
        tracks = scan_dub_tracks()
        
        return {
            "id": "ultimate_dub",
            "name": "Ultimate Chill Dub Reggae",
            "description": "8+ hours of the headiest, chillest dub bangers ever recorded",
            "theme": "dub",
            "tracks": tracks,
            "total_tracks": len(tracks),
            "total_size_mb": round(sum(t["size_mb"] for t in tracks), 2),
            "license": "Personal use - Educational purposes",
            "created": "2026-01-21"
        }
    
    elif playlist_id == "trenchtown":
        # Return existing Trenchtown playlist
        return get_playlist_json("trenchtown")
    
    else:
        raise HTTPException(status_code=404, detail=f"Playlist '{playlist_id}' not found")


@router.get("/dub/stream/{filename:path}")
async def stream_dub_track(filename: str, request: Request):
    """
    Stream dub track with range request support for efficient playback.
    Handles large files efficiently with HTTP range requests.

    Note: If USE_R2_DUB=true, this endpoint should be routed to Cloudflare Worker
    instead. This is a fallback for local file serving.
    """
    # Decode URL-encoded filename
    decoded_filename = unquote(filename)

    # If using R2, this endpoint shouldn't be hit (Worker handles it)
    # But we'll keep it as fallback
    if USE_R2:
        logger.warning(f"R2 enabled but local endpoint hit for {decoded_filename}. Ensure Worker route is configured.")

    file_path = DUB_PLAYLIST_DIR / decoded_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Track '{filename}' not found")
    
    # Security: ensure file is in the dub_mixes directory
    try:
        file_path.resolve().relative_to(DUB_PLAYLIST_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid file path")
    
    # Support range requests for streaming
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range header
        start, end = range_header.replace("bytes=", "").split("-")
        start = int(start) if start else 0
        end = int(end) if end else file_path.stat().st_size - 1
        
        file_size = file_path.stat().st_size
        
        # Open file and seek to start position
        def generate():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": "audio/mpeg",
            "Cache-Control": "public, max-age=3600"
        }
        
        return StreamingResponse(
            generate(),
            status_code=206,
            headers=headers,
            media_type="audio/mpeg"
        )
    else:
        # Full file response (with caching)
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Accept-Ranges": "bytes"
            }
        )


@router.get("/dub/m3u")
async def get_dub_m3u():
    """Generate M3U playlist file for ultimate dub collection."""
    tracks = scan_dub_tracks()
    
    m3u_content = "#EXTM3U\n"
    m3u_content += "# Ultimate Chill Dub Reggae Playlist\n"
    m3u_content += f"# Total tracks: {len(tracks)}\n\n"
    
    for track in tracks:
        m3u_content += f"#EXTINF:-1,{track['artist']} - {track['title']}\n"
        m3u_content += f"{track['url']}\n\n"
    
    return Response(
        content=m3u_content,
        media_type="audio/x-mpegurl",
        headers={
            "Content-Disposition": "attachment; filename=ultimate_dub_playlist.m3u"
        }
    )
