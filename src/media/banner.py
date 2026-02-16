"""
DexScreener Banner Generator
=============================
Creates animated banners for DexScreener, Twitter, and social media.
Inspired by SOLTOMATO's grow banner on DexScreener.

DexScreener Banner Specs:
- Recommended size: 1500x500 pixels
- Format: GIF (animated) or PNG/JPG (static)
- Max file size: 5MB for GIF
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging
import math

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


# DexScreener banner dimensions
DEXSCREENER_WIDTH = 1500
DEXSCREENER_HEIGHT = 500

# Twitter header dimensions
TWITTER_WIDTH = 1500
TWITTER_HEIGHT = 500


class BannerGenerator:
    """
    Generate animated banners for DexScreener and social media.

    Banner Styles:
    1. "timelapse" - Animated plant growth timelapse
    2. "stats" - Animated stats/metrics display
    3. "hybrid" - Timelapse with stats overlay
    4. "logo" - Animated logo with effects

    Usage:
        banner = BannerGenerator()

        # From timelapse frames
        banner.create_timelapse_banner(
            frames_dir="data/timelapse",
            output_path="banner.gif"
        )

        # Animated stats banner
        banner.create_stats_banner(
            grow_day=49,
            stage="FLOWERING",
            output_path="stats_banner.gif"
        )
    """

    def __init__(
        self,
        width: int = DEXSCREENER_WIDTH,
        height: int = DEXSCREENER_HEIGHT,
    ):
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow required. Install with: pip install Pillow")

        self.width = width
        self.height = height

        # Brand colors (cannabis/Jamaican theme)
        self.colors = {
            "green": (34, 139, 34),       # Forest green
            "lime": (50, 205, 50),        # Lime green
            "gold": (255, 215, 0),        # Gold/yellow
            "red": (178, 34, 34),         # Dark red
            "black": (10, 10, 10),        # Near black
            "white": (255, 255, 255),
            "purple": (138, 43, 226),     # Purple (cannabis)
            "grok_blue": (29, 161, 242),  # xAI/Grok blue
        }

    def create_timelapse_banner(
        self,
        frames_dir: str | Path,
        output_path: str | Path,
        fps: int = 8,
        max_frames: int = 50,
        skip_frames: int = 0,
        add_branding: bool = True,
        add_stats_overlay: bool = True,
    ) -> Path:
        """
        Create animated timelapse banner from captured frames.

        Args:
            frames_dir: Directory with timelapse frames
            output_path: Output GIF path
            fps: Frames per second
            max_frames: Max frames to include
            skip_frames: Skip every N frames
            add_branding: Add Grok & Mon branding
            add_stats_overlay: Add live stats overlay

        Returns:
            Path to created banner
        """
        frames_dir = Path(frames_dir)
        output_path = Path(output_path)

        # Load frame index
        index_file = frames_dir / "frames_index.json"
        metadata_list = []
        if index_file.exists():
            with open(index_file) as f:
                metadata_list = json.load(f)

        # Get frames
        frame_files = sorted(frames_dir.glob("frame_*.jpg"))

        if not frame_files:
            logger.warning("No frames found, creating placeholder banner")
            return self.create_placeholder_banner(output_path)

        # Apply skip and limit
        if skip_frames > 0:
            frame_files = frame_files[::skip_frames + 1]
            metadata_list = metadata_list[::skip_frames + 1] if metadata_list else []

        frame_files = frame_files[:max_frames]
        metadata_list = metadata_list[:max_frames] if metadata_list else []

        # Process frames
        banner_frames = []
        for i, frame_path in enumerate(frame_files):
            metadata = metadata_list[i] if i < len(metadata_list) else {}
            banner = self._create_banner_frame(
                frame_path,
                metadata,
                add_branding=add_branding,
                add_stats=add_stats_overlay,
            )
            banner_frames.append(banner)

        # Save GIF
        duration = 1000 // fps
        banner_frames[0].save(
            output_path,
            save_all=True,
            append_images=banner_frames[1:],
            duration=duration,
            loop=0,
            optimize=True,
        )

        logger.info(f"Created banner: {output_path}")
        return output_path

    def _create_banner_frame(
        self,
        frame_path: Path,
        metadata: dict,
        add_branding: bool = True,
        add_stats: bool = True,
    ) -> Image.Image:
        """Create a single banner frame from timelapse image"""

        # Create banner canvas
        banner = Image.new("RGB", (self.width, self.height), self.colors["black"])

        # Load and process plant image
        plant_img = Image.open(frame_path)

        # Calculate crop/resize to fit banner while keeping plant centered
        # Use center-weighted crop for best plant visibility
        plant_aspect = plant_img.width / plant_img.height
        banner_aspect = self.width / self.height

        if plant_aspect > banner_aspect:
            # Image is wider - fit height, crop width
            new_height = self.height
            new_width = int(new_height * plant_aspect)
        else:
            # Image is taller - fit width, crop height
            new_width = self.width
            new_height = int(new_width / plant_aspect)

        plant_img = plant_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center crop
        left = (new_width - self.width) // 2
        top = (new_height - self.height) // 2
        plant_img = plant_img.crop((left, top, left + self.width, top + self.height))

        # Apply subtle darkening for better text visibility
        enhancer = ImageEnhance.Brightness(plant_img)
        plant_img = enhancer.enhance(0.85)

        banner.paste(plant_img, (0, 0))

        draw = ImageDraw.Draw(banner)

        # Add branding
        if add_branding:
            self._add_branding(draw, banner)

        # Add stats overlay
        if add_stats and metadata:
            self._add_stats_overlay(draw, metadata)

        return banner

    def _add_branding(self, draw: ImageDraw.Draw, banner: Image.Image):
        """Add Grok & Mon branding to banner"""

        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = title_font

        # Title: "GROK & MON"
        title = "GROK & MON"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]

        # Position in top-left with padding
        x, y = 40, 30

        # Draw shadow
        draw.text((x + 2, y + 2), title, fill=(0, 0, 0), font=title_font)
        # Draw text with gradient effect (green to gold)
        draw.text((x, y), title, fill=self.colors["lime"], font=title_font)

        # Subtitle
        subtitle = '"Grok grows your herb, mon" 🌿'
        draw.text((x + 2, y + 60 + 2), subtitle, fill=(0, 0, 0), font=subtitle_font)
        draw.text((x, y + 60), subtitle, fill=self.colors["gold"], font=subtitle_font)

        # Token symbol in corner
        token_text = "$MON"
        token_bbox = draw.textbbox((0, 0), token_text, font=title_font)
        token_x = self.width - (token_bbox[2] - token_bbox[0]) - 40
        draw.text((token_x + 2, y + 2), token_text, fill=(0, 0, 0), font=title_font)
        draw.text((token_x, y), token_text, fill=self.colors["gold"], font=title_font)

    def _add_stats_overlay(self, draw: ImageDraw.Draw, metadata: dict):
        """Add live stats overlay to banner"""

        try:
            stats_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
        except Exception:
            stats_font = ImageFont.load_default()

        # Build stats text
        stats = []
        if "grow_day" in metadata:
            stats.append(f"DAY {metadata['grow_day']}")
        if "growth_stage" in metadata:
            stats.append(metadata['growth_stage'])
        if "temperature_f" in metadata and metadata["temperature_f"]:
            stats.append(f"{metadata['temperature_f']:.1f}°F")
        if "humidity" in metadata and metadata["humidity"]:
            stats.append(f"{metadata['humidity']:.0f}%RH")
        if "vpd" in metadata and metadata["vpd"]:
            stats.append(f"VPD:{metadata['vpd']:.2f}")

        stats_text = " | ".join(stats)

        # Position at bottom
        stats_bbox = draw.textbbox((0, 0), stats_text, font=stats_font)
        stats_width = stats_bbox[2] - stats_bbox[0]
        stats_height = stats_bbox[3] - stats_bbox[1]

        x = (self.width - stats_width) // 2
        y = self.height - stats_height - 30

        # Draw background bar
        padding = 15
        bar_rect = [0, y - padding, self.width, self.height]
        # Semi-transparent black bar
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(bar_rect, fill=(0, 0, 0, 200))

        # Draw stats text
        draw.text((x + 2, y + 2), stats_text, fill=(0, 0, 0), font=stats_font)
        draw.text((x, y), stats_text, fill=self.colors["lime"], font=stats_font)

    def create_stats_banner(
        self,
        grow_day: int,
        stage: str,
        output_path: str | Path,
        frames: int = 30,
        fps: int = 10,
        stats: Optional[dict] = None,
    ) -> Path:
        """
        Create animated stats-only banner.

        Useful when no timelapse frames available.
        Creates animated counters and effects.

        Args:
            grow_day: Current grow day
            stage: Current growth stage
            output_path: Output GIF path
            frames: Number of animation frames
            fps: Frames per second
            stats: Additional stats dict

        Returns:
            Path to created banner
        """
        output_path = Path(output_path)
        banner_frames = []

        for i in range(frames):
            banner = self._create_stats_frame(grow_day, stage, i, frames, stats)
            banner_frames.append(banner)

        duration = 1000 // fps
        banner_frames[0].save(
            output_path,
            save_all=True,
            append_images=banner_frames[1:],
            duration=duration,
            loop=0,
            optimize=True,
        )

        return output_path

    def _create_stats_frame(
        self,
        grow_day: int,
        stage: str,
        frame_num: int,
        total_frames: int,
        stats: Optional[dict] = None,
    ) -> Image.Image:
        """Create a single stats animation frame"""

        banner = Image.new("RGB", (self.width, self.height), self.colors["black"])
        draw = ImageDraw.Draw(banner)

        # Animated gradient background
        progress = frame_num / total_frames
        self._draw_animated_background(draw, progress)

        # Load fonts
        try:
            big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except Exception:
            big_font = ImageFont.load_default()
            medium_font = big_font
            small_font = big_font

        # Animated day counter (counting up effect)
        display_day = min(grow_day, int(grow_day * min(1, progress * 2)))

        # Center content
        center_x = self.width // 2
        center_y = self.height // 2

        # Day counter
        day_text = f"DAY {display_day}"
        day_bbox = draw.textbbox((0, 0), day_text, font=big_font)
        day_x = center_x - (day_bbox[2] - day_bbox[0]) // 2
        day_y = center_y - 80

        # Pulsing effect
        pulse = 1 + 0.05 * math.sin(progress * math.pi * 4)

        draw.text((day_x + 3, day_y + 3), day_text, fill=(0, 0, 0), font=big_font)
        draw.text((day_x, day_y), day_text, fill=self.colors["lime"], font=big_font)

        # Stage
        stage_bbox = draw.textbbox((0, 0), stage, font=medium_font)
        stage_x = center_x - (stage_bbox[2] - stage_bbox[0]) // 2
        draw.text((stage_x, center_y + 20), stage, fill=self.colors["gold"], font=medium_font)

        # Title
        title = "GROK & MON"
        title_bbox = draw.textbbox((0, 0), title, font=medium_font)
        title_x = center_x - (title_bbox[2] - title_bbox[0]) // 2
        draw.text((title_x, 40), title, fill=self.colors["lime"], font=medium_font)

        # Tagline
        tagline = '"Grok grows your herb, mon" 🌿'
        tag_bbox = draw.textbbox((0, 0), tagline, font=small_font)
        tag_x = center_x - (tag_bbox[2] - tag_bbox[0]) // 2
        draw.text((tag_x, self.height - 60), tagline, fill=self.colors["white"], font=small_font)

        # $MON token
        token = "$MON on Monad"
        token_bbox = draw.textbbox((0, 0), token, font=small_font)
        token_x = self.width - (token_bbox[2] - token_bbox[0]) - 40
        draw.text((token_x, 50), token, fill=self.colors["gold"], font=small_font)

        return banner

    def _draw_animated_background(self, draw: ImageDraw.Draw, progress: float):
        """Draw animated gradient background"""

        # Moving gradient lines (cannabis leaf pattern suggestion)
        for i in range(0, self.width + 100, 50):
            offset = int(100 * math.sin(progress * math.pi * 2 + i / 100))
            x1 = i + offset
            draw.line(
                [(x1, 0), (x1 - 200, self.height)],
                fill=(20, 40, 20),
                width=2
            )

    def create_placeholder_banner(self, output_path: str | Path) -> Path:
        """Create a placeholder banner when no frames available"""
        return self.create_stats_banner(
            grow_day=1,
            stage="STARTING SOON",
            output_path=output_path,
            frames=30,
        )

    def create_animated_banner(
        self,
        output_path: str | Path,
        grow_day: int = 1,
        stage: str = "VEGETATIVE",
        frames: int = 60,
        fps: int = 15,
        style: str = "glow",  # glow, wave, pulse, matrix
    ) -> Path:
        """
        Create a stylized animated banner like SOLTOMATO's DexScreener banner.

        Pure animated graphic with effects - no plant photos needed.

        Args:
            output_path: Output GIF path
            grow_day: Current grow day for display
            stage: Current growth stage
            frames: Number of animation frames (more = smoother)
            fps: Frames per second
            style: Animation style (glow, wave, pulse, matrix)

        Returns:
            Path to created banner
        """
        output_path = Path(output_path)
        banner_frames = []

        for i in range(frames):
            progress = i / frames
            banner = self._create_animated_frame(grow_day, stage, progress, style)
            banner_frames.append(banner)

        duration = 1000 // fps
        banner_frames[0].save(
            output_path,
            save_all=True,
            append_images=banner_frames[1:],
            duration=duration,
            loop=0,
            optimize=True,
        )

        logger.info(f"Created animated banner: {output_path}")
        return output_path

    def _create_animated_frame(
        self,
        grow_day: int,
        stage: str,
        progress: float,
        style: str,
    ) -> Image.Image:
        """Create a single animated banner frame with effects"""

        banner = Image.new("RGB", (self.width, self.height), self.colors["black"])
        draw = ImageDraw.Draw(banner)

        # Draw animated background based on style
        if style == "matrix":
            self._draw_matrix_bg(draw, progress)
        elif style == "wave":
            self._draw_wave_bg(draw, progress)
        else:
            self._draw_glow_bg(banner, draw, progress)

        # Load fonts
        try:
            huge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
            big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
            medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except Exception:
            huge_font = ImageFont.load_default()
            big_font = huge_font
            medium_font = huge_font
            small_font = huge_font

        center_x = self.width // 2
        center_y = self.height // 2

        # Animated glow effect intensity
        glow_intensity = 0.5 + 0.5 * math.sin(progress * math.pi * 2)

        # Draw cannabis leaf silhouettes in background
        self._draw_leaf_pattern(draw, progress)

        # Main title with glow effect
        title = "GROK & MON"
        title_bbox = draw.textbbox((0, 0), title, font=huge_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = center_x - title_width // 2
        title_y = 60

        # Glow layers (multiple shadow passes for glow)
        glow_color = (
            int(50 + 100 * glow_intensity),
            int(205 + 50 * glow_intensity),
            int(50 + 100 * glow_intensity),
        )
        for offset in [6, 4, 2]:
            alpha = int(100 * glow_intensity * (1 - offset / 8))
            draw.text((title_x, title_y + offset), title, fill=(0, alpha, 0), font=huge_font)

        # Main title
        draw.text((title_x + 3, title_y + 3), title, fill=(0, 50, 0), font=huge_font)
        draw.text((title_x, title_y), title, fill=self.colors["lime"], font=huge_font)

        # Tagline with wave effect
        tagline = '"Grok grows your herb, mon"'
        tag_bbox = draw.textbbox((0, 0), tagline, font=medium_font)
        tag_width = tag_bbox[2] - tag_bbox[0]
        tag_x = center_x - tag_width // 2
        tag_y = 170 + int(5 * math.sin(progress * math.pi * 4))

        draw.text((tag_x + 2, tag_y + 2), tagline, fill=(0, 0, 0), font=medium_font)
        draw.text((tag_x, tag_y), tagline, fill=self.colors["gold"], font=medium_font)

        # Day counter with counting animation
        display_day = grow_day
        day_text = f"DAY {display_day}"
        day_bbox = draw.textbbox((0, 0), day_text, font=big_font)
        day_width = day_bbox[2] - day_bbox[0]
        day_x = center_x - day_width // 2
        day_y = center_y + 20

        # Pulsing scale effect for day
        scale_factor = 1 + 0.03 * math.sin(progress * math.pi * 3)

        draw.text((day_x + 3, day_y + 3), day_text, fill=(0, 0, 0), font=big_font)
        draw.text((day_x, day_y), day_text, fill=self.colors["lime"], font=big_font)

        # Growth stage
        stage_bbox = draw.textbbox((0, 0), stage, font=medium_font)
        stage_width = stage_bbox[2] - stage_bbox[0]
        stage_x = center_x - stage_width // 2
        stage_y = center_y + 100

        draw.text((stage_x + 2, stage_y + 2), stage, fill=(0, 0, 0), font=medium_font)
        draw.text((stage_x, stage_y), stage, fill=self.colors["gold"], font=medium_font)

        # $MON token badge (top right)
        token_text = "$MON"
        token_bbox = draw.textbbox((0, 0), token_text, font=big_font)
        token_width = token_bbox[2] - token_bbox[0]
        token_x = self.width - token_width - 50
        token_y = 40 + int(3 * math.sin(progress * math.pi * 2 + 1))

        # Token glow
        for offset in [4, 2]:
            draw.text((token_x, token_y + offset), token_text, fill=(80, 60, 0), font=big_font)
        draw.text((token_x + 2, token_y + 2), token_text, fill=(50, 40, 0), font=big_font)
        draw.text((token_x, token_y), token_text, fill=self.colors["gold"], font=big_font)

        # "on Monad" subtitle
        monad_text = "on Monad"
        monad_bbox = draw.textbbox((0, 0), monad_text, font=small_font)
        monad_x = token_x + (token_width - (monad_bbox[2] - monad_bbox[0])) // 2
        draw.text((monad_x, token_y + 70), monad_text, fill=self.colors["purple"], font=small_font)

        # Cannabis emoji / leaf indicator (animated)
        leaf = "🌿"
        leaf_positions = [
            (50, self.height - 80),
            (self.width - 100, self.height - 80),
        ]
        for i, (lx, ly) in enumerate(leaf_positions):
            offset_y = int(8 * math.sin(progress * math.pi * 2 + i * math.pi))
            draw.text((lx, ly + offset_y), leaf, font=medium_font)

        # Bottom bar with live info
        bar_y = self.height - 50
        draw.rectangle([0, bar_y, self.width, self.height], fill=(15, 30, 15))

        # Scrolling text effect in bottom bar
        scroll_text = "🌱 AI-POWERED CULTIVATION • $MON TOKEN • GROK INTELLIGENCE • AUTONOMOUS GROW • "
        scroll_text = scroll_text * 3  # Repeat for seamless scroll

        scroll_offset = int(progress * 500) % 500
        scroll_bbox = draw.textbbox((0, 0), scroll_text, font=small_font)
        draw.text((-scroll_offset, bar_y + 10), scroll_text, fill=self.colors["lime"], font=small_font)

        return banner

    def _draw_glow_bg(self, banner: Image.Image, draw: ImageDraw.Draw, progress: float):
        """Draw glowing gradient background"""

        # Radial gradient effect from center
        center_x, center_y = self.width // 2, self.height // 2

        for i in range(0, max(self.width, self.height), 20):
            intensity = 1 - (i / max(self.width, self.height))
            pulse = 0.5 + 0.5 * math.sin(progress * math.pi * 2 + i / 100)

            green = int(20 + 30 * intensity * pulse)
            color = (5, green, 5)

            draw.ellipse(
                [center_x - i, center_y - i // 2, center_x + i, center_y + i // 2],
                outline=color,
                width=2,
            )

    def _draw_wave_bg(self, draw: ImageDraw.Draw, progress: float):
        """Draw animated wave background"""

        for y in range(0, self.height, 30):
            points = []
            for x in range(0, self.width + 50, 10):
                wave_y = y + int(15 * math.sin(progress * math.pi * 2 + x / 80 + y / 50))
                points.append((x, wave_y))

            if len(points) > 1:
                intensity = 1 - (y / self.height)
                green = int(30 * intensity)
                draw.line(points, fill=(5, green + 10, 5), width=1)

    def _draw_matrix_bg(self, draw: ImageDraw.Draw, progress: float):
        """Draw matrix-style falling characters background"""

        try:
            matrix_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
        except Exception:
            matrix_font = ImageFont.load_default()

        chars = "01アイウエオカキクケコ🌿💚"

        for x in range(0, self.width, 25):
            # Each column falls at different speed
            speed = 0.5 + (x % 100) / 100
            y_offset = int((progress * speed * self.height * 2) % (self.height + 100))

            for y in range(-100, self.height, 20):
                display_y = (y + y_offset) % (self.height + 100) - 50
                if 0 <= display_y < self.height:
                    char = chars[(x + y) % len(chars)]
                    fade = 1 - (display_y / self.height)
                    green = int(100 + 100 * fade)
                    draw.text((x, display_y), char, fill=(0, green, 0), font=matrix_font)

    def _draw_leaf_pattern(self, draw: ImageDraw.Draw, progress: float):
        """Draw subtle animated cannabis leaf pattern"""

        # Simple 7-point leaf silhouette positions
        leaf_positions = [
            (100, 250),
            (self.width - 150, 200),
            (200, 400),
            (self.width - 200, 380),
        ]

        for i, (cx, cy) in enumerate(leaf_positions):
            # Gentle floating animation
            offset_y = int(10 * math.sin(progress * math.pi * 2 + i))
            offset_x = int(5 * math.cos(progress * math.pi * 2 + i))

            # Draw simple leaf shape (5-point star-ish)
            size = 40 + i * 5
            self._draw_simple_leaf(draw, cx + offset_x, cy + offset_y, size, progress + i / 4)

    def _draw_simple_leaf(self, draw: ImageDraw.Draw, cx: int, cy: int, size: int, phase: float):
        """Draw a simple cannabis leaf silhouette"""

        # Breathing effect
        breath = 1 + 0.1 * math.sin(phase * math.pi * 2)
        size = int(size * breath)

        # Very subtle green for background leaf
        alpha = int(30 + 20 * math.sin(phase * math.pi * 2))
        color = (0, alpha, 0)

        # Draw 7 pointed leaf using lines from center
        angles = [0, 30, 60, 90, 120, 150, 180]  # Half the leaf, mirrored
        for angle in angles:
            rad = math.radians(angle - 90)
            length = size * (0.5 + 0.5 * math.sin(rad * 3 + 1))

            x1 = cx
            y1 = cy
            x2 = cx + int(length * math.cos(rad))
            y2 = cy + int(length * math.sin(rad))

            draw.line([(x1, y1), (x2, y2)], fill=color, width=3)

            # Mirror
            x2_mirror = cx - int(length * math.cos(rad))
            draw.line([(x1, y1), (x2_mirror, y2)], fill=color, width=3)


def create_animated_dexscreener_banner(
    output_path: str = "data/banners/grokmon_banner.gif",
    grow_day: int = 1,
    stage: str = "VEGETATIVE",
    style: str = "glow",
) -> Path:
    """
    Create a stylized animated banner for DexScreener.

    Like SOLTOMATO's banner - pure animated graphics.

    Args:
        output_path: Output GIF path
        grow_day: Current grow day
        stage: Current growth stage
        style: Animation style (glow, wave, pulse, matrix)

    Returns:
        Path to created banner
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    banner = BannerGenerator()
    return banner.create_animated_banner(
        output_path=output_path,
        grow_day=grow_day,
        stage=stage,
        style=style,
    )


def create_dexscreener_banner(
    timelapse_dir: str = "data/timelapse",
    output_path: str = "data/timelapse/dexscreener_banner.gif",
    fps: int = 8,
    max_frames: int = 40,
) -> Path:
    """
    Create a DexScreener-ready banner from timelapse.

    Args:
        timelapse_dir: Directory with timelapse frames
        output_path: Output GIF path
        fps: Frames per second
        max_frames: Maximum frames to include

    Returns:
        Path to created banner
    """
    banner = BannerGenerator()
    return banner.create_timelapse_banner(
        frames_dir=timelapse_dir,
        output_path=output_path,
        fps=fps,
        max_frames=max_frames,
    )
