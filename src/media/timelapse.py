"""
Timelapse Capture System
========================
Captures images at regular intervals for grow documentation.
Stores metadata alongside images for GIF generation.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
import logging

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FrameMetadata:
    """Metadata stored with each timelapse frame"""
    timestamp: str
    grow_day: int
    growth_stage: str
    frame_number: int

    # Environmental data at capture time
    temperature_f: Optional[float] = None
    humidity: Optional[float] = None
    vpd: Optional[float] = None

    # Image info
    filename: str = ""
    width: int = 0
    height: int = 0


class TimelapseCapture:
    """
    Captures and manages timelapse frames.

    Usage:
        timelapse = TimelapseCapture(output_dir="data/timelapse")

        # Capture frame with metadata
        timelapse.capture(
            grow_day=14,
            growth_stage="VEGETATIVE",
            sensor_data={"temperature_f": 77, "humidity": 55}
        )

        # Get all frames for a day
        frames = timelapse.get_frames_for_day(14)
    """

    def __init__(
        self,
        output_dir: str = "data/timelapse",
        camera_index: int = 0,
        resolution: tuple[int, int] = (1920, 1080),
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.camera_index = camera_index
        self.resolution = resolution
        self.frame_count = self._get_frame_count()

        # Metadata index file
        self.index_file = self.output_dir / "frames_index.json"
        self.frames_index = self._load_index()

    def _get_frame_count(self) -> int:
        """Count existing frames"""
        return len(list(self.output_dir.glob("frame_*.jpg")))

    def _load_index(self) -> list[dict]:
        """Load frames index from disk"""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except Exception:
                return []
        return []

    def _save_index(self):
        """Save frames index to disk"""
        self.index_file.write_text(json.dumps(self.frames_index, indent=2))

    def capture(
        self,
        grow_day: int,
        growth_stage: str,
        sensor_data: Optional[dict] = None,
        image_path: Optional[str] = None,
    ) -> Optional[FrameMetadata]:
        """
        Capture a timelapse frame.

        Args:
            grow_day: Current grow day
            growth_stage: Current growth stage
            sensor_data: Optional dict with temp, humidity, vpd
            image_path: Optional path to existing image (skip camera capture)

        Returns:
            FrameMetadata for the captured frame
        """
        self.frame_count += 1
        timestamp = datetime.now()
        filename = f"frame_{self.frame_count:06d}.jpg"
        filepath = self.output_dir / filename

        # Capture from camera or copy existing image
        # Priority: explicit image_path > webcam API > direct USB camera
        if image_path:
            shutil.copy(image_path, filepath)
            width, height = self._get_image_dimensions(filepath)
        elif HTTPX_AVAILABLE:
            success, width, height = self._capture_from_api(filepath)
            if not success:
                # Fall back to direct camera capture
                if CV2_AVAILABLE:
                    success, width, height = self._capture_from_camera(filepath)
                    if not success:
                        logger.error("Failed to capture from both webcam API and camera")
                        return None
                else:
                    logger.error("Webcam API failed and cv2 not available")
                    return None
        elif CV2_AVAILABLE:
            success, width, height = self._capture_from_camera(filepath)
            if not success:
                logger.error("Failed to capture from camera")
                return None
        else:
            logger.error("No image source available (httpx and cv2 not installed)")
            return None

        # Build metadata
        metadata = FrameMetadata(
            timestamp=timestamp.isoformat(),
            grow_day=grow_day,
            growth_stage=growth_stage,
            frame_number=self.frame_count,
            filename=filename,
            width=width,
            height=height,
        )

        # Add sensor data if provided
        if sensor_data:
            metadata.temperature_f = sensor_data.get("temperature_f")
            metadata.humidity = sensor_data.get("humidity") or sensor_data.get("humidity_percent")
            metadata.vpd = sensor_data.get("vpd") or sensor_data.get("vpd_kpa")

        # Save metadata
        self.frames_index.append(asdict(metadata))
        self._save_index()

        # Also save metadata alongside image
        meta_file = filepath.with_suffix(".json")
        meta_file.write_text(json.dumps(asdict(metadata), indent=2))

        logger.info(f"Captured frame {self.frame_count}: {filename}")
        return metadata

    def _capture_from_camera(self, filepath: Path) -> tuple[bool, int, int]:
        """Capture image from USB camera"""
        if not CV2_AVAILABLE:
            return False, 0, 0

        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        ret, frame = cap.read()
        cap.release()

        if ret:
            cv2.imwrite(str(filepath), frame)
            height, width = frame.shape[:2]
            return True, width, height

        return False, 0, 0

    def _capture_from_api(
        self,
        filepath: Path,
        api_url: str = "http://localhost:8000/api/webcam/latest",
        timeout: float = 10.0,
    ) -> tuple[bool, int, int]:
        """
        Capture image from the webcam HTTP API.

        The Chromebook server exposes the webcam at /api/webcam/latest
        which returns a JPEG image directly.

        Args:
            filepath: Where to save the captured frame
            api_url: Webcam API endpoint URL
            timeout: Request timeout in seconds

        Returns:
            (success, width, height)
        """
        if not HTTPX_AVAILABLE:
            logger.error("httpx not installed - cannot fetch from webcam API")
            return False, 0, 0

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(api_url)
                response.raise_for_status()

                # Verify we got image data
                content_type = response.headers.get("content-type", "")
                if "image" not in content_type and len(response.content) < 100:
                    logger.error(f"Webcam API returned non-image content: {content_type}")
                    return False, 0, 0

                # Write the raw JPEG bytes
                filepath.write_bytes(response.content)

                # Get dimensions
                width, height = self._get_image_dimensions(filepath)
                logger.info(f"Captured frame from webcam API: {width}x{height}")
                return True, width, height

        except httpx.TimeoutException:
            logger.error(f"Webcam API timeout after {timeout}s")
            return False, 0, 0
        except httpx.HTTPStatusError as e:
            logger.error(f"Webcam API error: {e.response.status_code}")
            return False, 0, 0
        except Exception as e:
            logger.error(f"Webcam API capture failed: {e}")
            return False, 0, 0

    def _get_image_dimensions(self, filepath: Path) -> tuple[int, int]:
        """Get dimensions of an image file"""
        if PIL_AVAILABLE:
            with Image.open(filepath) as img:
                return img.size
        elif CV2_AVAILABLE:
            img = cv2.imread(str(filepath))
            if img is not None:
                h, w = img.shape[:2]
                return w, h
        return 0, 0

    def get_all_frames(self) -> list[FrameMetadata]:
        """Get metadata for all captured frames"""
        return [FrameMetadata(**f) for f in self.frames_index]

    def get_frames_for_day(self, grow_day: int) -> list[FrameMetadata]:
        """Get all frames captured on a specific grow day"""
        return [
            FrameMetadata(**f)
            for f in self.frames_index
            if f["grow_day"] == grow_day
        ]

    def get_frames_for_stage(self, stage: str) -> list[FrameMetadata]:
        """Get all frames from a specific growth stage"""
        return [
            FrameMetadata(**f)
            for f in self.frames_index
            if f["growth_stage"] == stage
        ]

    def get_frame_paths(self, frames: Optional[list[FrameMetadata]] = None) -> list[Path]:
        """Get file paths for frames"""
        if frames is None:
            frames = self.get_all_frames()
        return [self.output_dir / f.filename for f in frames]


def capture_timelapse_frame(
    grow_day: int,
    growth_stage: str,
    sensor_data: Optional[dict] = None,
    output_dir: str = "data/timelapse",
    webcam_url: str = "http://localhost:8000/api/webcam/latest",
) -> Optional[FrameMetadata]:
    """
    Convenience function to capture a single timelapse frame.

    Fetches a webcam image from the API and saves it as
    ``data/timelapse/day{N}_{timestamp}.jpg`` alongside the usual
    sequential ``frame_NNNNNN.jpg`` file managed by TimelapseCapture.

    Call this from the agent decision loop to build timelapse.

    Args:
        grow_day: Current grow day number
        growth_stage: Current growth stage string (e.g. "VEGETATIVE")
        sensor_data: Optional dict with temp, humidity, vpd keys
        output_dir: Base directory for timelapse frames
        webcam_url: Webcam API endpoint

    Returns:
        FrameMetadata for the captured frame, or None on failure
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Save a human-readable named copy: day14_20260208_143022.jpg
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    friendly_name = f"day{grow_day}_{timestamp_str}.jpg"
    friendly_path = out / friendly_name

    # Try fetching from webcam API first
    fetched = False
    if HTTPX_AVAILABLE:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(webcam_url)
                resp.raise_for_status()
                friendly_path.write_bytes(resp.content)
                fetched = True
                logger.info(f"Webcam frame saved: {friendly_name}")
        except Exception as e:
            logger.warning(f"Webcam API fetch failed: {e}")

    # Use TimelapseCapture for indexed storage and metadata
    timelapse = TimelapseCapture(output_dir=output_dir)

    if fetched:
        # Pass the already-downloaded image
        return timelapse.capture(
            grow_day, growth_stage, sensor_data,
            image_path=str(friendly_path),
        )
    else:
        # Let TimelapseCapture try its own capture methods
        metadata = timelapse.capture(grow_day, growth_stage, sensor_data)
        if metadata:
            # Copy the indexed frame to the friendly name as well
            indexed_path = out / metadata.filename
            if indexed_path.exists() and not friendly_path.exists():
                shutil.copy(indexed_path, friendly_path)
        return metadata
