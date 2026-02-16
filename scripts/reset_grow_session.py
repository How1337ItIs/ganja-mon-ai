#!/usr/bin/env python3
"""
Reset Grow Session
==================

Creates a fresh grow session for Purple Milk clone.
Run this on the Chromebook to reset the database.

Usage:
    python scripts/reset_grow_session.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db.connection import init_database, close_database, get_db_session
from db.models import GrowSession, GrowthStage, Photoperiod


async def reset_grow_session():
    """Create a fresh grow session for Purple Milk clone"""
    print("Initializing database...")
    await init_database()

    async with get_db_session() as session:
        # Deactivate ALL existing sessions
        from sqlalchemy import update
        await session.execute(
            update(GrowSession)
            .where(GrowSession.is_active == True)
            .values(is_active=False, end_date=datetime.utcnow())
        )
        await session.commit()
        print("Deactivated all old sessions")

        # Create new session for Purple Milk
        new_session = GrowSession(
            plant_name="Mon",
            strain_name="Purple Milk",
            strain_type="Hybrid (60/40 sativa-dominant)",
            is_active=True,
            start_date=datetime.utcnow(),
            current_day=1,
            current_stage=GrowthStage.VEGETATIVE,
            photoperiod=Photoperiod.VEG_24_0,  # 24/0 for clone establishment
            notes="Compound Genetics (Horchata x Grape Gasoline). Freshly transplanted clone. 24/0 light for establishment."
        )
        session.add(new_session)
        await session.commit()

        print(f"""
=== NEW GROW SESSION CREATED ===
Plant Name:  Mon
Strain:      Purple Milk (Compound Genetics)
Type:        Hybrid (60/40 sativa-dominant)
Day:         1
Stage:       VEGETATIVE
Photoperiod: 24/0 (continuous light)
Started:     {new_session.start_date.isoformat()}
Session ID:  {new_session.id}
================================
""")

    await close_database()
    print("Database connection closed. Restart the API server to apply changes.")


if __name__ == "__main__":
    asyncio.run(reset_grow_session())
