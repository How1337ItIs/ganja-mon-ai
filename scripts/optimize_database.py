#!/usr/bin/env python3
"""
Database Optimization Script
=============================
Runs database maintenance: VACUUM, ANALYZE, add indexes.

Usage:
    python scripts/optimize_database.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db.connection import get_db_session

async def optimize_database():
    """Run database optimization"""
    print("[*] Starting database optimization...")

    async with get_db_session() as session:
        # Read and execute index creation SQL
        sql_path = Path(__file__).parent.parent / "src" / "db" / "add_indexes.sql"

        with open(sql_path, 'r') as f:
            sql = f.read()

        # Execute each statement
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    await session.execute(statement)
                    print(f"[✓] {statement[:60]}...")
                except Exception as e:
                    print(f"[!] Failed: {e}")

        await session.commit()

        # Run VACUUM to reclaim space
        print("[*] Running VACUUM...")
        await session.execute("VACUUM")

        # Run ANALYZE to update query planner statistics
        print("[*] Running ANALYZE...")
        await session.execute("ANALYZE")

        await session.commit()

    print("[✓] Database optimization complete!")

if __name__ == "__main__":
    asyncio.run(optimize_database())
