"""
GIF Generator for Grok & Mon
============================
Creates animated GIFs from timelapse frames.
Supports data overlays, text annotations, and various styles.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import logging

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class GifGenerator:
    """
    Generate animated GIFs from image sequences.

    Features:
    - Variable frame duration
    - Data overlays (temp, humidity, VPD, day)
    - Text annotations
    - Resize/crop options
    - Loop control

    Usage:
        gen = GifGenerator()
        gen.create_gif(
            input_frames=["frame_001.jpg", "frame_002.jpg", ...],
            output_path="grow_timelapse.gif",
            fps=10,
            overlay_data=True
        )
    """

    def __init__(self):
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow required for GIF generation. Install with: pip install Pillow")

        # Default overlay settings
        self.overlay_font_size = 24
        self.overlay_color = (0, 255, 100)  # Green
        self.overlay_bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.overlay_position = "bottom"  # top, bottom, corner

    def create_gif(
        self,
        input_frames: list[str | Path],
        output_path: str | Path,
        fps: int = 10,
        duration_ms: Optional[int] = None,
        size: Optional[tuple[int, int]] = None,
        loop: int = 0,  # 0 = infinite loop
        overlay_data: bool = False,
        frame_metadata: Optional[list[dict]] = None,
        optimize: bool = True,
    ) -> Path:
        """
        Create an animated GIF from image frames.

        Args:
            input_frames: List of image file paths
            output_path: Output GIF path
            fps: Frames per second (ignored if duration_ms set)
            duration_ms: Duration per frame in milliseconds
            size: Output size (width, height) - None to keep original
            loop: Number of loops (0 = infinite)
            overlay_data: Whether to add data overlay
            frame_metadata: List of metadata dicts for each frame
            optimize: Whether to optimize GIF size

        Returns:
            Path to created GIF
        """
        if not input_frames:
            raise ValueError("No input frames provided")

        output_path = Path(output_path)
        duration = duration_ms or (1000 // fps)

        # Load and process frames
        frames = []
        for i, frame_path in enumerate(input_frames):
            img = Image.open(frame_path)

            # Resize if needed
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)

            # Convert to RGB if necessary (GIF doesn't support RGBA well)
            if img.mode == "RGBA":
                # Create white background
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Add overlay if requested
            if overlay_data and frame_metadata and i < len(frame_metadata):
                img = self._add_overlay(img, frame_metadata[i])

            frames.append(img)

        # Save GIF
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            optimize=optimize,
        )

        logger.info(f"Created GIF: {output_path} ({len(frames)} frames, {fps}fps)")
        return output_path

    def _add_overlay(self, img: Image.Image, metadata: dict) -> Image.Image:
        """Add data overlay to frame"""
        draw = ImageDraw.Draw(img)

        # Try to load a nice font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", self.overlay_font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", self.overlay_font_size)
            except Exception:
                font = ImageFont.load_default()

        # Build overlay text
        lines = []
        if "grow_day" in metadata:
            lines.append(f"Day {metadata['grow_day']}")
        if "growth_stage" in metadata:
            lines.append(metadata['growth_stage'])
        if "temperature_f" in metadata and metadata["temperature_f"]:
            lines.append(f"{metadata['temperature_f']:.1f}°F")
        if "humidity" in metadata and metadata["humidity"]:
            lines.append(f"{metadata['humidity']:.0f}% RH")
        if "vpd" in metadata and metadata["vpd"]:
            lines.append(f"VPD: {metadata['vpd']:.2f}")

        overlay_text = " | ".join(lines)

        # Calculate position
        bbox = draw.textbbox((0, 0), overlay_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 10
        if self.overlay_position == "bottom":
            x = (img.width - text_width) // 2
            y = img.height - text_height - padding - 20
        elif self.overlay_position == "top":
            x = (img.width - text_width) // 2
            y = padding
        else:  # corner
            x = padding
            y = img.height - text_height - padding - 20

        # Draw background rectangle
        bg_rect = [x - padding, y - padding // 2, x + text_width + padding, y + text_height + padding // 2]
        draw.rectangle(bg_rect, fill=self.overlay_bg_color)

        # Draw text
        draw.text((x, y), overlay_text, fill=self.overlay_color, font=font)

        return img

    def create_from_timelapse(
        self,
        timelapse_dir: str | Path,
        output_path: str | Path,
        fps: int = 10,
        size: Optional[tuple[int, int]] = None,
        overlay_data: bool = True,
        skip_frames: int = 0,
        max_frames: Optional[int] = None,
    ) -> Path:
        """
        Create GIF from timelapse directory.

        Automatically loads frames and metadata from timelapse directory.

        Args:
            timelapse_dir: Path to timelapse directory
            output_path: Output GIF path
            fps: Frames per second
            size: Output size (width, height)
            overlay_data: Whether to add data overlay
            skip_frames: Skip every N frames (for faster GIF)
            max_frames: Maximum frames to include

        Returns:
            Path to created GIF
        """
        timelapse_dir = Path(timelapse_dir)
        index_file = timelapse_dir / "frames_index.json"

        # Load frame index
        if index_file.exists():
            with open(index_file) as f:
                all_metadata = json.load(f)
        else:
            # Fall back to scanning for images
            all_metadata = []

        # Get frame files
        frame_files = sorted(timelapse_dir.glob("frame_*.jpg"))

        if not frame_files:
            raise ValueError(f"No frames found in {timelapse_dir}")

        # Apply skip and max
        if skip_frames > 0:
            frame_files = frame_files[::skip_frames + 1]
            all_metadata = all_metadata[::skip_frames + 1] if all_metadata else []

        if max_frames:
            frame_files = frame_files[:max_frames]
            all_metadata = all_metadata[:max_frames] if all_metadata else []

        return self.create_gif(
            input_frames=frame_files,
            output_path=output_path,
            fps=fps,
            size=size,
            overlay_data=overlay_data,
            frame_metadata=all_metadata if overlay_data else None,
        )


def create_grow_gif(
    timelapse_dir: str = "data/timelapse",
    output_path: str = "data/timelapse/grow_timelapse.gif",
    fps: int = 10,
    size: tuple[int, int] = (640, 480),
    overlay: bool = True,
) -> Path:
    """
    Convenience function to create a grow timelapse GIF.

    Args:
        timelapse_dir: Directory containing timelapse frames
        output_path: Output GIF path
        fps: Frames per second
        size: Output dimensions
        overlay: Include data overlay

    Returns:
        Path to created GIF
    """
    gen = GifGenerator()
    return gen.create_from_timelapse(
        timelapse_dir=timelapse_dir,
        output_path=output_path,
        fps=fps,
        size=size,
        overlay_data=overlay,
    )
