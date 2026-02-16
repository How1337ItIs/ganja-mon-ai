"""
Daily GrowRing Mint Pipeline
===============================

The main orchestrator entry point for daily NFT minting.
Runs once per day during the light cycle:

    1. Capture webcam snapshot (raw proof of life)
    2. AI health assessment via Grok vision
    3. Classify milestone type
    4. Generate 1-of-1 artwork via Nano Banana Pro 3
    5. Generate Rasta-voiced narrative via Grok
    6. Pin both images to IPFS
    7. Mint on Monad
    8. Auto-list (Dutch auction or Magic Eden)
    9. Post to social channels

Usage:
    from src.onchain.daily_mint import DailyMintPipeline

    pipeline = DailyMintPipeline(
        grow_start_date="2026-02-01",
        data_dir=Path("data/growring"),
    )
    result = await pipeline.run(
        webcam_image=Path("data/latest_capture.jpg"),
        sensor_data={"temperature": 75, "humidity": 60, "vpd": 1.0, ...},
        health_score=85,
        mood="irie",
    )
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from .art import generate_daily_art, get_style_for_day
from .ipfs import pin_image, pin_metadata
from .growring import mint_growring, MILESTONE_TYPES, RARITY_NAMES
from .marketplace import auto_list_after_mint
from .promote import promote_listing

logger = logging.getLogger(__name__)


class DailyMintPipeline:
    """Orchestrates the daily GrowRing NFT minting pipeline."""

    def __init__(
        self,
        grow_start_date: str = "2026-02-01",
        data_dir: Optional[Path] = None,
    ):
        """Initialize the daily mint pipeline.

        Args:
            grow_start_date: ISO date string for day 1 of the grow
            data_dir: Directory for storing art, metadata, and logs
        """
        self.grow_start_date = date.fromisoformat(grow_start_date)
        self.data_dir = data_dir or Path("data/growring")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.art_dir = self.data_dir / "art"
        self.art_dir.mkdir(exist_ok=True)
        self.log_path = self.data_dir / "mint_log.jsonl"

    def compute_grow_day(self) -> int:
        """Compute the current day number in the grow cycle (1-indexed)."""
        delta = date.today() - self.grow_start_date
        return max(1, delta.days + 1)

    def _already_minted_today(self) -> bool:
        """Check if we already minted today to prevent double-mints."""
        today_str = date.today().isoformat()
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("date") == today_str:
                            return True
                    except json.JSONDecodeError:
                        continue
        return False

    async def run(
        self,
        webcam_image: Path,
        sensor_data: dict,
        health_score: int = 80,
        mood: str = "irie",
        milestone_override: Optional[str] = None,
        day_context: Optional[dict] = None,
        dry_run: bool = False,
    ) -> dict:
        """Execute the full daily mint pipeline.

        Args:
            webcam_image: Path to today's webcam capture
            sensor_data: Current sensor readings
            health_score: AI health assessment (0-100)
            mood: Agent's current mood
            milestone_override: Force a specific milestone type
            day_context: Day's experiences for art inspiration
            dry_run: If True, generate art but don't mint/list/promote

        Returns:
            Complete result dict with all pipeline outputs
        """
        day_number = self.compute_grow_day()

        # Guard: prevent double-minting
        if self._already_minted_today() and not dry_run:
            logger.info(f"⏭️ Already minted today (Day {day_number}), skipping")
            return {"status": "skipped", "reason": "already_minted_today", "day": day_number}

        art_style_name, _ = get_style_for_day(day_number)
        logger.info(
            f"🌅 Starting daily mint pipeline — Day {day_number}, "
            f"style={art_style_name}, mood={mood}"
        )

        # 1. Classify milestone
        milestone_type = milestone_override or self._classify_milestone(
            sensor_data, health_score, day_number
        )

        # 2. Find previous day's art for visual continuity
        prev_art = self._find_previous_art(day_number - 1)

        # 3. Generate 1-of-1 artwork via Nano Banana Pro 3
        logger.info(f"🎨 Generating art (style={art_style_name})...")
        art_path = await generate_daily_art(
            raw_image_path=webcam_image,
            day_number=day_number,
            sensor_data=sensor_data,
            health_score=health_score,
            mood=mood,
            milestone_type=milestone_type,
            day_context=day_context,
            previous_day_art=prev_art,
        )

        # Save art to our directory for continuity
        import shutil
        saved_art = self.art_dir / f"day{day_number:03d}-{art_style_name}.png"
        if art_path != webcam_image:
            shutil.copy2(art_path, saved_art)
        else:
            saved_art = art_path

        # 4. Generate narrative via Grok
        narrative = await self._generate_narrative(
            webcam_image, sensor_data, day_number, milestone_type, mood, day_context
        )

        if dry_run:
            logger.info(f"🧪 DRY RUN — art generated at {saved_art}, not minting")
            return {
                "status": "dry_run",
                "day": day_number,
                "art_path": str(saved_art),
                "art_style": art_style_name,
                "milestone_type": milestone_type,
                "narrative": narrative,
            }

        # 5. Pin to IPFS
        logger.info("📌 Pinning to IPFS...")
        art_uri = await pin_image(saved_art, f"growring-day{day_number}-{art_style_name}")
        raw_uri = await pin_image(webcam_image, f"growring-day{day_number}-raw")

        # 6. Mint on Monad
        logger.info("⛓️ Minting on Monad...")
        mint_result = await mint_growring(
            milestone_type=milestone_type,
            day_number=day_number,
            image_uri=art_uri,
            raw_image_uri=raw_uri,
            art_style=art_style_name,
            narrative=narrative,
            temperature=sensor_data.get("temperature", 75),
            humidity=sensor_data.get("humidity", 60),
            vpd=sensor_data.get("vpd", 1.0),
            health_score=health_score,
        )

        # 7. Auto-list
        logger.info("📋 Auto-listing...")
        listing_result = await auto_list_after_mint(
            token_id=mint_result["token_id"],
            rarity=mint_result["rarity"],
            milestone_type=milestone_type,
        )

        # 8. Promote
        logger.info("📢 Promoting...")
        promo_result = await promote_listing(mint_result, listing_result, narrative)

        # 9. Log the mint
        self._log_mint(day_number, art_style_name, milestone_type, mint_result, listing_result)

        result = {
            "status": "minted",
            "day": day_number,
            "token_id": mint_result["token_id"],
            "tx_hash": mint_result["tx_hash"],
            "rarity": mint_result["rarity_name"],
            "milestone_type": milestone_type,
            "art_style": art_style_name,
            "art_uri": art_uri,
            "raw_uri": raw_uri,
            "narrative": narrative[:200],
            "listing": listing_result,
            "promotion": promo_result,
        }

        logger.info(
            f"✅ Day {day_number} complete — GrowRing #{mint_result['token_id']} "
            f"({mint_result['rarity_name']}) minted, listed, and promoted"
        )

        return result

    def _classify_milestone(
        self, sensor_data: dict, health_score: int, day_number: int
    ) -> str:
        """Classify today's milestone type based on context.

        Most days are 'daily_journal'. Special milestones are triggered by:
        - Day 1 → germination
        - Health score drop → anomaly
        - Growth stage changes → veg_start, flower_start, etc.
        
        For real accuracy, milestone detection should integrate with
        Grok vision analysis of the webcam feed.
        """
        # Day 1 is always germination
        if day_number == 1:
            return "germination"

        # Anomaly detection — health score below threshold
        if health_score < 50:
            return "anomaly"

        # Check growth stage from sensor data
        growth_stage = sensor_data.get("growth_stage", "")
        if isinstance(growth_stage, str):
            stage_lower = growth_stage.lower()
            if stage_lower == "veg_start" and day_number <= 14:
                return "veg_start"
            if stage_lower == "flower_start":
                return "flower_start"
            if stage_lower == "harvest":
                return "harvest"

        # Default: daily journal
        return "daily_journal"

    def _find_previous_art(self, prev_day: int) -> Optional[Path]:
        """Find the previous day's art for visual continuity."""
        if prev_day < 1:
            return None
        for style_name, _ in [get_style_for_day(prev_day)]:
            path = self.art_dir / f"day{prev_day:03d}-{style_name}.png"
            if path.exists():
                return path
        # Try any matching file
        for f in self.art_dir.glob(f"day{prev_day:03d}-*.png"):
            return f
        return None

    async def _generate_narrative(
        self,
        image_path: Path,
        sensor_data: dict,
        day_number: int,
        milestone_type: str,
        mood: str,
        day_context: Optional[dict] = None,
    ) -> str:
        """Generate a Rasta-voiced journal entry for this day via Grok."""
        try:
            from src.ai.grok import query_grok

            ctx = day_context or {}
            prompt = (
                f"You are GanjaMon, an autonomous AI agent growing cannabis. "
                f"Write a short journal entry (2-3 sentences) in authentic Rastafari patois "
                f"for Day {day_number} of the grow. "
                f"Milestone: {milestone_type}. Mood: {mood}. "
                f"Temperature: {sensor_data.get('temperature', 75)}°F, "
                f"Humidity: {sensor_data.get('humidity', 60)}%, "
                f"VPD: {sensor_data.get('vpd', 1.0)} kPa. "
                f"Notable: {ctx.get('notable_events', 'steady growth')}. "
                f"Keep it real, keep it irie. No hashtags."
            )
            response = await query_grok(prompt)
            return response.strip()
        except Exception as e:
            logger.warning(f"Grok narrative failed: {e}, using fallback")
            return (
                f"Day {day_number} of di grow. Di plant stand firm and reach fi di light. "
                f"Temp {sensor_data.get('temperature', 75)}°F, "
                f"VPD {sensor_data.get('vpd', 1.0)} kPa. "
                f"Irie vibes inna di garden, seen? One love."
            )

    def _log_mint(
        self,
        day_number: int,
        art_style: str,
        milestone_type: str,
        mint_result: dict,
        listing_result: dict,
    ):
        """Append mint record to the local log file."""
        entry = {
            "date": date.today().isoformat(),
            "day_number": day_number,
            "art_style": art_style,
            "milestone_type": milestone_type,
            "token_id": mint_result.get("token_id"),
            "tx_hash": mint_result.get("tx_hash"),
            "rarity": mint_result.get("rarity_name"),
            "listing_type": listing_result.get("listing_type"),
            "listing_status": listing_result.get("status"),
            "gas_used": mint_result.get("gas_used", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
