"""
Webcam Night Vision Patch
==========================
Adds faux night vision to the ContinuousWebcam class for dark period visibility.

Usage:
    # In orchestrator or API, enable night mode
    cam = ContinuousWebcam(device_index=2, night_mode=True)
    cam.set_dark_period(True)  # Switch to night vision settings

The camera will:
- Crank up gain/exposure during dark periods
- Apply image brightening in post-processing
- Return to normal settings during light periods
"""

import subprocess
import logging
import numpy as np

logger = logging.getLogger(__name__)


def apply_night_vision_settings(device_index: int):
    """
    Apply camera settings optimized for low-light (faux night vision).

    Args:
        device_index: Video device index (/dev/videoX)
    """
    try:
        device = f"/dev/video{device_index}"

        # Night vision settings: max gain, high exposure, high brightness
        subprocess.run([
            "v4l2-ctl", f"--device={device}",
            "--set-ctrl=brightness=200",      # Max brightness
            "--set-ctrl=contrast=150",        # High contrast
            "--set-ctrl=saturation=100",      # Normal saturation
            "--set-ctrl=gain=255",            # Max gain (ISO)
            "--set-ctrl=exposure_auto=1",     # Manual exposure
            "--set-ctrl=exposure_absolute=600",  # Long exposure (max for C270)
            "--set-ctrl=backlight_compensation=1"  # Enable backlight comp
        ], capture_output=True, timeout=5, check=False)

        logger.info(f"Applied NIGHT VISION settings to {device}")

    except Exception as e:
        logger.warning(f"Could not apply night vision settings: {e}")


def apply_normal_settings(device_index: int):
    """
    Apply normal daytime camera settings.

    Args:
        device_index: Video device index (/dev/videoX)
    """
    try:
        device = f"/dev/video{device_index}"

        # Normal settings: moderate brightness, low gain
        subprocess.run([
            "v4l2-ctl", f"--device={device}",
            "--set-ctrl=brightness=110",
            "--set-ctrl=contrast=128",        # Default
            "--set-ctrl=saturation=128",      # Default
            "--set-ctrl=gain=0",              # Auto gain
            "--set-ctrl=exposure_auto=3",     # Aperture priority auto
            "--set-ctrl=backlight_compensation=0"
        ], capture_output=True, timeout=5, check=False)

        logger.info(f"Applied NORMAL settings to {device}")

    except Exception as e:
        logger.warning(f"Could not apply normal settings: {e}")


def brighten_dark_frame(frame_bytes: bytes, boost: float = 2.5) -> bytes:
    """
    Post-process a dark frame to make it more visible.

    Args:
        frame_bytes: JPEG image bytes
        boost: Brightness multiplier (1.0 = no change, 2.5 = 2.5x brighter)

    Returns:
        Brightened JPEG bytes
    """
    try:
        import cv2
        import numpy as np

        # Decode JPEG
        nparr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return frame_bytes

        # Convert to float for processing
        img_float = img.astype(np.float32)

        # Brighten (gamma correction for natural look)
        img_brightened = np.power(img_float / 255.0, 1.0 / boost) * 255.0
        img_brightened = np.clip(img_brightened, 0, 255).astype(np.uint8)

        # Increase contrast slightly
        img_contrast = cv2.convertScaleAbs(img_brightened, alpha=1.2, beta=10)

        # Add slight green tint for "night vision" aesthetic
        img_tinted = img_contrast.copy()
        img_tinted[:, :, 1] = np.clip(img_tinted[:, :, 1] * 1.1, 0, 255)  # Boost green channel

        # Re-encode to JPEG
        _, buffer = cv2.imencode('.jpg', img_tinted, [cv2.IMWRITE_JPEG_QUALITY, 85])

        return buffer.tobytes()

    except Exception as e:
        logger.error(f"Failed to brighten frame: {e}")
        return frame_bytes  # Return original on error
