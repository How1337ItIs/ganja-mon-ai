#!/usr/bin/env python3
"""
Automated Database Backup
==========================
Backs up SQLite database with rotation and compression.

Usage:
    python scripts/backup_database.py

Cron (daily at 3 AM):
    0 3 * * * cd /home/natha/projects/sol-cannabis && python3 scripts/backup_database.py
"""

import os
import shutil
import gzip
from datetime import datetime
from pathlib import Path

# Configuration
DB_PATH = Path(__file__).parent.parent / "grokmon.db"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
KEEP_DAYS = 30  # Keep last 30 days of backups

def backup_database():
    """Create compressed database backup"""
    if not DB_PATH.exists():
        print(f"[!] Database not found: {DB_PATH}")
        return False

    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)

    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"grokmon_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_name
    compressed_path = BACKUP_DIR / f"{backup_name}.gz"

    try:
        # Copy database
        print(f"[*] Backing up database to {backup_path}")
        shutil.copy2(DB_PATH, backup_path)

        # Compress backup
        print(f"[*] Compressing backup...")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove uncompressed backup
        backup_path.unlink()

        # Get sizes
        original_size = DB_PATH.stat().st_size / 1024 / 1024  # MB
        compressed_size = compressed_path.stat().st_size / 1024 / 1024  # MB
        ratio = (1 - compressed_size / original_size) * 100

        print(f"[✓] Backup created: {compressed_path.name}")
        print(f"    Original: {original_size:.2f}MB → Compressed: {compressed_size:.2f}MB ({ratio:.1f}% saved)")

        # Cleanup old backups
        cleanup_old_backups()

        return True

    except Exception as e:
        print(f"[!] Backup failed: {e}")
        if backup_path.exists():
            backup_path.unlink()
        return False


def cleanup_old_backups():
    """Remove backups older than KEEP_DAYS"""
    if not BACKUP_DIR.exists():
        return

    cutoff = datetime.now().timestamp() - (KEEP_DAYS * 86400)
    removed = 0

    for backup_file in BACKUP_DIR.glob("grokmon_backup_*.db.gz"):
        if backup_file.stat().st_mtime < cutoff:
            backup_file.unlink()
            removed += 1
            print(f"    Removed old backup: {backup_file.name}")

    if removed > 0:
        print(f"[*] Cleaned up {removed} old backups (keeping last {KEEP_DAYS} days)")


def list_backups():
    """List all available backups"""
    if not BACKUP_DIR.exists():
        print("[!] No backups directory found")
        return

    backups = sorted(BACKUP_DIR.glob("grokmon_backup_*.db.gz"), reverse=True)

    if not backups:
        print("[!] No backups found")
        return

    print(f"\n[*] Available backups ({len(backups)}):")
    for backup in backups:
        size = backup.stat().st_size / 1024 / 1024  # MB
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"    {backup.name} - {size:.2f}MB - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_backups()
    else:
        success = backup_database()
        sys.exit(0 if success else 1)
