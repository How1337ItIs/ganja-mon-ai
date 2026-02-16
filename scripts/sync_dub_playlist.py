#!/usr/bin/env python3
"""
Sync Dub Playlist to Website
============================

Copies or creates symlinks for dub tracks to web/music directory.
Handles large files efficiently by using symlinks when possible.
"""

import shutil
import sys
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DUB_PLAYLIST_DIR = PROJECT_ROOT / "research" / "dub_playlist" / "dub_mixes"
WEB_MUSIC_DIR = PROJECT_ROOT / "src" / "web" / "music"
DUB_SUBDIR = WEB_MUSIC_DIR / "ultimate_dub"

# Create subdirectory for dub tracks
DUB_SUBDIR.mkdir(parents=True, exist_ok=True)


def sync_tracks(use_symlinks: bool = True):
    """Sync dub tracks to web/music directory."""
    
    if not DUB_PLAYLIST_DIR.exists():
        logger.error(f"Dub playlist directory not found: {DUB_PLAYLIST_DIR}")
        return False
    
    mp3_files = list(DUB_PLAYLIST_DIR.glob("*.mp3"))
    
    if not mp3_files:
        logger.warning("No MP3 files found in dub playlist directory")
        return False
    
    logger.info(f"Found {len(mp3_files)} MP3 files to sync")
    
    synced = 0
    skipped = 0
    errors = 0
    
    for mp3_file in mp3_files:
        dest_path = DUB_SUBDIR / mp3_file.name
        
        # Skip if already exists and is same size
        if dest_path.exists():
            if dest_path.stat().st_size == mp3_file.stat().st_size:
                skipped += 1
                continue
            else:
                # Remove old file if size differs
                dest_path.unlink()
        
        try:
            if use_symlinks:
                # Try to create symlink (more efficient)
                try:
                    if sys.platform == "win32":
                        # Windows requires admin or developer mode for symlinks
                        # Fall back to copy
                        shutil.copy2(mp3_file, dest_path)
                        logger.info(f"Copied: {mp3_file.name}")
                    else:
                        # Unix/Linux - create symlink
                        dest_path.symlink_to(mp3_file)
                        logger.info(f"Linked: {mp3_file.name}")
                except (OSError, NotImplementedError):
                    # Fallback to copy if symlink fails
                    shutil.copy2(mp3_file, dest_path)
                    logger.info(f"Copied (symlink failed): {mp3_file.name}")
            else:
                # Copy file
                shutil.copy2(mp3_file, dest_path)
                logger.info(f"Copied: {mp3_file.name}")
            
            synced += 1
            
        except Exception as e:
            logger.error(f"Error syncing {mp3_file.name}: {e}")
            errors += 1
    
    logger.info(f"\nSync complete: {synced} synced, {skipped} skipped, {errors} errors")
    return errors == 0


def generate_playlist_json():
    """Generate playlist.json for ultimate dub playlist."""
    tracks = []
    
    mp3_files = sorted(DUB_SUBDIR.glob("*.mp3"))
    
    for i, file_path in enumerate(mp3_files, 1):
        filename = file_path.stem
        
        # Parse artist - title from filename
        if " - " in filename:
            parts = filename.split(" - ", 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = "Various Artists"
            title = filename
        
        tracks.append({
            "file": f"ultimate_dub/{file_path.name}",
            "title": title,
            "artist": artist,
            "album": "Ultimate Chill Dub Reggae",
            "genre": "Dub Reggae",
            "vibe": "heady",
            "quality": "VBR",
            "source": "YouTube/Streaming"
        })
    
    playlist = {
        "name": "Ultimate Chill Dub Reggae",
        "description": "8+ hours of the headiest, chillest dub bangers - from King Tubby to modern interpretations",
        "theme": "dub",
        "tracks": tracks,
        "total_tracks": len(tracks),
        "license": "Personal use - Educational purposes",
        "created": "2026-01-21"
    }
    
    playlist_path = WEB_MUSIC_DIR / "ultimate_dub_playlist.json"
    with open(playlist_path, 'w', encoding='utf-8') as f:
        json.dump(playlist, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated playlist.json: {len(tracks)} tracks")
    return playlist


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync dub playlist to website")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of symlinks")
    parser.add_argument("--playlist-only", action="store_true", help="Only generate playlist.json")
    
    args = parser.parse_args()
    
    if args.playlist_only:
        generate_playlist_json()
        return
    
    # Sync tracks
    success = sync_tracks(use_symlinks=not args.copy)
    
    if success:
        # Generate playlist.json
        generate_playlist_json()
        logger.info("\n✅ Dub playlist synced successfully!")
        logger.info(f"Tracks available at: /music/ultimate_dub/")
        logger.info(f"Playlist API: /api/playlist/ultimate_dub")
    else:
        logger.error("\n❌ Some errors occurred during sync")
        sys.exit(1)


if __name__ == "__main__":
    main()
