#!/usr/bin/env python3
"""
Database Initialization Script
==============================

Creates all tables and optionally seeds with test data.

Usage:
    python -m src.db.init_db              # Create tables only
    python -m src.db.init_db --seed       # Create tables + seed data
    python -m src.db.init_db --reset      # Drop all tables and recreate
"""

import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from .connection import DatabaseManager, init_database
from .models import (
    Base, GrowSession, SensorReading, DeviceState, AIDecision,
    GrowthStage, Photoperiod, ActionType
)
from .repository import GrowRepository


async def create_tables(db: DatabaseManager) -> None:
    """Create all database tables"""
    print("Creating database tables...")
    await db.initialize()
    print("Tables created successfully!")


async def drop_tables(db: DatabaseManager) -> None:
    """Drop all database tables"""
    print("Dropping all tables...")
    async with db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Tables dropped!")


async def seed_fresh_session(db: DatabaseManager) -> None:
    """
    Create a fresh grow session for Purple Milk clone.
    Does NOT seed any fake sensor data - only creates the session.
    """
    print("Creating fresh grow session...")

    async with db.session() as session:
        repo = GrowRepository(session)

        # Create a fresh grow session for Purple Milk
        grow_session = await repo.create_session(
            plant_name="Mon",
            strain_name="Purple Milk",
            strain_type="Hybrid (60/40 sativa-dominant)",
        )

        # Start at Day 1 in vegetative
        grow_session.current_day = 1
        grow_session.current_stage = GrowthStage.VEGETATIVE
        grow_session.photoperiod = Photoperiod.VEG_24_0  # 24/0 for clone establishment
        grow_session.notes = "Compound Genetics (Horchata x Grape Gasoline). Freshly transplanted clone."

        await session.commit()

    print("Fresh grow session created!")
    print("  Plant: Mon (Purple Milk)")
    print("  Stage: VEGETATIVE, Day 1")
    print("  Photoperiod: 24/0")
    print("  NOTE: No fake sensor data seeded - only real readings will be stored.")


async def main():
    parser = argparse.ArgumentParser(description="Initialize Grok & Mon database")
    parser.add_argument("--seed", action="store_true", help="Seed with test data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables")
    parser.add_argument("--db-path", type=str, help="Custom database path")

    args = parser.parse_args()

    # Setup database
    db_url = None
    if args.db_path:
        Path(args.db_path).parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite+aiosqlite:///{args.db_path}"

    db = DatabaseManager(db_url)

    try:
        if args.reset:
            await drop_tables(db)

        await create_tables(db)

        if args.seed:
            await seed_fresh_session(db)

        print("\nDatabase ready!")
        print(f"Location: {db.database_url}")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
