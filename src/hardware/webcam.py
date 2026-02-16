"""
USB Webcam Integration
======================

Captures images from USB webcam (Logitech C270) for:
- Timelapse photography
- AI vision analysis
- Live monitoring

Works on Chromebook Linux (Crostini) with proper USB passthrough.

Chromebook Setup:
1. Enable Linux: Settings > Advanced > Developers > Linux
2. Connect webcam to USB
3. Share USB with Linux: Settings > Advanced > Developers > Linux > USB preferences
4. Test: ls /dev/video*
"""

import asyncio
import base64
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import io

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    np = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .base import CameraHub

logger = logging.getLogger(__name__)


@dataclass
class CaptureSettings:
    """Webcam capture settings"""
    width: int = 1280
    height: int = 720
    jpeg_quality: int = 85
    warmup_frames: int = 5  # Discard first N frames (auto-exposure)
    device_index: int = 0


class USBWebcam(CameraHub):
    """
    USB Webcam controller for grow monitoring.

    Optimized for Logitech C270:
    - 720p HD resolution
    - Auto-focus/exposure
    - Works with OpenCV

    Usage:
        webcam = USBWebcam()
        if await webcam.connect():
            image_bytes = await webcam.capture()
            # Save or analyze image
    """

    def __init__(
        self,
        device_index: int = 0,
        resolution: Tuple[int, int] = (1280, 720),
        jpeg_quality: int = 85,
    ):
        """
        Initialize webcam.

        Args:
            device_index: Camera device index (0 = first camera)
            resolution: Capture resolution (width, height)
            jpeg_quality: JPEG compression quality (0-100)
        """
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV required: pip install opencv-python")

        self.device_index = device_index
        self.resolution = resolution
        self.jpeg_quality = jpeg_quality

        self._cap: Optional[cv2.VideoCapture] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to webcam.

        Returns True if successful.
        """
        try:
            # Try to open camera
            self._cap = cv2.VideoCapture(self.device_index)

            if not self._cap.isOpened():
                logger.error(f"Failed to open camera at index {self.device_index}")
                return False

            # Set resolution
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

            # Warm up camera (let auto-exposure settle)
            for _ in range(5):
                self._cap.read()

            self._connected = True
            logger.info(f"Webcam connected at {self.resolution[0]}x{self.resolution[1]}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to webcam: {e}")
            return False

    async def capture(self, save_path: Optional[Path] = None, release_after: bool = True) -> bytes:
        """
        Capture a single frame.

        Args:
            save_path: Optional path to save JPEG file
            release_after: Release camera after capture (allows sharing between processes)

        Returns:
            JPEG image bytes
        """
        # Always try to connect fresh - this allows sharing between processes
        needs_warmup = not self._connected or self._cap is None or not self._cap.isOpened()
        if needs_warmup:
            if not await self.connect():
                raise ConnectionError("Webcam not available")

        try:
            # Extra warmup frames when freshly connected (auto-exposure needs time)
            if needs_warmup:
                for _ in range(10):  # Additional warmup for auto-exposure
                    self._cap.read()

            # Capture frame
            ret, frame = self._cap.read()

            if not ret or frame is None:
                raise RuntimeError("Failed to capture frame")

            # Encode to JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_params)
            image_bytes = buffer.tobytes()

            # Save if path provided
            if save_path:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(image_bytes)
                logger.debug(f"Saved frame to {save_path}")

            return image_bytes

        except Exception as e:
            logger.error(f"Capture failed: {e}")
            raise
        finally:
            # Release camera after capture to allow other processes to use it
            if release_after and self._cap is not None:
                self._cap.release()
                self._cap = None
                self._connected = False

    async def capture_for_analysis(self) -> Tuple[bytes, str]:
        """
        Capture image optimized for AI analysis.

        Returns:
            Tuple of (jpeg_bytes, base64_encoded_string)
        """
        image_bytes = await self.capture()
        b64_string = base64.b64encode(image_bytes).decode('utf-8')
        return image_bytes, b64_string

    async def capture_with_timestamp(
        self,
        save_dir: Path,
        prefix: str = "capture",
    ) -> Path:
        """
        Capture and save with timestamp filename.

        Args:
            save_dir: Directory to save images
            prefix: Filename prefix

        Returns:
            Path to saved image
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        save_path = save_dir / filename

        await self.capture(save_path)
        return save_path

    async def is_connected(self) -> bool:
        """Check if webcam is connected and working"""
        if not self._cap:
            return False

        return self._cap.isOpened()

    def get_resolution(self) -> Tuple[int, int]:
        """Get current capture resolution"""
        if self._cap and self._cap.isOpened():
            width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        return self.resolution

    async def disconnect(self):
        """Release webcam"""
        if self._cap:
            self._cap.release()
            self._cap = None
        self._connected = False
        logger.info("Webcam disconnected")

    def __del__(self):
        """Cleanup on destruction"""
        if self._cap:
            self._cap.release()


# =============================================================================
# Continuous Frame Grabber (for API serving)
# =============================================================================

class ContinuousWebcam:
    """
    Webcam with continuous frame grabbing in a background thread.
    Keeps camera open and serves frames from a buffer instantly.

    Use this for API endpoints that need fast response times.
    """

    def __init__(
        self,
        device_index: int = 0,
        resolution: Tuple[int, int] = (1280, 720),
        jpeg_quality: int = 85,
        frame_interval: float = 0.5,  # Capture every 0.5 seconds
        exposure: Optional[int] = None,  # Manual exposure (-10 to 0, lower = darker)
        night_mode: bool = False,  # Enable faux night vision during dark periods
    ):
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV required: pip install opencv-python")

        self.device_index = device_index
        self.resolution = resolution
        self.jpeg_quality = jpeg_quality
        self.frame_interval = frame_interval
        self.exposure = exposure
        self.night_mode = night_mode

        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Frame buffer
        self._latest_frame: Optional[bytes] = None
        self._frame_time: Optional[datetime] = None
        self._is_dark_period = False  # Track if currently in dark period
        self._frame_count = 0  # Counter for periodic settings re-apply
        self._settings_interval = 600  # Re-apply camera settings every 600 frames (~5 min at 0.5s)

    def start(self) -> bool:
        """Start the continuous frame grabber thread."""
        if self._running:
            return True

        # Open camera
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            logger.error(f"Failed to open camera at index {self.device_index}")
            return False

        # Set resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        # Set buffer size to 1 to always get latest frame
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Apply v4l2-ctl camera settings (works better than OpenCV for Logitech webcams)
        self._apply_camera_settings(night_mode=False)  # Start with normal settings

        # Warmup
        for _ in range(10):
            self._cap.read()

        # Start background thread
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        logger.info(f"ContinuousWebcam started at {self.resolution[0]}x{self.resolution[1]}")
        return True

    def _apply_camera_settings(self, night_mode: bool = False):
        """Apply camera settings for normal or night vision mode."""
        try:
            import subprocess
            device = f"/dev/video{self.device_index}"

            if night_mode and self.night_mode:
                # NIGHT VISION MODE: Max everything for low light
                subprocess.run([
                    "v4l2-ctl", f"--device={device}",
                    "--set-ctrl=brightness=255",       # MAX brightness
                    "--set-ctrl=contrast=200",         # High contrast
                    "--set-ctrl=saturation=150",       # Boost saturation for better visibility
                    "--set-ctrl=gain=255",             # MAX gain (ISO equivalent)
                    "--set-ctrl=sharpness=200",        # High sharpness
                    "--set-ctrl=exposure_auto=1",      # Manual exposure mode
                    "--set-ctrl=exposure_absolute=1000",  # VERY long exposure (max possible)
                    "--set-ctrl=backlight_compensation=2",  # Max backlight comp
                    "--set-ctrl=white_balance_temperature_auto=0",  # Disable auto white balance
                    "--set-ctrl=white_balance_temperature=4000"  # Warmer WB for low light
                ], capture_output=True, timeout=5, check=False)
                logger.info(f"NIGHT VISION mode: gain=255, exposure=1000, brightness=255")
            else:
                # NORMAL MODE: Manual exposure to handle bright grow light
                # Calibrated Jan 26 2026 - prevents washout from 600W LED at 50%
                # Feb 15 2026: Auto WB + low saturation is the winning combo.
                # Manual WB at any temperature caused persistent yellow cast.
                # Auto WB adapts to LED spectrum; low saturation prevents
                # warm color amplification.
                settings = [
                    ("brightness", "45"),        # Low — bright LED washes out at higher values
                    ("contrast", "50"),          # Above default — adds depth under flat LED light
                    ("saturation", "20"),        # Low — prevents warm LED color amplification
                    ("gain", "8"),               # Low — LED is bright enough
                    ("sharpness", "50"),         # Moderate — avoids halo artifacts
                    ("auto_exposure", "1"),      # Manual exposure mode
                    ("exposure_time_absolute", "25"),  # Short — prevents washout under 600W LED
                    ("backlight_compensation", "0"),
                    ("white_balance_automatic", "1"),  # Auto WB — adapts to grow LED spectrum
                ]
                for ctrl, val in settings:
                    subprocess.run(
                        ["v4l2-ctl", f"--device={device}", f"--set-ctrl={ctrl}={val}"],
                        capture_output=True, timeout=5, check=False,
                    )
                logger.info(f"Normal camera settings: brightness=45, contrast=50, sat=20, gain=8, exposure=25, WB=auto")
        except Exception as e:
            logger.warning(f"Could not apply camera settings: {e}")

    def _enforce_white_balance(self):
        """Ensure auto white balance stays enabled.

        Under grow LEDs, auto WB with low saturation produces the best
        color balance. This method ensures auto WB hasn't been disabled
        by the driver or another process.
        """
        try:
            import subprocess
            device = f"/dev/video{self.device_index}"
            # Ensure auto WB is ON — manual WB at any temperature caused yellow
            for ctrl in ["white_balance_automatic", "white_balance_temperature_auto"]:
                subprocess.run(
                    ["v4l2-ctl", f"--device={device}", f"--set-ctrl={ctrl}=1"],
                    capture_output=True, timeout=3, check=False,
                )
        except Exception:
            pass  # Silently fail — this is a best-effort periodic fix

    def set_dark_period(self, is_dark: bool):
        """Switch between normal and night vision mode based on light schedule."""
        if not self.night_mode:
            return  # Night mode disabled

        if is_dark != self._is_dark_period:
            self._is_dark_period = is_dark
            self._apply_camera_settings(night_mode=is_dark)
            logger.info(f"Camera mode: {'NIGHT VISION' if is_dark else 'NORMAL'}")

    def _brighten_frame(self, frame):
        """Apply advanced low-light enhancement for night vision."""
        if not self._is_dark_period or not self.night_mode:
            return frame

        try:
            # Step 1: Denoise first (critical for high-gain footage)
            denoised = cv2.fastNlMeansDenoisingColored(frame, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)

            # Step 2: Convert to LAB color space for better luminance control
            lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Step 3: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to luminance
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)

            # Step 4: Brighten luminance with gamma correction
            l_float = l_clahe.astype('float32') / 255.0
            l_brightened = np.power(l_float, 0.5) * 255.0  # Gamma 0.5
            l_brightened = np.clip(l_brightened, 0, 255).astype('uint8')

            # Step 5: Merge back and convert to BGR
            enhanced_lab = cv2.merge([l_brightened, a, b])
            enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

            # Step 6: Boost saturation slightly
            hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV).astype('float32')
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.3, 0, 255)  # 30% more saturation
            hsv = hsv.astype('uint8')
            final = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            # Step 7: Add slight green tint for night vision aesthetic
            final[:, :, 1] = np.clip(final[:, :, 1] * 1.08, 0, 255)

            return final

        except Exception as e:
            logger.error(f"Frame enhancement failed: {e}")
            return frame

    def _enhance_for_analysis(self, frame):
        """Enhance a frame for plant health analysis under grow lights.

        Corrects grow-light color cast, boosts greens/yellows for deficiency
        detection, and sharpens leaf detail — without changing what the camera
        streams to humans.  Only used when ``get_analysis_frame()`` is called.
        """
        try:
            # 1. Partial gray-world white-balance correction (60% strength)
            #    Full gray-world overcorrects under grow LEDs because the
            #    scene is dominated by warm light.  Partial correction
            #    reduces the cast enough to reveal yellowing without
            #    swinging the image to blue/cyan.
            WB_STRENGTH = 0.35  # 0 = no correction, 1 = full gray-world
            result = frame.astype('float32')
            avg_b = np.mean(result[:, :, 0])
            avg_g = np.mean(result[:, :, 1])
            avg_r = np.mean(result[:, :, 2])
            avg_all = (avg_b + avg_g + avg_r) / 3
            if avg_b > 0:
                factor_b = avg_all / avg_b
                result[:, :, 0] *= 1.0 + WB_STRENGTH * (factor_b - 1.0)
            if avg_g > 0:
                factor_g = avg_all / avg_g
                result[:, :, 1] *= 1.0 + WB_STRENGTH * (factor_g - 1.0)
            if avg_r > 0:
                factor_r = avg_all / avg_r
                result[:, :, 2] *= 1.0 + WB_STRENGTH * (factor_r - 1.0)
            result = np.clip(result, 0, 255).astype('uint8')

            # 2. CLAHE on luminance for even exposure across the canopy
            lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
            l_ch, a_ch, b_ch = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_ch = clahe.apply(l_ch)
            result = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)

            # 3. Gentle unsharp-mask sharpening for leaf texture / spots
            blurred = cv2.GaussianBlur(result, (0, 0), 3)
            result = cv2.addWeighted(result, 1.3, blurred, -0.3, 0)

            return result
        except Exception as e:
            logger.warning(f"Frame enhancement for analysis failed: {e}")
            return frame

    def get_analysis_frame(self) -> Optional[bytes]:
        """Return latest frame enhanced for plant-health AI analysis.

        Applies white-balance correction, CLAHE contrast normalization,
        and sharpening so the vision model can reliably detect yellowing,
        spots, curling, pests, etc. under grow-light conditions.
        """
        with self._lock:
            raw = self._latest_frame
        if raw is None:
            return None

        # Decode JPEG → numpy, enhance, re-encode
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return raw  # fallback to unenhanced

        enhanced = self._enhance_for_analysis(frame)
        _, buf = cv2.imencode('.jpg', enhanced,
                              [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        return buf.tobytes()

    def _capture_loop(self):
        """Background thread that continuously grabs frames."""
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]

        while self._running:
            try:
                ret, frame = self._cap.read()
                if ret and frame is not None:
                    self._frame_count += 1

                    # Periodically re-enforce white balance to prevent yellow drift
                    # The C270 driver can silently reset to auto WB
                    if (self._frame_count % self._settings_interval == 0
                            and not self._is_dark_period):
                        self._enforce_white_balance()

                    # Apply night vision brightening if in dark period
                    if self._is_dark_period and self.night_mode:
                        frame = self._brighten_frame(frame)

                    # Encode to JPEG
                    _, buffer = cv2.imencode('.jpg', frame, encode_params)
                    frame_bytes = buffer.tobytes()

                    # Update buffer
                    with self._lock:
                        self._latest_frame = frame_bytes
                        self._frame_time = datetime.now()
                else:
                    logger.warning("Frame capture failed, attempting reconnect...")
                    # Try to reconnect
                    self._cap.release()
                    time.sleep(1)
                    self._cap = cv2.VideoCapture(self.device_index)
                    self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                    self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                    self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self._apply_camera_settings(night_mode=self._is_dark_period)
                    self._frame_count = 0  # Reset counter after reconnect
                    for _ in range(5):
                        self._cap.read()
            except Exception as e:
                logger.error(f"Capture loop error: {e}")

            time.sleep(self.frame_interval)

    def get_frame(self) -> Optional[bytes]:
        """Get the latest frame instantly from buffer."""
        with self._lock:
            return self._latest_frame

    def get_frame_age(self) -> Optional[float]:
        """Get age of latest frame in seconds."""
        with self._lock:
            if self._frame_time:
                return (datetime.now() - self._frame_time).total_seconds()
            return None

    async def capture(self, save_path: Optional[Path] = None, release_after: bool = False) -> bytes:
        """
        Get frame from buffer (compatible with USBWebcam interface).

        Args:
            save_path: Optional path to save JPEG file
            release_after: Ignored for continuous webcam

        Returns:
            JPEG image bytes
        """
        frame = self.get_frame()
        if frame is None:
            raise ConnectionError("No frame available")

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(frame)

        return frame

    async def is_connected(self) -> bool:
        """Check if webcam is running and has frames."""
        return self._running and self._latest_frame is not None

    def stop(self):
        """Stop the frame grabber and release camera."""
        self._running = False
        if hasattr(self, '_thread') and self._thread:
            self._thread.join(timeout=2.0)
        if hasattr(self, '_cap') and self._cap:
            self._cap.release()
            self._cap = None
        logger.info("ContinuousWebcam stopped")

    def __del__(self):
        """Cleanup on destruction."""
        self.stop()


# =============================================================================
# IP Camera (for network streams like Alfred, IP Webcam apps)
# =============================================================================

class IPCamera:
    """
    Network IP camera that captures from HTTP/RTSP streams.

    Works with apps like:
    - Alfred Camera (local network mode)
    - IP Webcam (Android)
    - Any RTSP/MJPEG camera

    Common URL formats:
    - IP Webcam: http://[ip]:8080/shot.jpg (snapshot)
    - IP Webcam: http://[ip]:8080/video (MJPEG stream)
    - Alfred: Varies by setup
    - RTSP: rtsp://[ip]:[port]/live

    Usage:
        # For snapshot URL (recommended - simpler and more reliable)
        cam = IPCamera(snapshot_url="http://192.168.1.100:8080/shot.jpg")
        cam.start()
        frame = cam.get_frame()

        # For video stream
        cam = IPCamera(stream_url="http://192.168.1.100:8080/video")
        cam.start()
    """

    def __init__(
        self,
        stream_url: Optional[str] = None,
        snapshot_url: Optional[str] = None,
        name: str = "IP Camera",
        jpeg_quality: int = 85,
        frame_interval: float = 1.0,  # Capture interval for streams
        timeout: int = 5,  # Connection timeout
        username: Optional[str] = None,  # For digest auth
        password: Optional[str] = None,  # For digest auth
    ):
        """
        Initialize IP camera.

        Args:
            stream_url: RTSP or MJPEG stream URL (OpenCV VideoCapture)
            snapshot_url: HTTP URL that returns a JPEG image
            name: Display name for this camera
            jpeg_quality: JPEG compression quality for re-encoding
            frame_interval: How often to grab frames from stream
            timeout: Connection timeout in seconds
            username: Username for digest authentication
            password: Password for digest authentication
        """
        if not stream_url and not snapshot_url:
            raise ValueError("Either stream_url or snapshot_url required")

        self.stream_url = stream_url
        self.snapshot_url = snapshot_url
        self.name = name
        self.jpeg_quality = jpeg_quality
        self.frame_interval = frame_interval
        self.timeout = timeout
        self.username = username
        self.password = password

        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._opener = None  # URL opener with auth handler

        # Frame buffer
        self._latest_frame: Optional[bytes] = None
        self._frame_time: Optional[datetime] = None
        self._error: Optional[str] = None

    def _create_opener(self):
        """Create URL opener with optional digest authentication."""
        import urllib.request
        from urllib.parse import urlparse

        if self.username and self.password:
            # Set up digest auth handler
            parsed = urlparse(self.snapshot_url)
            top_level_url = f"{parsed.scheme}://{parsed.netloc}/"

            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, top_level_url, self.username, self.password)

            digest_handler = urllib.request.HTTPDigestAuthHandler(password_mgr)
            self._opener = urllib.request.build_opener(digest_handler)
            logger.info(f"IPCamera {self.name}: Using digest authentication")
        else:
            self._opener = urllib.request.build_opener()

    def _fetch_snapshot(self) -> bytes:
        """Fetch a snapshot using the configured opener."""
        import urllib.request

        req = urllib.request.Request(self.snapshot_url, headers={'User-Agent': 'GrokMon/1.0'})
        with self._opener.open(req, timeout=self.timeout) as response:
            return response.read()

    def start(self) -> bool:
        """Start the IP camera capture thread."""
        if self._running:
            return True

        # Test connection first
        if self.snapshot_url:
            try:
                self._create_opener()
                data = self._fetch_snapshot()
                if len(data) < 100:  # Too small to be a valid image
                    self._error = "Invalid response from snapshot URL"
                    logger.error(f"IPCamera {self.name}: {self._error}")
                    return False
                # Store initial frame
                with self._lock:
                    self._latest_frame = data
                    self._frame_time = datetime.now()
                logger.info(f"IPCamera {self.name}: Connected to {self.snapshot_url}")
            except Exception as e:
                self._error = f"Failed to connect: {e}"
                logger.error(f"IPCamera {self.name}: {self._error}")
                return False

        elif self.stream_url:
            self._cap = cv2.VideoCapture(self.stream_url)
            if not self._cap.isOpened():
                self._error = f"Failed to open stream: {self.stream_url}"
                logger.error(f"IPCamera {self.name}: {self._error}")
                return False
            logger.info(f"IPCamera {self.name}: Connected to stream {self.stream_url}")

        # Start background thread
        self._running = True
        self._error = None
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        logger.info(f"IPCamera {self.name}: Started")
        return True

    def _capture_loop(self):
        """Background thread that continuously grabs frames."""
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self._running:
            try:
                frame_bytes = None

                if self.snapshot_url:
                    # Fetch snapshot via HTTP (with digest auth if configured)
                    frame_bytes = self._fetch_snapshot()

                elif self.stream_url and self._cap:
                    # Grab frame from video stream
                    ret, frame = self._cap.read()
                    if ret and frame is not None:
                        _, buffer = cv2.imencode('.jpg', frame, encode_params)
                        frame_bytes = buffer.tobytes()
                    else:
                        # Try reconnect
                        logger.warning(f"IPCamera {self.name}: Frame capture failed, reconnecting...")
                        self._cap.release()
                        time.sleep(1)
                        self._cap = cv2.VideoCapture(self.stream_url)

                if frame_bytes:
                    with self._lock:
                        self._latest_frame = frame_bytes
                        self._frame_time = datetime.now()
                        self._error = None
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1

            except Exception as e:
                consecutive_errors += 1
                with self._lock:
                    self._error = str(e)
                logger.warning(f"IPCamera {self.name}: Capture error: {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"IPCamera {self.name}: Too many errors, slowing down...")
                    time.sleep(5)  # Back off on repeated errors

            time.sleep(self.frame_interval)

    def get_frame(self) -> Optional[bytes]:
        """Get the latest frame from buffer."""
        with self._lock:
            return self._latest_frame

    def get_frame_age(self) -> Optional[float]:
        """Get age of latest frame in seconds."""
        with self._lock:
            if self._frame_time:
                return (datetime.now() - self._frame_time).total_seconds()
            return None

    def get_error(self) -> Optional[str]:
        """Get last error message if any."""
        with self._lock:
            return self._error

    async def capture(self, save_path: Optional[Path] = None, release_after: bool = False) -> bytes:
        """Get frame from buffer (compatible interface)."""
        frame = self.get_frame()
        if frame is None:
            raise ConnectionError(f"No frame available from {self.name}")

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(frame)

        return frame

    async def is_connected(self) -> bool:
        """Check if camera is running and has frames."""
        return self._running and self._latest_frame is not None

    def stop(self):
        """Stop capture and release resources."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info(f"IPCamera {self.name}: Stopped")

    def __del__(self):
        """Cleanup on destruction."""
        self.stop()


# =============================================================================
# Timelapse Capture Integration
# =============================================================================

class TimelapseController:
    """
    Manages timelapse capture for grow documentation.

    Captures frames at regular intervals with metadata.
    Integrates with the existing timelapse system.
    """

    def __init__(
        self,
        output_dir: str = "data/timelapse",
        webcam: Optional[USBWebcam] = None,
        interval_seconds: int = 3600,  # 1 hour default
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.webcam = webcam or USBWebcam()
        self.interval = interval_seconds

        self._running = False
        self._frame_count = self._count_existing_frames()

    def _count_existing_frames(self) -> int:
        """Count existing timelapse frames"""
        return len(list(self.output_dir.glob("frame_*.jpg")))

    async def capture_frame(
        self,
        grow_day: int,
        growth_stage: str,
        sensor_data: Optional[dict] = None,
    ) -> Path:
        """
        Capture a single timelapse frame with metadata.

        Args:
            grow_day: Current grow day
            growth_stage: Current stage (SEEDLING, VEGETATIVE, etc.)
            sensor_data: Optional sensor readings to embed in metadata

        Returns:
            Path to saved frame
        """
        self._frame_count += 1
        filename = f"frame_{self._frame_count:06d}.jpg"
        frame_path = self.output_dir / filename

        # Capture image
        await self.webcam.capture(frame_path)

        # Save metadata alongside
        metadata = {
            "frame_number": self._frame_count,
            "timestamp": datetime.now().isoformat(),
            "grow_day": grow_day,
            "growth_stage": growth_stage,
            "sensor_data": sensor_data,
        }

        meta_path = frame_path.with_suffix('.json')
        import json
        meta_path.write_text(json.dumps(metadata, indent=2))

        logger.info(f"Captured timelapse frame {self._frame_count}")
        return frame_path

    async def run_continuous(
        self,
        get_grow_day: callable,
        get_growth_stage: callable,
        get_sensor_data: callable = None,
    ):
        """
        Run continuous timelapse capture.

        Args:
            get_grow_day: Callable that returns current grow day
            get_growth_stage: Callable that returns current growth stage
            get_sensor_data: Optional callable for sensor data
        """
        self._running = True
        logger.info(f"Starting timelapse capture every {self.interval}s")

        while self._running:
            try:
                grow_day = get_grow_day() if callable(get_grow_day) else get_grow_day
                stage = get_growth_stage() if callable(get_growth_stage) else get_growth_stage
                sensors = get_sensor_data() if get_sensor_data and callable(get_sensor_data) else None

                await self.capture_frame(grow_day, stage, sensors)

            except Exception as e:
                logger.error(f"Timelapse capture failed: {e}")

            await asyncio.sleep(self.interval)

    def stop(self):
        """Stop continuous capture"""
        self._running = False

    @property
    def frame_count(self) -> int:
        """Get total frame count"""
        return self._frame_count


# =============================================================================
# Device Discovery
# =============================================================================

def list_cameras() -> List[dict]:
    """
    List available camera devices.

    Returns list of dicts with camera info.
    """
    if not CV2_AVAILABLE:
        return []

    cameras = []

    # Check first 5 device indices
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Try to get device name from sysfs
            name = None
            try:
                name_path = Path(f"/sys/class/video4linux/video{i}/name")
                if name_path.exists():
                    name = name_path.read_text().strip()
            except Exception:
                pass

            cameras.append({
                "index": i,
                "name": name,
                "resolution": f"{width}x{height}",
                "fps": fps,
                "backend": cap.getBackendName(),
            })
            cap.release()

    return cameras


def find_camera_by_name(name_pattern: str) -> Optional[int]:
    """
    Find camera device index by name pattern.

    Args:
        name_pattern: Substring to match in camera name (case-insensitive)

    Returns:
        Device index if found, None otherwise
    """
    try:
        video_dir = Path("/sys/class/video4linux")
        if not video_dir.exists():
            return None

        for video_dev in sorted(video_dir.iterdir()):
            name_file = video_dev / "name"
            if name_file.exists():
                dev_name = name_file.read_text().strip()
                if name_pattern.lower() in dev_name.lower():
                    # Extract device number from video0, video2, etc.
                    dev_num = int(video_dev.name.replace("video", ""))
                    return dev_num
    except Exception:
        pass
    return None


def get_logitech_index() -> int:
    """
    Find the Logitech C270 camera index.

    Returns device index, defaulting to 0 if not found.
    """
    idx = find_camera_by_name("C270")
    if idx is not None:
        return idx
    # Fallback to common index 0 (most common default)
    return 0


# =============================================================================
# CLI for Testing
# =============================================================================

async def main():
    """Test webcam functionality"""
    import sys

    print("USB Webcam Test")
    print("=" * 40)

    # List cameras
    print("\nDiscovering cameras...")
    cameras = list_cameras()

    if not cameras:
        print("No cameras found!")
        print("\nTroubleshooting:")
        print("1. Check webcam is connected to USB")
        print("2. On Chromebook: Share USB with Linux in settings")
        print("3. Run: ls /dev/video*")
        sys.exit(1)

    print(f"Found {len(cameras)} camera(s):")
    for cam in cameras:
        print(f"  [{cam['index']}] {cam['resolution']} @ {cam['fps']}fps ({cam['backend']})")

    # Test capture
    print("\nTesting capture...")
    webcam = USBWebcam(device_index=cameras[0]['index'])

    if await webcam.connect():
        test_path = Path("test_capture.jpg")
        await webcam.capture(test_path)
        print(f"Saved test image to: {test_path}")
        print(f"File size: {test_path.stat().st_size / 1024:.1f} KB")
        await webcam.disconnect()
    else:
        print("Failed to connect to webcam")
        sys.exit(1)

    print("\nWebcam test complete!")


if __name__ == "__main__":
    asyncio.run(main())
