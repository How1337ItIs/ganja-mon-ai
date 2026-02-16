#!/usr/bin/env python3
"""
Create DexScreener Banner
=========================
Generate animated GIF banners for DexScreener and social media.

Usage:
    python scripts/create_banner.py                    # Default glow style
    python scripts/create_banner.py --style matrix     # Matrix rain style
    python scripts/create_banner.py --style wave       # Wave pattern
    python scripts/create_banner.py --day 49 --stage FLOWERING

Output: data/banners/grokmon_banner.gif (1500x500 px)
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from media.banner import create_animated_dexscreener_banner


def main():
    parser = argparse.ArgumentParser(
        description="Create animated DexScreener banner for Grok & Mon"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/banners/grokmon_banner.gif",
        help="Output GIF path (default: data/banners/grokmon_banner.gif)"
    )
    parser.add_argument(
        "--day", "-d",
        type=int,
        default=1,
        help="Grow day to display (default: 1)"
    )
    parser.add_argument(
        "--stage", "-s",
        default="VEGETATIVE",
        choices=["SEEDLING", "VEGETATIVE", "TRANSITION", "FLOWERING", "LATE_FLOWER", "HARVEST"],
        help="Growth stage (default: VEGETATIVE)"
    )
    parser.add_argument(
        "--style",
        default="glow",
        choices=["glow", "wave", "matrix"],
        help="Animation style (default: glow)"
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=60,
        help="Number of frames (more = smoother, larger file) (default: 60)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=15,
        help="Frames per second (default: 15)"
    )

    args = parser.parse_args()

    print(f"Creating {args.style} style banner...")
    print(f"  Day: {args.day}")
    print(f"  Stage: {args.stage}")
    print(f"  Frames: {args.frames} @ {args.fps}fps")

    output_path = create_animated_dexscreener_banner(
        output_path=args.output,
        grow_day=args.day,
        stage=args.stage,
        style=args.style,
    )

    print(f"\nBanner created: {output_path}")
    print(f"Size: 1500x500 px (DexScreener optimized)")
    print("\nUpload to DexScreener or use as Twitter header!")


if __name__ == "__main__":
    main()
