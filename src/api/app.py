"""
FastAPI Application
===================

Main API server for Grok & Mon website.
Endpoints match SOLTOMATO's claudeandsol.com structure for frontend compatibility.

Endpoints:
    GET  /api/sensors/latest     - Current sensor readings
    GET  /api/sensors/history    - Historical sensor data
    GET  /api/devices/latest     - Current device states
    GET  /api/ai/latest          - Latest AI output
    GET  /api/grow/stage         - Growth stage info (cannabis-specific)
    GET  /api/webcam/og-image    - Webcam image for social sharing
    WS   /ws/sensors             - Real-time sensor updates
"""

import asyncio
import logging
import os

# Configure logger for this module
logger = logging.getLogger(__name__)
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.middleware.base import BaseHTTPMiddleware
import json

# Support both relative and absolute imports
try:
    from ..db.connection import init_database, close_database, get_db_session
    from ..db.repository import GrowRepository
    from ..hardware import MockSensorHub, MockActuatorHub, MockCameraHub
    from ..blockchain import NadFunClient
    from ..cultivation import calculate_vpd, get_stage_parameters, GrowthStage, check_parameters_in_range
    from ..ai import GrokVision, create_vision_analyzer
    from .auth import (
        Token, User, login_for_access_token, get_current_user_info,
        get_current_user, get_current_user_required, get_current_admin
    )
except ImportError:
    from db.connection import init_database, close_database, get_db_session
    from db.repository import GrowRepository
    from hardware import MockSensorHub, MockActuatorHub, MockCameraHub
    from blockchain import NadFunClient
    from cultivation import calculate_vpd, get_stage_parameters, GrowthStage, check_parameters_in_range
    from ai import GrokVision, create_vision_analyzer
    from api.auth import (
        Token, User, login_for_access_token, get_current_user_info,
        get_current_user, get_current_user_required, get_current_admin
    )

# Try to import real hardware modules
try:
    from hardware.govee import GoveeSensorHub
    GOVEE_AVAILABLE = True
except ImportError:
    try:
        from ..hardware.govee import GoveeSensorHub
        GOVEE_AVAILABLE = True
    except ImportError:
        GOVEE_AVAILABLE = False

try:
    from hardware.kasa import KasaActuatorHub
    KASA_AVAILABLE = True
except ImportError:
    try:
        from ..hardware.kasa import KasaActuatorHub
        KASA_AVAILABLE = True
    except ImportError:
        KASA_AVAILABLE = False


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    import os

    # Startup
    print("Starting Grok & Mon API...")
    await init_database()

    # Try to use real hardware, fall back to mock
    use_real_hardware = os.environ.get("USE_HARDWARE", "true").lower() == "true"

    # Initialize sensors (Govee or Mock)
    if use_real_hardware and GOVEE_AVAILABLE and os.environ.get("GOVEE_API_KEY"):
        try:
            app.state.sensors = GoveeSensorHub()
            if await app.state.sensors.connect():
                print("[OK] Govee sensor connected")
            else:
                print("[!] Govee failed, using mock sensors")
                app.state.sensors = MockSensorHub()
        except Exception as e:
            print(f"[!] Govee error: {e}, using mock sensors")
            app.state.sensors = MockSensorHub()
    else:
        print("[i] Using mock sensors")
        app.state.sensors = MockSensorHub()

    # Initialize actuators (Kasa or Mock)
    if use_real_hardware and KASA_AVAILABLE:
        kasa_ips = {}
        # Use semantic device names matching DeviceState fields and orchestrator
        enable_co2_solenoid = os.environ.get("ENABLE_CO2_SOLENOID", "true").strip().lower() == "true"
        _kasa_env_map = {
            "water_pump": "KASA_WATER_PUMP_IP",
            "exhaust_fan": "KASA_EXHAUST_FAN_IP",
            "circulation_fan": "KASA_CIRC_FAN_IP",
            "grow_light": "KASA_GROW_LIGHT_IP",
        }
        if enable_co2_solenoid:
            _kasa_env_map["co2_solenoid"] = "KASA_CO2_SOLENOID_IP"
        for name, env_var in _kasa_env_map.items():
            ip = os.environ.get(env_var)
            if ip:
                kasa_ips[name] = ip
        if kasa_ips:
            try:
                app.state.actuators = KasaActuatorHub(kasa_ips)
                if await app.state.actuators.connect():
                    print(f"[OK] Kasa plugs connected ({len(kasa_ips)} devices)")
                else:
                    print("[!] Kasa failed, using mock actuators")
                    app.state.actuators = MockActuatorHub()
            except Exception as e:
                print(f"[!] Kasa error: {e}, using mock actuators")
                app.state.actuators = MockActuatorHub()
        else:
            print("[i] No Kasa IPs configured, using mock actuators")
            app.state.actuators = MockActuatorHub()
    else:
        print("[i] Using mock actuators")
        app.state.actuators = MockActuatorHub()

    # Camera - use ContinuousWebcam for fast API responses
    # RETRY LOGIC: Orchestrator may have camera open briefly at startup (race condition)
    try:
        from hardware.webcam import ContinuousWebcam, get_logitech_index
        import time
        logitech_idx = get_logitech_index()

        camera_started = False
        for attempt in range(5):  # Try up to 5 times
            if attempt > 0:
                print(f"[*] Camera retry attempt {attempt + 1}/5 (waiting for orchestrator to release)...")
                time.sleep(2)  # Wait 2 seconds between retries

            app.state.camera = ContinuousWebcam(
                device_index=logitech_idx,
                frame_interval=0.5,  # Capture every 500ms
                night_mode=True,  # Enable faux night vision during dark periods
            )
            if app.state.camera.start():
                # Wait for first frame
                for _ in range(20):  # Wait up to 2 seconds
                    if app.state.camera.get_frame():
                        break
                    time.sleep(0.1)
                if app.state.camera.get_frame():
                    camera_started = True
                    print("[OK] ContinuousWebcam started (threaded frame grabber)")
                    break
                else:
                    print(f"[!] ContinuousWebcam started but no frames (attempt {attempt + 1})")
                    app.state.camera.stop()
            else:
                print(f"[!] ContinuousWebcam failed to start (attempt {attempt + 1})")

        if camera_started:
            # Start background task to sync camera mode with light schedule
            async def sync_camera_night_mode():
                """Periodically sync camera mode with light schedule (inverse)."""
                while True:
                    try:
                        # Check if lights are currently off
                        async with get_db_session() as session:
                            repo = GrowRepository(session)
                            stage_data = await repo.get_current_stage()
                            photoperiod = stage_data.get("photoperiod", "18/6") if stage_data else "18/6"

                            # Determine if currently in dark period
                            from datetime import datetime
                            now = datetime.now()
                            hour = now.hour

                            # Parse photoperiod (e.g., "18/6" means lights on at 6AM, off at midnight)
                            if "/" in photoperiod:
                                hours_on, hours_off = map(int, photoperiod.split("/"))
                                light_on_hour = 6  # 6 AM
                                light_off_hour = (light_on_hour + hours_on) % 24  # 6 + 18 = 24 = 0 (midnight)

                                # Check if current hour is in dark period
                                if light_off_hour > light_on_hour:
                                    # Normal case: e.g., 6 AM to midnight
                                    is_dark = hour < light_on_hour or hour >= light_off_hour
                                else:
                                    # Wrap case: e.g., midnight to 6 AM
                                    is_dark = hour >= light_off_hour and hour < light_on_hour

                                # Update camera mode (inverse of lights)
                                if hasattr(app.state.camera, 'set_dark_period'):
                                    app.state.camera.set_dark_period(is_dark)
                    except Exception as e:
                        print(f"[WARN] Camera night mode sync error: {e}")

                    await asyncio.sleep(60)  # Check every minute

            asyncio.create_task(sync_camera_night_mode())
            print("[OK] Camera night vision sync task started")
        else:
            print("[!] ContinuousWebcam failed after 5 attempts, using mock")
            app.state.camera = MockCameraHub()
    except Exception as e:
        print(f"[!] Webcam error: {e}, using mock")
        app.state.camera = MockCameraHub()

    # Second camera (IP camera - IP Webcam app, etc.)
    app.state.camera2 = None
    ip_camera_url = os.environ.get("IP_CAMERA_URL")
    if ip_camera_url:
        ip_camera_user = os.environ.get("IP_CAMERA_USER")
        ip_camera_pass = os.environ.get("IP_CAMERA_PASS")
        try:
            from hardware.webcam import IPCamera
            app.state.camera2 = IPCamera(
                snapshot_url=ip_camera_url,
                name="Cam 2",
                frame_interval=1.0,  # Capture every 1 second
                username=ip_camera_user,
                password=ip_camera_pass,
            )
            if app.state.camera2.start():
                auth_msg = " (with auth)" if ip_camera_user else ""
                print(f"[OK] IP Camera (Cam 2) started: {ip_camera_url}{auth_msg}")
            else:
                print(f"[!] IP Camera failed to connect to {ip_camera_url}")
                app.state.camera2 = None
        except Exception as e:
            print(f"[!] IP Camera error: {e}")
            app.state.camera2 = None
    else:
        print("[i] No IP_CAMERA_URL configured, second camera disabled")

    # Initialize Ecowitt soil sensors
    app.state.soil_sensors = None
    ecowitt_ip = os.environ.get("ECOWITT_GATEWAY_IP")
    if ecowitt_ip:
        try:
            from src.hardware.ecowitt import EcowittSoilHub
            app.state.soil_sensors = EcowittSoilHub(ecowitt_ip)
            healthy = await app.state.soil_sensors.health_check()
            if healthy:
                print(f"[OK] Ecowitt soil sensors connected ({ecowitt_ip})")
            else:
                print(f"[!] Ecowitt not responding at {ecowitt_ip}")
                app.state.soil_sensors = None
        except Exception as e:
            print(f"[!] Ecowitt error: {e}")
            app.state.soil_sensors = None

    # Link sensors to actuators if mock
    if hasattr(app.state.actuators, 'link_sensors'):
        app.state.actuators.link_sensors(app.state.sensors)

    # WebSocket connections
    app.state.ws_connections: List[WebSocket] = []

    # Blockchain client
    app.state.nadfun = NadFunClient()

    # Vision analyzer
    app.state.vision = create_vision_analyzer()

    # Initialize Tapo smart plugs (grow light control)
    # This runs in the FastAPI server process so the light scheduler has
    # direct hardware access — no dependency on the orchestrator.
    app.state.tapo_hub = None
    tapo_user = os.environ.get("TAPO_USERNAME")
    tapo_pass = os.environ.get("TAPO_PASSWORD")
    tapo_light_ip = os.environ.get("TAPO_GROW_LIGHT_IP")
    if tapo_user and tapo_pass and tapo_light_ip:
        try:
            from src.hardware.tapo import TapoActuatorHub
            app.state.tapo_hub = TapoActuatorHub()
            tapo_connected = await app.state.tapo_hub.connect()
            if tapo_connected:
                print(f"[OK] Tapo grow light connected ({tapo_light_ip})")
            else:
                print("[!] Tapo grow light failed to connect")
                app.state.tapo_hub = None
        except Exception as e:
            print(f"[!] Tapo error: {e}")
            app.state.tapo_hub = None
    else:
        print("[i] Tapo not configured (TAPO_USERNAME/PASSWORD/GROW_LIGHT_IP)")

    # Start the light scheduler (enforces photoperiod even without orchestrator)
    # CRITICAL FIX: Previously light automation only ran inside the orchestrator,
    # which is NOT started in "all" (OpenClaw) mode. This caused lights to stay
    # on past midnight when the service was running in default "all" mode.
    try:
        from src.scheduling.light_scheduler import light_scheduler_loop
        asyncio.create_task(light_scheduler_loop(app.state))
        print("[OK] Light scheduler active (photoperiod enforcement every 60s)")
    except Exception as e:
        print(f"[!] Light scheduler failed to start: {e}")

    # Persist live sensor/device snapshots to the DB. In OpenClaw-first mode we
    # do not run the legacy orchestrator loop, so without this the DB can go
    # stale (breaking history views, plant progress, and downstream automation).
    #
    # This loop is intentionally lightweight and non-LLM.
    try:
        persist_interval_s = int(os.getenv("DB_PERSIST_INTERVAL_SECONDS", "120"))
    except Exception:
        persist_interval_s = 120
    persist_interval_s = max(30, persist_interval_s)

    async def _persist_loop():
        from src.db.connection import get_db_session
        from src.db.repository import GrowRepository

        # Give hardware + DB a moment to settle.
        await asyncio.sleep(10)

        while True:
            try:
                # Read sensors from hardware.
                try:
                    reading = await app.state.sensors.read_all()
                    s = reading.to_dict()
                except Exception:
                    s = {}

                # Merge Ecowitt soil probes if available (best source of truth).
                if getattr(app.state, "soil_sensors", None):
                    try:
                        soil_data = await app.state.soil_sensors.read()
                        if soil_data and soil_data.sensors:
                            s["soil_moisture"] = soil_data.average_moisture
                            if len(soil_data.sensors) >= 1:
                                s["soil_moisture_probe1"] = soil_data.sensors[0].moisture_percent
                            if len(soil_data.sensors) >= 2:
                                s["soil_moisture_probe2"] = soil_data.sensors[1].moisture_percent
                    except Exception:
                        pass

                # Read actuator state (best-effort).
                try:
                    d_state = await app.state.actuators.get_state()
                    d = d_state.to_dict()
                except Exception:
                    d = {}

                air_temp = s.get("air_temp")
                humidity = s.get("humidity")
                vpd = s.get("vpd")
                soil = s.get("soil_moisture")
                co2 = s.get("co2")
                leaf_delta = s.get("leaf_temp_delta")

                # DB schema expects non-null core values; use safe fallbacks.
                if air_temp is None or humidity is None or vpd is None or soil is None:
                    await asyncio.sleep(persist_interval_s)
                    continue
                if co2 is None:
                    co2 = 0.0
                if leaf_delta is None:
                    leaf_delta = -2.0

                async with get_db_session() as session:
                    repo = GrowRepository(session)

                    # Sensor snapshot
                    await repo.add_sensor_reading(
                        air_temp=float(air_temp),
                        humidity=float(humidity),
                        vpd=float(vpd),
                        soil_moisture=float(soil),
                        co2=float(co2),
                        leaf_temp_delta=float(leaf_delta),
                        soil_moisture_probe1=s.get("soil_moisture_probe1"),
                        soil_moisture_probe2=s.get("soil_moisture_probe2"),
                        soil_temp=s.get("soil_temp"),
                        leaf_temp=s.get("leaf_temp"),
                        light_level=s.get("light_level"),
                        light_ppfd=s.get("light_ppfd"),
                        dew_point=s.get("dew_point"),
                    )

                    # Device snapshot (omit timestamp; DB sets it)
                    if d:
                        d.pop("timestamp", None)
                        # Derived from photoperiod; do not persist from hardware snapshots.
                        d.pop("is_dark_period", None)
                        await repo.update_device_state(**d)

                    await session.commit()
            except asyncio.CancelledError:
                break
            except Exception:
                # Never crash the API for background persistence.
                try:
                    await asyncio.sleep(persist_interval_s)
                except Exception:
                    pass

            await asyncio.sleep(persist_interval_s)

    try:
        app.state._db_persist_task = asyncio.create_task(_persist_loop())
        print(f"[OK] DB persistence loop active (interval={persist_interval_s}s)")
    except Exception as e:
        print(f"[!] DB persistence loop failed to start: {e}")

    print("API ready!")

    yield

    # Shutdown
    print("Shutting down...")

    # Stop ContinuousWebcam
    if hasattr(app.state.camera, 'stop'):
        app.state.camera.stop()

    # Stop IP Camera
    if app.state.camera2 and hasattr(app.state.camera2, 'stop'):
        app.state.camera2.stop()

    # Stop DB persistence loop
    persist_task = getattr(app.state, "_db_persist_task", None)
    if persist_task:
        try:
            persist_task.cancel()
        except Exception:
            pass

    if hasattr(app.state.sensors, 'disconnect'):
        await app.state.sensors.disconnect()
    await close_database()


# =============================================================================
# Application Factory
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Grok & Mon API",
        description="AI-powered cannabis cultivation monitoring",
        version="0.1.0",
        lifespan=lifespan,
    )

    # =======================================================================
    # Middleware Stack (SIMPLIFIED for Chromebook stability)
    # =======================================================================

    import os

    # 1. GZip compression (lightweight)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 2. CORS for frontend
    cors_origins = os.environ.get("CORS_ORIGINS", "https://grokandmon.com,http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # NOTE: Security middleware temporarily disabled for stability testing
    # Re-enable after identifying crash cause:
    # - TrustedHostMiddleware
    # - SecurityHeadersMiddleware
    # - RequestSizeLimitMiddleware

    # Mount static files (website)
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        well_known_dir = web_dir / ".well-known"
        if well_known_dir.exists():
            app.mount("/.well-known", StaticFiles(directory=well_known_dir), name="well-known")
        app.mount("/static", StaticFiles(directory=web_dir), name="static")

    # Mount assets directory for images
    assets_dir = web_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Mount music directory for MP3 files
    music_dir = web_dir / "music"
    if music_dir.exists():
        app.mount("/music", StaticFiles(directory=music_dir), name="music")

    # Register OBS overlay routes
    from .overlays import router as overlay_router
    app.include_router(overlay_router)

    # Register playlist routes
    from .playlist import router as playlist_router
    app.include_router(playlist_router)

    # Register admin routes (for remote management via Cloudflare Tunnel)
    from .admin import router as admin_router
    app.include_router(admin_router)

    # Register core health endpoints (/health, /ready)
    from src.core.health import health_router
    app.include_router(health_router)

    # Register A2A (Agent-to-Agent) protocol endpoint
    from .a2a import router as a2a_router
    app.include_router(a2a_router)

    # Register Grimoire learning API (OpenClaw skill integration)
    from .grimoire import router as grimoire_router
    app.include_router(grimoire_router)

    # Register Research / Pirate Intelligence API (OpenClaw skill integration)
    from .research import router as research_router
    app.include_router(research_router)

    # Register Operations Log API (ops log, hackathon timeline)
    from .ops import router as ops_router
    app.include_router(ops_router)

    # Register x402 Oracle paid endpoints
    try:
        from src.x402_hackathon.oracle.endpoints import router as x402_oracle_router
        app.include_router(x402_oracle_router)
    except ImportError:
        pass  # x402_hackathon not deployed yet

    # Serve art studio images
    @app.get("/api/art/image/{filename}")
    async def serve_art_image(filename: str):
        """Serve art pieces from data/art_studio/"""
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+\.(png|jpg|jpeg|gif|webp)$', filename):
            return Response(status_code=400, content="Invalid filename")
        art_dir = Path(__file__).parent.parent.parent / "data" / "art_studio"
        filepath = art_dir / filename
        if not filepath.exists():
            return Response(status_code=404, content="Art not found")
        suffix = filepath.suffix.lower()
        media = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
        return FileResponse(filepath, media_type=media.get(suffix[1:], "image/png"))

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI):
    """Register all API routes"""

    def _timestamp_is_stale(value: Optional[str], max_age_minutes: int) -> bool:
        """True when timestamp is missing/unparseable or older than threshold."""
        if max_age_minutes <= 0:
            return False
        parsed = _parse_iso_timestamp(value) if value else None
        if not parsed:
            return True
        if parsed.tzinfo:
            now = datetime.now(parsed.tzinfo)
        else:
            now = datetime.utcnow()
        return (now - parsed).total_seconds() > (max_age_minutes * 60)

    async def _read_live_sensors_dict() -> dict:
        """Read sensors directly from hardware and include soil probes when available."""
        try:
            reading = await app.state.sensors.read_all()
            result = reading.to_dict()
        except (ConnectionError, Exception) as e:
            logger.warning(f"Sensor read failed: {e}")
            # Return empty/default values instead of crashing
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "air_temp": None,
                "humidity": None,
                "vpd": None,
                "co2": None,
                "error": str(e)
            }

        # Merge Ecowitt soil moisture if available
        if app.state.soil_sensors:
            try:
                soil_data = await app.state.soil_sensors.read()
                if soil_data and soil_data.sensors:
                    result["soil_moisture"] = soil_data.average_moisture
                    if len(soil_data.sensors) >= 1:
                        result["soil_moisture_probe1"] = soil_data.sensors[0].moisture_percent
                    if len(soil_data.sensors) >= 2:
                        result["soil_moisture_probe2"] = soil_data.sensors[1].moisture_percent
            except Exception:
                pass  # Keep Govee values if Ecowitt fails

        return result

    # =========================================================================
    # Sensor Endpoints (mirrors SOLTOMATO)
    # =========================================================================

    @app.get("/api/sensors/latest")
    async def get_sensors_latest():
        """
        Get latest sensor readings.
        Matches SOLTOMATO's /api/sensors/latest endpoint.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            data = await repo.get_sensors_latest()
            max_age_min = int(os.getenv("SENSOR_LATEST_MAX_AGE_MINUTES", "30"))

            if data and _timestamp_is_stale(data.get("timestamp"), max_age_min):
                logger.warning(
                    "Sensors latest row is stale (>%s min); using live hardware fallback.",
                    max_age_min,
                )
                data = None

            if not data:
                # Generate from live hardware if no DB data (or stale row)
                return await _read_live_sensors_dict()

            return data

    @app.get("/api/sensors/history")
    async def get_sensors_history(hours: int = Query(default=24, ge=1, le=168)):
        """
        Get historical sensor data.
        Matches SOLTOMATO's /api/sensors/history?hours=N endpoint.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            return await repo.get_sensors_history(hours=hours)

    @app.get("/api/sensors/live")
    async def get_sensors_live():
        """
        Get live sensor reading directly from hardware.
        Bypasses database for real-time monitoring.
        Merges Govee temp/humidity/CO2 with Ecowitt soil moisture.
        """
        return await _read_live_sensors_dict()

    @app.get("/api/sensors")
    async def get_sensors():
        """
        Back-compat alias for older tooling that expects /api/sensors to return
        a JSON sensor snapshot.

        Historically some internal scripts and OpenClaw HEARTBEAT.md used this
        path. We map it to the live hardware read to keep behavior intuitive.
        """
        return await get_sensors_live()

    # =========================================================================
    # Device Endpoints (mirrors SOLTOMATO)
    # =========================================================================

    @app.get("/api/devices/latest")
    async def get_devices_latest():
        """
        Get current device states.
        Matches SOLTOMATO's /api/devices/latest endpoint.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            data = await repo.get_devices_latest()
            max_age_min = int(os.getenv("DEVICE_LATEST_MAX_AGE_MINUTES", "30"))

            if data and _timestamp_is_stale(data.get("timestamp"), max_age_min):
                logger.warning(
                    "Devices latest row is stale (>%s min); using live actuator state fallback.",
                    max_age_min,
                )
                data = None

            # `is_dark_period` must be derived from the photoperiod schedule, not
            # persisted hardware/DB state. Persisted values can be wrong when
            # running in OpenClaw-first mode (DB snapshot loop).
            #
            # Always compute is_dark_period if possible.
            try:
                stage_data = await repo.get_current_stage()
                photoperiod = stage_data.get("photoperiod", "18/6") if stage_data else "18/6"
                from src.scheduling.light_scheduler import should_light_be_on, DEFAULT_LIGHT_ON_HOUR
                expected_on = should_light_be_on(
                    now=datetime.now(),
                    light_on_hour=DEFAULT_LIGHT_ON_HOUR,
                    photoperiod=photoperiod,
                )
                computed_is_dark = not bool(expected_on)
            except Exception:
                computed_is_dark = None

            if not data:
                state = await app.state.actuators.get_state()
                if computed_is_dark is not None:
                    state.is_dark_period = computed_is_dark
                return state.to_dict()

            if computed_is_dark is not None:
                data["is_dark_period"] = computed_is_dark
            return data

    # =========================================================================
    # AI Output Endpoint (mirrors SOLTOMATO)
    # =========================================================================

    def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            # Handle trailing Z from ISO-8601 UTC strings.
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _format_sensor_wisdom(bullets: list, current_day: int = 1) -> str:
        """Transform raw heartbeat sensor bullets into Grok personality commentary.

        Instead of showing 'Temperature: 25.100000000000005°C' as raw data,
        generate natural language wisdom about the plant's conditions.
        """
        import re

        # Extract sensor values from bullet points
        sensors = {}
        for b in bullets:
            b_lower = b.lower()
            # Match patterns like "- Temperature: 25.1°C" or "- VPD: 0.64 kPa"
            num_match = re.search(r':\s*([\d.]+)', b)
            val = float(num_match.group(1)) if num_match else None

            if 'temperature' in b_lower or 'temp' in b_lower:
                sensors['temp'] = val
            elif 'humidity' in b_lower or 'rh' in b_lower:
                sensors['humidity'] = val
            elif 'vpd' in b_lower:
                sensors['vpd'] = val
            elif 'soil' in b_lower or 'moisture' in b_lower:
                sensors['soil'] = val
            elif 'co2' in b_lower:
                sensors['co2'] = val

        # Build Grok-style commentary
        parts = []

        # Temperature + humidity combo
        temp = sensors.get('temp')
        rh = sensors.get('humidity')
        if temp is not None and rh is not None:
            temp_f = temp * 9 / 5 + 32
            if 22 <= temp <= 28 and 55 <= rh <= 75:
                parts.append(f"Mon chillin' at {temp:.1f}°C ({temp_f:.0f}°F) with {rh:.0f}% humidity — right in the sweet spot.")
            elif temp > 28:
                parts.append(f"Mon runnin' hot at {temp:.1f}°C ({temp_f:.0f}°F), {rh:.0f}% RH — might want to check ventilation.")
            elif temp < 20:
                parts.append(f"Mon feelin' cold at {temp:.1f}°C ({temp_f:.0f}°F), {rh:.0f}% RH — keep her warm, fam.")
            else:
                parts.append(f"Mon vibin' at {temp:.1f}°C ({temp_f:.0f}°F) with {rh:.0f}% humidity.")

        # VPD assessment
        vpd = sensors.get('vpd')
        if vpd is not None:
            if 0.4 <= vpd <= 0.8:
                parts.append(f"VPD at {vpd:.2f} kPa — perfect transpiration zone.")
            elif vpd < 0.4:
                parts.append(f"VPD low at {vpd:.2f} kPa — watch for mold risk, increase airflow.")
            elif vpd > 1.2:
                parts.append(f"VPD high at {vpd:.2f} kPa — she might be stressed, raise humidity or lower temp.")
            else:
                parts.append(f"VPD at {vpd:.2f} kPa — acceptable range.")

        # Soil moisture
        soil = sensors.get('soil')
        if soil is not None:
            if soil < 25:
                parts.append(f"Soil moisture at {soil:.0f}% — time for a drink soon.")
            elif soil > 70:
                parts.append(f"Soil moisture at {soil:.0f}% — well watered, let her dry back a bit.")
            else:
                parts.append(f"Soil moisture sitting at {soil:.0f}%.")

        # CO2
        co2 = sensors.get('co2')
        if co2 is not None:
            if co2 == 0:
                parts.append("CO2 sensor offline.")
            elif co2 > 800:
                parts.append(f"CO2 at {co2:.0f} ppm — boosted levels, she's eating good.")
            else:
                parts.append(f"CO2 at {co2:.0f} ppm.")

        if not parts:
            return "Grok is monitoring Mon's environment..."

        return "\n\n".join(parts)

    def _format_autopilot_wisdom(raw_output: str, current_day: int = 1, current_stage: str = "vegetative") -> Optional[str]:
        """Convert autopilot watering logs into user-facing patois guidance."""
        import re

        if not raw_output or "AUTOPILOT (gentle_daily_watering)" not in raw_output:
            return None

        fields: Dict[str, str] = {}
        for line in raw_output.splitlines():
            line = line.strip()
            if not line.startswith("- "):
                continue
            # Expected format: "- key: value"
            m = re.match(r"-\s*([a-zA-Z0-9_]+)\s*:\s*(.+)$", line)
            if m:
                fields[m.group(1).strip().lower()] = m.group(2).strip()

        # Use the CURRENT stage from the DB, not the stale stage stored in the log
        stage = current_stage
        soil_raw = fields.get("soil_before")
        planned_raw = fields.get("planned_ml")
        backend = fields.get("backend", "pump")
        ts_utc = fields.get("ts_utc")
        success_raw = fields.get("success", "false").strip().lower()
        success = success_raw in {"1", "true", "yes"}

        soil_text = "unknown"
        try:
            soil_text = f"{float(soil_raw):.0f}%"
        except Exception:
            if soil_raw:
                soil_text = soil_raw

        planned_text = "0ml"
        planned_ml: Optional[int] = None
        try:
            planned_ml = int(float(planned_raw))
            planned_text = f"{planned_ml}ml"
        except Exception:
            if planned_raw:
                planned_text = planned_raw

        timing_line = ""
        if ts_utc:
            timing_line = f"\n\nLast autopilot watering check logged at {ts_utc}."

        if success and (planned_ml is None or planned_ml > 0):
            return (
                f"Day {current_day} {stage} vibes: I and I gave Mon a gentle {planned_text} top-up through {backend}. "
                f"Soil was reading around {soil_text}, so di move was to hydrate softly and avoid overdoing it."
                f"\n\nNext move: let di root zone breathe and re-check before any next pour. "
                f"Soil probe is supplemental; schedule and cooldown still run di show."
                f"{timing_line}"
            )

        if success:
            return (
                f"Day {current_day} {stage} check complete. Automation ran clean through {backend}, "
                f"and no extra water was pushed."
                f"\n\nNext move: keep monitoring soil trend and only top up when schedule + thresholds align."
                f"{timing_line}"
            )

        return (
            f"Day {current_day} {stage} check flagged caution. Soil showed about {soil_text}, "
            f"but autopilot did not complete a watering action."
            f"\n\nNext move: inspect pump/backend health and re-run gentle watering path safely."
            f"{timing_line}"
        )

    def _latest_openclaw_memory_snapshot(default_day: int = 1) -> Optional[Dict[str, Any]]:
        """
        Read the newest OpenClaw markdown memory entry and present it in /api/ai/latest format.
        This keeps the endpoint fresh when OpenClaw is the active orchestrator.
        """
        import re
        from src.core.paths import OPENCLAW_MEMORY

        if not OPENCLAW_MEMORY.exists():
            return None

        date_file_re = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
        section_re = re.compile(r"^##\s*(\d{2}:\d{2})\s*[-\u2013\u2014]\s*(.+?)\s*$", re.MULTILINE)
        # Grow-relevant keywords — these entries belong on the website
        grow_title_re = re.compile(
            r"(sensor|plant|grow|decision|heartbeat|monitor|temp|humid|vpd|water|light|photoperiod|environment|health|calibrat|actuator|pump|fan|exhaust|deficien|nutrient|soil|co2)",
            re.IGNORECASE,
        )
        # Non-grow keywords — these should NOT appear in Grok's Wisdom
        non_grow_title_re = re.compile(
            r"(self.?improv|upgrade|social|post|tweet|research|trade|trading|pirate|intel|moltbook|clawk|farcaster|telegram|email|a2a|reputation|8004|bridge|ntt|token|swap)",
            re.IGNORECASE,
        )
        rich_title_re = re.compile(
            r"(decision|improvement|review|action|research|upgrade|post|trade|alert|mission)",
            re.IGNORECASE,
        )

        files = sorted(
            [p for p in OPENCLAW_MEMORY.glob("*.md") if date_file_re.match(p.name)],
            reverse=True,
        )
        now = datetime.utcnow()
        lookback_hours = 72  # keep context recent while allowing richer non-mirror entries
        candidates: List[Tuple[float, datetime, Dict[str, Any]]] = []
        fallback_snapshot: Optional[Dict[str, Any]] = None
        for mem_file in files:
            try:
                text = mem_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            matches = list(section_re.finditer(text))
            if not matches:
                continue

            # Walk backward through sections and rank richer entries above heartbeat mirrors.
            for idx in range(len(matches) - 1, -1, -1):
                match = matches[idx]
                body_start = match.end()
                body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
                body = text[body_start:body_end].strip()

                date_str = mem_file.stem
                time_str = match.group(1)
                section_title = match.group(2).strip()

                try:
                    ts = datetime.fromisoformat(f"{date_str}T{time_str}:00")
                except Exception:
                    ts = datetime.utcnow()

                age_h = (now - ts).total_seconds() / 3600.0
                if age_h > lookback_hours:
                    continue

                bullets = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("- ")]
                is_mirror_entry = "heartbeat (mirror)" in section_title.lower()

                if bullets and is_mirror_entry:
                    # Transform raw sensor mirrors into Grok personality commentary
                    output_text = _format_sensor_wisdom(bullets, default_day)
                elif bullets:
                    lines = [f"OpenClaw {section_title}", "", "Latest notes:"]
                    lines.extend([f"  {ln}" for ln in bullets[:6]])
                    output_text = "\n".join(lines)
                else:
                    fallback_text = body.strip()
                    if len(fallback_text) > 900:
                        fallback_text = fallback_text[:900] + "..."
                    output_text = (
                        f"OpenClaw {section_title}\n\n{fallback_text}"
                        if fallback_text
                        else f"OpenClaw {section_title}\n\nNo structured notes captured yet."
                    )

                snapshot = {
                    "timestamp": ts.isoformat(),
                    "output_text": output_text,
                    "mon_day": default_day,
                }
                has_non_error_bullet = any(not b.lower().startswith("- error:") for b in bullets)
                title_l = section_title.lower()
                is_mirror = "heartbeat (mirror)" in title_l
                non_error_bullets = [b for b in bullets if not b.lower().startswith("- error:")]

                score = 0.0
                score += 30.0 if not is_mirror else 0.0
                score += 20.0 if rich_title_re.search(section_title) else 0.0
                score += min(len(non_error_bullets), 6) * 2.0
                score += min(len(body) / 220.0, 8.0)
                # CRITICAL: Grow-relevance filtering for Grok's Wisdom
                # Self-improvement, social, research, trading entries should NOT
                # appear on the public website — only grow-related decisions.
                if non_grow_title_re.search(section_title):
                    score -= 100.0  # Effectively exclude non-grow entries
                if grow_title_re.search(section_title):
                    score += 40.0  # Strongly prefer grow-related entries
                # Also check body for grow keywords (some entries have generic titles)
                body_lower = body.lower()
                if any(kw in body_lower for kw in ["upgrade_request_json", "self-improvement", "social post", "trading signal", "pirate intel"]):
                    score -= 80.0  # Penalize non-grow body content
                if any(kw in body_lower for kw in ["temperature", "humidity", "vpd", "sensor", "grow light", "watering", "photoperiod", "plant health"]):
                    score += 20.0  # Boost grow-related body content
                score -= 12.0 if bullets and not non_error_bullets else 0.0
                score -= min(age_h, 24.0) * 0.2  # slight freshness preference

                if has_non_error_bullet or not bullets:
                    candidates.append((score, ts, snapshot))
                if fallback_snapshot is None and is_mirror:
                    fallback_snapshot = snapshot

        if candidates:
            # Prefer higher quality first, then more recent.
            candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
            return candidates[0][2]
        return fallback_snapshot

    @app.get("/api/ai/latest")
    async def get_ai_latest():
        """
        Get latest AI decision/output.
        Matches SOLTOMATO's /api/ai/latest endpoint.

        Returns the irie vibes commentary (not technical JSON).
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            stage = await repo.get_current_stage()
            current_day = stage.get("current_day", 1) if stage else 1
            data = await repo.get_ai_latest()
            openclaw_data = _latest_openclaw_memory_snapshot(default_day=current_day)

            # Prefer OpenClaw memory when it is newer than the legacy AI table.
            if openclaw_data:
                db_ts = _parse_iso_timestamp(data.get("timestamp")) if data else None
                oc_ts = _parse_iso_timestamp(openclaw_data.get("timestamp"))
                if oc_ts and (not db_ts or oc_ts > db_ts):
                    return openclaw_data

            if not data:
                # Return placeholder if no AI decisions yet
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "output_text": "Grok is analyzing Mon's environment...\n\nAwaiting first decision cycle.",
                    "mon_day": current_day,
                }

            # Extract user-friendly output from JSON if present
            output_text = data.get("output_text", "")
            data["mon_day"] = current_day

            # Handle autopilot watering logs with user-facing patois guidance.
            growth_stage = stage.get("current_stage", "vegetative") if stage else "vegetative"
            autopilot_wisdom = _format_autopilot_wisdom(output_text, current_day=current_day, current_stage=growth_stage)
            if autopilot_wisdom:
                data["output_text"] = autopilot_wisdom
                return data

            import re

            # Try to extract individual fields using regex (handles malformed JSON)
            commentary_match = re.search(r'"commentary"\s*:\s*"([^"]*)"', output_text)
            health_match = re.search(r'"overall_health"\s*:\s*"([^"]*)"', output_text)
            social_match = re.search(r'"social_post"\s*:\s*"([^"]*)"', output_text)

            # Extract observations array
            observations = []
            obs_match = re.search(r'"observations"\s*:\s*\[(.*?)\]', output_text, re.DOTALL)
            if obs_match:
                obs_items = re.findall(r'"([^"]+)"', obs_match.group(1))
                observations = obs_items[:3]

            # Extract concerns array
            concerns = []
            concerns_match = re.search(r'"concerns"\s*:\s*\[(.*?)\]', output_text, re.DOTALL)
            if concerns_match:
                concern_items = re.findall(r'"([^"]+)"', concerns_match.group(1))
                concerns = concern_items[:2]

            # Extract recommendations array
            recommendations = []
            rec_match = re.search(r'"recommendations"\s*:\s*\[(.*?)\]', output_text, re.DOTALL)
            if rec_match:
                rec_items = re.findall(r'"([^"]+)"', rec_match.group(1))
                recommendations = rec_items[:2]

            # Build friendly output
            lines = []
            if commentary_match:
                lines.append(commentary_match.group(1))
            if health_match:
                lines.append(f"\nPlant Health: {health_match.group(1)}")
            if observations:
                lines.append("\nObservations:")
                for obs in observations:
                    lines.append(f"  - {obs}")
            if concerns:
                lines.append("\nHeads up:")
                for concern in concerns:
                    lines.append(f"  - {concern}")
            if recommendations:
                lines.append("\nNext steps:")
                for rec in recommendations:
                    lines.append(f"  - {rec}")
            if social_match:
                lines.append(f"\n{social_match.group(1)}")

            # Append tool results if present (the ✓ and ✗ lines)
            tool_results = re.findall(r'[✓✗][^\n]+', output_text)
            if tool_results:
                lines.append("\n\nActions taken:")
                for result in tool_results[:5]:
                    lines.append(f"  {result}")

            if lines:
                data["output_text"] = "\n".join(lines)
            else:
                # Fallback: strip JSON/code blocks but keep readable text
                cleaned = re.sub(r'```(?:json)?\s*', '', output_text)
                cleaned = re.sub(r'\{[^}]*\}', '', cleaned)
                cleaned = re.sub(r'\[THINK\].*?\[/THINK\]', '', cleaned, flags=re.DOTALL)
                data["output_text"] = cleaned.strip() if cleaned.strip() else "Grok is monitoring Mon..."

            return data

    @app.get("/api/ai/history")
    async def get_ai_history(limit: int = Query(default=20, ge=1, le=100)):
        """
        Get historical AI decisions.
        Returns list of past AI outputs for the history panel.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            data = await repo.get_ai_history(limit=limit)
            return data

    @app.post("/api/ai/trigger")
    async def trigger_ai_decision(current_user: User = Depends(get_current_admin)):
        """
        Manually trigger an AI decision cycle (admin only).
        Useful for testing or forcing immediate analysis.
        """
        from hardware import USBWebcam, get_logitech_index, MockActuatorHub, MockCameraHub
        from ai import GrokBrain, ToolExecutor
        from safety import SafetyGuardian, SafeActuatorHub

        async with get_db_session() as session:
            repo = GrowRepository(session)

            # Get current state
            sensors = await repo.get_sensors_latest()
            devices = await repo.get_devices_latest()
            stage = await repo.get_current_stage()

            if not sensors:
                return {"error": "No sensor data available", "success": False}

            current_day = stage.get("current_day", 1) if stage else 1
            growth_stage = stage.get("current_stage", "seedling") if stage else "seedling"
            photoperiod = stage.get("photoperiod", "18/6") if stage else "18/6"

            # Setup camera
            try:
                cam_idx = get_logitech_index()
                camera = USBWebcam(device_index=cam_idx)
            except Exception:
                camera = MockCameraHub()

            # Setup actuators and safety
            actuators = MockActuatorHub()
            guardian = SafetyGuardian()
            safe_actuators = SafeActuatorHub(actuators, guardian)

            # Create tool executor and brain
            tool_exec = ToolExecutor(safe_actuators, camera, repo)
            brain = GrokBrain(tool_executor=tool_exec, plant_name="Mon")

            # Run decision
            result = await brain.decide(
                sensors=sensors,
                devices=devices or {},
                current_day=current_day,
                growth_stage=growth_stage,
                photoperiod=photoperiod,
                is_dark_period=False,
                water_today_ml=0
            )

            # Save to database
            await repo.log_ai_decision(
                grow_day=current_day,
                output_text=result.output_text,
                actions_taken=result.actions_taken,
                tokens_used=result.tokens_used
            )

            return {
                "success": True,
                "output_text": result.output_text,
                "actions": result.actions_taken,
                "tokens": result.tokens_used
            }

    # =========================================================================
    # Interactive Agent Query (agentic brain with full tool access)
    # =========================================================================

    @app.post("/api/ai/ask")
    async def ask_agent(request: Request):
        """
        Ask the agentic brain a question with full tool access.

        The agent can read sensors, check history, query memory,
        and even take actions in response.

        Body JSON:
            query: str (required) — the question to ask
            context: str (optional) — additional context
            api_key: str (optional) — API key for auth (alternative to admin token)

        Returns:
            output_text, actions_taken, tool_rounds, total_tool_calls, tokens_used
        """
        import os

        body = await request.json()
        query_text = body.get("query", "").strip()
        user_context = body.get("context", "")
        provided_key = body.get("api_key", "")

        if not query_text:
            return {"error": "query is required", "success": False}

        # Auth: accept either admin token or a matching API key
        auth_ok = False

        # Check Authorization header for admin token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Try admin token validation
                from .auth import decode_token
                token = auth_header[7:]
                payload = decode_token(token)
                if payload and payload.get("role") == "admin":
                    auth_ok = True
            except Exception:
                pass

        # Check API key in body
        if not auth_ok and provided_key:
            expected = os.environ.get("AGENT_API_KEY", "")
            if expected and provided_key == expected:
                auth_ok = True

        # Fallback: allow if XAI_API_KEY is set (self-hosted, local access)
        if not auth_ok:
            # Check if request is from localhost
            client_host = request.client.host if request.client else ""
            if client_host in ("127.0.0.1", "localhost", "::1"):
                auth_ok = True

        if not auth_ok:
            return {"error": "Unauthorized. Provide admin token or api_key.", "success": False}

        try:
            # Create a standalone brain for this request
            from src.ai import GrokBrain, ToolExecutor

            api_key = os.environ.get("XAI_API_KEY", "")
            if not api_key:
                return {"error": "XAI_API_KEY not configured", "success": False}

            brain = GrokBrain(api_key=api_key, plant_name="Mon")

            # Create tool executor with DB access
            async with get_db_session() as session:
                repo = GrowRepository(session)
                executor = ToolExecutor(None, None, repo)
                brain.tool_executor = executor

                # Get current grow state
                stage_data = await repo.get_current_stage()
                growth_stage = stage_data.get("current_stage", "vegetative") if stage_data else "vegetative"
                current_day = stage_data.get("current_day", 1) if stage_data else 1

                # Add sensor context
                sensors = await repo.get_sensors_latest()
                context_parts = []
                if user_context:
                    context_parts.append(user_context)
                if sensors:
                    context_parts.append(
                        f"Current sensors: temp={sensors.get('air_temp')}°C, "
                        f"RH={sensors.get('humidity')}%, VPD={sensors.get('vpd')} kPa, "
                        f"CO2={sensors.get('co2')} ppm, soil={sensors.get('soil_moisture')}%"
                    )
                combined_context = "\n".join(context_parts) if context_parts else None

                result = await brain.interactive_query(
                    query=query_text,
                    context=combined_context,
                    growth_stage=growth_stage,
                    current_day=current_day,
                )

                return {
                    "success": True,
                    "output_text": result.output_text,
                    "actions_taken": result.actions_taken or [],
                    "tool_rounds": result.tool_rounds,
                    "total_tool_calls": result.total_tool_calls,
                    "tokens_used": result.tokens_used,
                    "trigger": result.trigger,
                }
        except Exception as e:
            logger.error(f"AI ask endpoint failed: {e}", exc_info=True)
            return {"error": str(e), "success": False}

    # =========================================================================
    # Growth Stage Endpoint (Cannabis-specific)
    # =========================================================================

    @app.get("/api/grow/stage")
    async def get_grow_stage():
        """
        Get current growth stage info.
        Cannabis-specific endpoint.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            data = await repo.get_current_stage()

            if not data:
                data = {
                    "current_stage": "seedling",
                    "current_day": 1,
                    "photoperiod": "18/6",
                    "total_water_ml": 0,
                }

            # Calculate is_dark_period based on photoperiod (shared logic with
            # light scheduler to avoid drift/bugs).
            try:
                photoperiod = data.get("photoperiod", "18/6")
                from src.scheduling.light_scheduler import should_light_be_on, DEFAULT_LIGHT_ON_HOUR
                expected_on = should_light_be_on(
                    now=datetime.now(),
                    light_on_hour=DEFAULT_LIGHT_ON_HOUR,
                    photoperiod=photoperiod,
                )
                data["is_dark_period"] = not bool(expected_on)
            except Exception:
                data["is_dark_period"] = False
            return data

    @app.get("/api/grow/strain")
    async def get_strain_info():
        """Get strain information"""
        async with get_db_session() as session:
            repo = GrowRepository(session)
            grow_session = await repo.get_active_session()

            if not grow_session:
                return {
                    "strain_name": "TBD",
                    "strain_type": "Unknown",
                    "flower_time": "8-10 weeks",
                    "difficulty": "Beginner",
                }

            return {
                "strain_name": grow_session.strain_name or "TBD",
                "strain_type": grow_session.strain_type or "Hybrid",
                "flower_time": "8-10 weeks",
                "difficulty": "Beginner",
            }

    # =========================================================================
    # Webcam Endpoint (mirrors SOLTOMATO)
    # =========================================================================

    @app.get("/api/webcam/og-image")
    async def get_webcam_og_image():
        """
        Get webcam image for OpenGraph/social sharing.
        Uses ContinuousWebcam's buffer for instant response.
        """
        try:
            image_data = await app.state.camera.capture()
            return Response(
                content=image_data,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=60"}
            )
        except Exception as e:
            logger.error(f"OG image capture failed: {e}")
            return Response(content=b"", status_code=503)

    @app.get("/api/webcam/latest")
    async def get_webcam_latest():
        """Get latest webcam image - instant response from ContinuousWebcam buffer"""
        try:
            # ContinuousWebcam.capture() returns instantly from buffer
            image_data = await app.state.camera.capture()
            frame_age = None
            if hasattr(app.state.camera, 'get_frame_age'):
                frame_age = app.state.camera.get_frame_age()

            headers = {
                "Cache-Control": "public, max-age=1",
                "X-Cache": "HIT"  # Always "HIT" since we use continuous buffer
            }
            if frame_age is not None:
                headers["X-Frame-Age"] = f"{frame_age:.1f}s"

            return Response(
                content=image_data,
                media_type="image/jpeg",
                headers=headers
            )
        except ConnectionError as e:
            logger.warning(f"Webcam not ready: {e}")
            return Response(
                content=b"",
                status_code=503,
                headers={"Retry-After": "2"}
            )
        except Exception as e:
            logger.error(f"Webcam capture failed: {e}")
            return Response(
                content=b"",
                status_code=503,
                headers={"Retry-After": "5"}
            )

    @app.get("/api/webcam/analysis")
    async def get_webcam_analysis():
        """Get latest webcam image enhanced for plant health analysis.

        Returns a white-balance-corrected, contrast-normalized, sharpened
        version of the current frame — optimized for the vision AI to
        detect yellowing, spots, curling, and other plant health issues
        under grow-light conditions.
        """
        try:
            if hasattr(app.state.camera, "get_analysis_frame"):
                analysis_frame = app.state.camera.get_analysis_frame()
                if analysis_frame:
                    return Response(
                        content=analysis_frame,
                        media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=1",
                                 "X-Enhancement": "grow-light-corrected"},
                    )
            return Response(content=b"", status_code=503,
                            headers={"X-Error": "Analysis frame not available"})
        except Exception as e:
            logger.error(f"Analysis frame failed: {e}")
            return Response(content=b"", status_code=503)

    # =========================================================================
    # Second Camera (IP Camera - Alfred, IP Webcam, etc.)
    # =========================================================================

    @app.get("/api/webcam/2/latest")
    async def get_webcam2_latest():
        """Get latest image from second camera (IP camera / Alfred)"""
        if not app.state.camera2:
            return Response(
                content=b"",
                status_code=503,
                headers={"X-Error": "Second camera not configured. Set IP_CAMERA_URL env var."}
            )

        try:
            image_data = await app.state.camera2.capture()
            frame_age = None
            if hasattr(app.state.camera2, 'get_frame_age'):
                frame_age = app.state.camera2.get_frame_age()

            headers = {
                "Cache-Control": "public, max-age=1",
                "X-Camera": app.state.camera2.name if hasattr(app.state.camera2, 'name') else "Camera 2"
            }
            if frame_age is not None:
                headers["X-Frame-Age"] = f"{frame_age:.1f}s"

            error = app.state.camera2.get_error() if hasattr(app.state.camera2, 'get_error') else None
            if error:
                headers["X-Last-Error"] = error

            return Response(
                content=image_data,
                media_type="image/jpeg",
                headers=headers
            )
        except ConnectionError as e:
            logger.warning(f"Camera 2 not ready: {e}")
            return Response(
                content=b"",
                status_code=503,
                headers={"Retry-After": "2", "X-Error": str(e)}
            )
        except Exception as e:
            logger.error(f"Camera 2 capture failed: {e}")
            return Response(
                content=b"",
                status_code=503,
                headers={"Retry-After": "5", "X-Error": str(e)}
            )

    @app.get("/api/webcam/2/status")
    async def get_webcam2_status():
        """Get status of second camera"""
        if not app.state.camera2:
            return {
                "configured": False,
                "message": "Set IP_CAMERA_URL environment variable to enable second camera"
            }

        connected = await app.state.camera2.is_connected() if hasattr(app.state.camera2, 'is_connected') else False
        frame_age = app.state.camera2.get_frame_age() if hasattr(app.state.camera2, 'get_frame_age') else None
        error = app.state.camera2.get_error() if hasattr(app.state.camera2, 'get_error') else None

        return {
            "configured": True,
            "connected": connected,
            "name": app.state.camera2.name if hasattr(app.state.camera2, 'name') else "Camera 2",
            "url": app.state.camera2.snapshot_url if hasattr(app.state.camera2, 'snapshot_url') else None,
            "frame_age_seconds": frame_age,
            "last_error": error
        }

    @app.post("/api/webcam/2/configure")
    async def configure_webcam2(url: str = None, username: str = None, password: str = None):
        """
        Configure or reconfigure the second camera URL.
        Useful for changing IP Webcam camera's address dynamically.

        Query params:
            url - The snapshot URL (e.g., http://192.168.1.100:8080/shot.jpg)
            username - Optional username for digest auth
            password - Optional password for digest auth
        """
        if not url:
            return {"error": "url parameter required"}

        # Stop existing camera if running
        if app.state.camera2 and hasattr(app.state.camera2, 'stop'):
            app.state.camera2.stop()
            app.state.camera2 = None

        try:
            from hardware.webcam import IPCamera
            app.state.camera2 = IPCamera(
                snapshot_url=url,
                name="IP Webcam",
                frame_interval=1.0,
                username=username,
                password=password,
            )
            if app.state.camera2.start():
                auth_msg = " (with auth)" if username else ""
                logger.info(f"Camera 2 configured: {url}{auth_msg}")
                return {"success": True, "url": url, "message": f"Second camera connected{auth_msg}"}
            else:
                error = app.state.camera2.get_error() if hasattr(app.state.camera2, 'get_error') else "Unknown error"
                app.state.camera2 = None
                return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Camera 2 configuration failed: {e}")
            app.state.camera2 = None
            return {"success": False, "error": str(e)}

    @app.get("/api/webcam/2/stream")
    async def get_webcam2_stream():
        """Live MJPEG video stream from second camera"""
        if not app.state.camera2:
            return Response(
                content=b"Camera 2 not configured",
                status_code=503
            )

        async def generate_frames():
            while True:
                try:
                    image_data = await app.state.camera2.capture()
                    yield b"--frame\r\n"
                    yield b"Content-Type: image/jpeg\r\n\r\n"
                    yield image_data
                    yield b"\r\n"
                except Exception as e:
                    logger.warning(f"Camera 2 stream error: {e}")
                    await asyncio.sleep(1)
                    continue
                await asyncio.sleep(0.5)  # 2 FPS

        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    @app.get("/api/meters/visual-read")
    async def read_meters_visually():
        """
        Capture image and use Grok vision to read pH/moisture meters.
        Call this endpoint when you've pressed the meter button and display is active.
        Position meters in camera view for best results.
        """
        import base64
        import os
        import httpx

        # Capture current image
        image_data = await app.state.camera.capture()
        b64_image = base64.b64encode(image_data).decode('utf-8')

        # Use Grok vision to read the meters
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            return {"error": "XAI_API_KEY not configured"}

        prompt = """Look at this image from a cannabis grow setup.

Find and read any visible meters/displays showing:
1. pH value (usually 0-14 scale)
2. Soil moisture (usually 0-10 or percentage)
3. Any other readings visible

For each reading found, report:
- Type of reading (pH, moisture, etc.)
- The numeric value shown
- Confidence level (high/medium/low)

If no meters are visible or displays are off, say so.

Respond in JSON format:
{
  "readings": [
    {"type": "pH", "value": 6.5, "confidence": "high"},
    {"type": "soil_moisture", "value": 7, "confidence": "medium"}
  ],
  "notes": "any relevant observations"
}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-vision-1212",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                                ]
                            }
                        ],
                        "max_tokens": 500
                    }
                )
                result = response.json()
                reading_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "raw_response": reading_text,
                    "image_captured": True
                }
        except Exception as e:
            return {"error": str(e), "image_captured": True}

    @app.get("/api/webcam/stream")
    async def get_webcam_stream():
        """
        Live MJPEG video stream.
        Use this endpoint for real-time camera viewing.
        """
        async def generate_frames():
            while True:
                try:
                    image_data = await app.state.camera.capture()
                    # MJPEG frame format
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        image_data +
                        b"\r\n"
                    )
                    # ~15 fps
                    await asyncio.sleep(0.067)
                except Exception as e:
                    print(f"Stream error: {e}")
                    break

        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    # =========================================================================
    # Aggregates Endpoint
    # =========================================================================

    @app.get("/api/aggregates/daily")
    async def get_daily_aggregates(day: Optional[int] = None):
        """Get daily statistics (watering totals, etc.)"""
        async with get_db_session() as session:
            repo = GrowRepository(session)

            if day is None:
                stage = await repo.get_current_stage()
                day = stage.get("current_day", 1) if stage else 1

            return await repo.get_daily_stats(grow_day=day)

    # =========================================================================
    # Health Check
    # =========================================================================

    @app.get("/api/health")
    async def api_health_check():
        """API health check — hardware-level status (complements /health for system-level)."""
        sensors_ok = await app.state.sensors.is_connected()
        actuators_ok = await app.state.actuators.is_connected()

        camera_is_mock = type(app.state.camera).__name__ == "MockCameraHub"
        camera_ok = not camera_is_mock  # Real webcam verified at startup

        # Include core health info for a single-endpoint view
        from src.core.watchdog import get_watchdog
        wd = get_watchdog()
        stale = wd.get_stale()
        has_components = len(wd.get_status()) > 0

        # In OpenClaw mode the legacy orchestrator/social components are not started,
        # so the watchdog may have no registered components. Treat the OpenClaw gateway
        # as a first-class readiness signal so /api/health stays meaningful in production.
        openclaw_ok = False
        try:
            # IMPORTANT: A plain TCP connect can succeed while the gateway is wedged
            # (e.g., stuck in a long cron run). Require a real HTTP response.
            import os
            import time as _time
            import urllib.request

            timeout_s = float(os.getenv("OPENCLAW_HEALTH_TIMEOUT_SECONDS", "2.5"))
            retries = max(1, int(os.getenv("OPENCLAW_HEALTH_PROBE_RETRIES", "1")))
            for attempt in range(retries):
                try:
                    req = urllib.request.Request(
                        "http://127.0.0.1:18789/__openclaw__/canvas/",
                        method="GET",
                    )
                    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                        _ = resp.read(1)
                        if int(getattr(resp, "status", 200)) == 200:
                            openclaw_ok = True
                            break
                except Exception:
                    if attempt + 1 < retries:
                        _time.sleep(0.35)
        except Exception:
            openclaw_ok = False

        ready = (has_components and len(stale) == 0) if has_components else (
            sensors_ok and actuators_ok and camera_ok and openclaw_ok
        )

        return {
            "status": "healthy" if (sensors_ok and actuators_ok and camera_ok) else "degraded",
            "ready": ready,
            "sensors": "connected" if sensors_ok else "disconnected",
            "actuators": "connected" if actuators_ok else "disconnected",
            "camera": "connected" if camera_ok else "disconnected (using mock)",
            "openclaw": "connected" if openclaw_ok else "disconnected",
            "stale_components": stale,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.get("/api/debug")
    async def debug_status():
        """
        Debug endpoint to diagnose database and service issues.
        Returns detailed error information for troubleshooting.
        """
        import traceback
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {"status": "unknown"},
            "active_session": {"status": "unknown"},
            "ai_latest": {"status": "unknown"},
            "sensors_latest": {"status": "unknown"},
        }
        
        # Test database connection
        try:
            async with get_db_session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                result["database"] = {"status": "ok"}
        except Exception as e:
            result["database"] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
        
        # Test active session query
        try:
            async with get_db_session() as session:
                repo = GrowRepository(session)
                active = await repo.get_active_session()
                if active:
                    result["active_session"] = {"status": "ok", "id": active.id, "name": active.name, "day": active.current_day}
                else:
                    result["active_session"] = {"status": "no_session", "message": "No active grow session found"}
        except Exception as e:
            result["active_session"] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
        
        # Test AI latest query
        try:
            async with get_db_session() as session:
                repo = GrowRepository(session)
                ai_data = await repo.get_ai_latest()
                if ai_data:
                    result["ai_latest"] = {"status": "ok", "timestamp": ai_data.get("timestamp")}
                else:
                    result["ai_latest"] = {"status": "no_data", "message": "No AI decisions found"}
        except Exception as e:
            result["ai_latest"] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
        
        # Test sensors latest query
        try:
            async with get_db_session() as session:
                repo = GrowRepository(session)
                sensors = await repo.get_sensors_latest()
                if sensors:
                    result["sensors_latest"] = {"status": "ok", "count": len(sensors) if isinstance(sensors, list) else 1}
                else:
                    result["sensors_latest"] = {"status": "no_data", "message": "No sensor readings found"}
        except Exception as e:
            result["sensors_latest"] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
        
        return result

    @app.post("/api/grow/advance-day")
    async def advance_grow_day(current_user: User = Depends(get_current_admin)):
        """
        Advance to the next grow day (admin only).
        Call this at midnight or when starting a new day.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            grow_session = await repo.get_active_session()

            if not grow_session:
                raise HTTPException(status_code=404, detail="No active grow session")

            # Increment day
            new_day = await repo.increment_day(grow_session.id)
            await session.commit()

            return {
                "success": True,
                "previous_day": new_day - 1,
                "current_day": new_day,
                "message": f"Advanced to Day {new_day}"
            }

    @app.post("/api/grow/reset")
    async def reset_grow_session(current_user: User = Depends(get_current_admin)):
        """
        Reset grow session to Day 1 Granddaddy Purple Runtz clone.
        Use this to start fresh with correct data.
        REQUIRES ADMIN AUTHENTICATION.
        """
        from sqlalchemy import update

        async with get_db_session() as session:
            repo = GrowRepository(session)

            # Deactivate all existing sessions
            from .models import GrowSession, GrowthStage, Photoperiod
            await session.execute(
                update(GrowSession)
                .where(GrowSession.is_active == True)
                .values(is_active=False, end_date=datetime.utcnow())
            )
            await session.commit()

            # Create new session for Granddaddy Purple Runtz
            new_session = GrowSession(
                plant_name="Mon",
                strain_name="Granddaddy Purple Runtz",
                strain_type="Indica-dominant hybrid",
                is_active=True,
                start_date=datetime.utcnow(),
                current_day=1,
                current_stage=GrowthStage.VEGETATIVE,
                photoperiod=Photoperiod.VEG_24_0,
                notes="GDP x Runtz cross. Freshly transplanted clone."
            )
            session.add(new_session)
            await session.commit()

            return {
                "status": "reset",
                "session_id": new_session.id,
                "plant_name": new_session.plant_name,
                "strain_name": new_session.strain_name,
                "current_day": new_session.current_day,
                "current_stage": new_session.current_stage.value,
                "message": "Grow session reset to Day 1 Granddaddy Purple Runtz clone"
            }

    # =========================================================================
    # Authentication Endpoints
    # =========================================================================

    @app.post("/api/auth/token", response_model=Token)
    async def auth_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
        """Get access token with username/password (rate limited)"""
        return await login_for_access_token(request, form_data)

    @app.get("/api/auth/me")
    async def auth_me(current_user: User = Depends(get_current_user_required)):
        """Get current user info"""
        return await get_current_user_info(current_user)

    # =========================================================================
    # VPD Calculation Endpoints
    # =========================================================================

    @app.get("/api/vpd/calculate")
    async def vpd_calculate(
        temp_f: float = Query(..., description="Temperature in Fahrenheit"),
        humidity: float = Query(..., ge=0, le=100, description="Humidity percentage"),
        leaf_temp_f: Optional[float] = Query(None, description="Leaf temperature (optional)"),
    ):
        """Calculate VPD from temperature and humidity"""
        result = calculate_vpd(temp_f, humidity, leaf_temp_f)
        return result.to_dict()

    @app.get("/api/vpd/current")
    async def vpd_current():
        """Get current VPD from live sensors"""
        reading = await app.state.sensors.read_all()
        sensor_dict = reading.to_dict()

        air_temp_c = sensor_dict.get("air_temp")
        temp_f = (air_temp_c * 9 / 5 + 32) if air_temp_c is not None else 75
        humidity = sensor_dict.get("humidity")
        if humidity is None:
            humidity = sensor_dict.get("humidity_percent", 50)

        result = calculate_vpd(temp_f, humidity)
        return {
            "vpd": result.to_dict(),
            "sensors": sensor_dict,
        }

    # =========================================================================
    # Growth Stage Endpoints
    # =========================================================================

    @app.get("/api/grow/parameters/{stage}")
    async def grow_parameters(stage: str):
        """Get optimal parameters for a growth stage"""
        try:
            params = get_stage_parameters(stage)
            return params.to_dict()
        except (ValueError, KeyError):
            raise HTTPException(status_code=400, detail=f"Unknown stage: {stage}")

    @app.get("/api/grow/check")
    async def grow_check():
        """Check current conditions against stage parameters"""
        # Get current stage
        async with get_db_session() as session:
            repo = GrowRepository(session)
            stage_data = await repo.get_current_stage()

        current_stage = stage_data.get("current_stage", "vegetative") if stage_data else "vegetative"

        # Get live sensor readings
        reading = await app.state.sensors.read_all()
        sensor_dict = reading.to_dict()

        # Calculate VPD
        air_temp_c = sensor_dict.get("air_temp")
        temp_f = (air_temp_c * 9 / 5 + 32) if air_temp_c is not None else 75
        humidity = sensor_dict.get("humidity")
        if humidity is None:
            humidity = sensor_dict.get("humidity_percent", 50)
        vpd_result = calculate_vpd(temp_f, humidity)

        # Check parameters
        check = check_parameters_in_range(
            current_stage,
            temp_f=temp_f,
            humidity=humidity,
            vpd=vpd_result.vpd_kpa,
            soil_moisture=sensor_dict.get("soil_moisture_percent"),
        )

        return {
            "stage": current_stage,
            "vpd": vpd_result.to_dict(),
            "parameter_check": check,
        }

    # =========================================================================
    # Plant Health Vision Endpoint
    # =========================================================================

    @app.post("/api/vision/analyze")
    async def vision_analyze(current_user: User = Depends(get_current_user)):
        """
        Analyze plant health from webcam image.
        Uses Grok vision model for analysis.
        Returns detected issues and recommendations.
        """
        # Capture current image
        image_data = await app.state.camera.capture()

        # Get current growth stage for context
        async with get_db_session() as session:
            repo = GrowRepository(session)
            stage_data = await repo.get_current_stage()

        current_day = stage_data.get("current_day", 1) if stage_data else 1
        growth_stage = stage_data.get("current_stage", "vegetative") if stage_data else "vegetative"

        # Run Grok vision analysis
        analysis = await app.state.vision.analyze(
            image_data=image_data,
            growth_stage=growth_stage,
            current_day=current_day,
        )

        return analysis.to_dict()

    # =========================================================================
    # Token Endpoints ($MON on Monad)
    # =========================================================================

    @app.get("/api/token/metrics")
    async def get_token_metrics():
        """
        Get $MON token metrics from LFJ Token Mill.
        Mirrors SOLTOMATO's token data endpoint.
        """
        metrics = await app.state.nadfun.get_token_metrics()
        if metrics is None:
            return {"error": "Token metrics unavailable", "symbol": "$MON"}
        return metrics.to_dict()

    @app.get("/api/token/trades")
    async def get_token_trades(limit: int = Query(default=10, ge=1, le=50)):
        """Get recent $MON trades"""
        trades = await app.state.nadfun.get_recent_trades(limit=limit)
        return {"trades": [t.to_dict() for t in trades]}

    # =========================================================================
    # $GANJA Token Payment Endpoints
    # =========================================================================

    @app.get("/api/ganja/pricing")
    async def get_ganja_pricing_endpoint():
        """Get art studio pricing in $GANJA tokens."""
        from src.onchain.ganja_payments import get_ganja_pricing
        return get_ganja_pricing()

    @app.get("/api/ganja/stats")
    async def get_ganja_stats():
        """Get $GANJA payment processing statistics."""
        from src.onchain.ganja_payments import GanjaPaymentProcessor
        processor = GanjaPaymentProcessor()
        return processor.get_stats()

    @app.get("/api/ganja/payments")
    async def get_ganja_payments(
        limit: int = Query(default=20, ge=1, le=100),
        current_user: User = Depends(get_current_admin),
    ):
        """Get recent $GANJA payment history (admin only)."""
        from src.onchain.ganja_payments import GanjaPaymentProcessor
        processor = GanjaPaymentProcessor()
        return {"payments": processor.get_payment_history(limit=limit)}

    @app.post("/api/ganja/check-payments")
    async def check_ganja_payments(
        current_user: User = Depends(get_current_admin),
    ):
        """Scan for new $GANJA payments (admin only)."""
        from src.onchain.ganja_payments import GanjaPaymentProcessor
        processor = GanjaPaymentProcessor()
        new_payments = await processor.check_payments()
        return {
            "new_payments": len(new_payments),
            "payments": [p.to_dict() for p in new_payments],
        }

    @app.post("/api/ganja/process-pending")
    async def process_ganja_pending(
        current_user: User = Depends(get_current_admin),
    ):
        """Process pending $GANJA payments (burn + buyback) (admin only)."""
        from src.onchain.ganja_payments import GanjaPaymentProcessor
        processor = GanjaPaymentProcessor()
        results = await processor.process_pending()
        return {"processed": len(results), "results": results}

    # =========================================================================
    # Photoperiod Scheduling Endpoints
    # =========================================================================

    @app.get("/api/schedule/status")
    async def get_schedule_status():
        """Get current photoperiod schedule status"""
        # Note: Full implementation requires orchestrator integration
        # This provides the schedule configuration interface
        return {
            "photoperiod": "18/6",
            "light_on_hour": 6,
            "light_off_hour": 0,
            "is_light_period": True,
            "next_transition": None,
            "status": "mock - orchestrator not running",
        }

    @app.post("/api/schedule/set")
    async def set_schedule(
        hours_on: int = Query(..., ge=12, le=24),
        hours_off: int = Query(..., ge=0, le=12),
        light_on_hour: int = Query(default=6, ge=0, le=23),
        current_user: User = Depends(get_current_admin),
    ):
        """Set photoperiod schedule (admin only)"""
        if hours_on + hours_off != 24:
            raise HTTPException(status_code=400, detail="Hours must total 24")

        return {
            "status": "scheduled",
            "schedule": f"{hours_on}/{hours_off}",
            "light_on_hour": light_on_hour,
            "message": "Schedule will take effect at next transition",
        }

    # =========================================================================
    # Social Media Endpoints
    # =========================================================================

    @app.post("/api/social/tweet")
    async def post_tweet(
        text: str = Query(..., max_length=280),
        include_image: bool = Query(default=True),
        current_user: User = Depends(get_current_admin),
    ):
        """Post a tweet manually (admin only)"""
        try:
            from ..social import TwitterClient

            client = TwitterClient()

            if include_image:
                image_data = await app.state.camera.capture()
                result = await client.tweet_with_image(text, image_data)
            else:
                result = await client.tweet(text)

            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "error": result.error,
            }
        except ImportError:
            raise HTTPException(status_code=501, detail="Twitter client not available")

    # -----------------------------------------------------------------
    # Internal posting endpoint — NO AUTH, localhost-only
    # Used by OpenClaw agent via exec curl from the same machine
    # -----------------------------------------------------------------
    from pydantic import BaseModel as PydanticBaseModel

    class _TweetRequest(PydanticBaseModel):
        text: str
        include_image: bool = False

    @app.post("/api/social/post")
    async def post_tweet_internal(req: _TweetRequest, request: Request):
        """Post a tweet from the local agent (no auth, localhost only).

        Usage from OpenClaw exec:
            curl -s -X POST http://localhost:8000/api/social/post \
                 -H 'Content-Type: application/json' \
                 -d '{"text": "Ya mon!"}'
        """
        # Localhost guard — only allow from 127.0.0.1 / ::1
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        if len(req.text) > 280:
            raise HTTPException(status_code=400, detail=f"Tweet too long: {len(req.text)} chars (max 280)")

        if not req.text.strip():
            raise HTTPException(status_code=400, detail="Empty tweet text")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()

            if req.include_image:
                image_data = await app.state.camera.capture()
                result = await client.tweet_with_image(req.text, image_data)
            else:
                result = await client.tweet(req.text)

            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "url": f"https://x.com/GanjaMonAI/status/{result.tweet_id}" if result.tweet_id else None,
                "error": result.error,
            }
        except Exception as e:
            logger.error(f"Tweet posting failed: {e}")
            return {"success": False, "tweet_id": None, "url": None, "error": str(e)}

    # -----------------------------------------------------------------
    # Search tweets — for finding QT targets
    # -----------------------------------------------------------------
    @app.get("/api/social/search")
    async def search_tweets_internal(
        q: str = Query(..., description="Search query"),
        limit: int = Query(default=10, ge=1, le=50),
        request: Request = None,
    ):
        """Search recent tweets (localhost only). Used by agent to find QT targets."""
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()
            results = await client.search_recent(q, max_results=limit)
            return {
                "success": True,
                "count": len(results),
                "tweets": [
                    {
                        "id": t.id,
                        "text": t.text,
                        "author": t.author_username,
                        "author_name": t.author_name,
                        "followers": t.author_followers,
                        "likes": t.likes,
                        "retweets": t.retweets,
                        "media_urls": t.media_urls,
                        "engagement_score": t.engagement_score(),
                    }
                    for t in results
                ],
            }
        except Exception as e:
            logger.error(f"Tweet search failed: {e}")
            return {"success": False, "count": 0, "tweets": [], "error": str(e)}

    # -----------------------------------------------------------------
    # Quote tweet — for Rasta QTs
    # -----------------------------------------------------------------
    class _QuoteTweetRequest(PydanticBaseModel):
        tweet_id: str
        text: str

    @app.post("/api/social/quote")
    async def quote_tweet_internal(req: _QuoteTweetRequest, request: Request):
        """Post a quote tweet (localhost only). The Rasta QT system.

        Usage:
            curl -s -X POST http://localhost:8000/api/social/quote \
                 -H 'Content-Type: application/json' \
                 -d '{"tweet_id": "123456", "text": "Ya mon! Dis tweet irie!"}'
        """
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        if not req.text.strip():
            raise HTTPException(status_code=400, detail="Empty QT text")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()
            result = await client.quote_tweet(req.tweet_id, req.text)
            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "url": f"https://x.com/GanjaMonAI/status/{result.tweet_id}" if result.tweet_id else None,
                "quoted": req.tweet_id,
                "error": result.error,
            }
        except Exception as e:
            logger.error(f"Quote tweet failed: {e}")
            return {"success": False, "tweet_id": None, "url": None, "error": str(e)}

    # -----------------------------------------------------------------
    # Reply to tweet
    # -----------------------------------------------------------------
    class _ReplyRequest(PydanticBaseModel):
        tweet_id: str
        text: str

    @app.post("/api/social/reply")
    async def reply_tweet_internal(req: _ReplyRequest, request: Request):
        """Reply to a tweet (localhost only).

        Usage:
            curl -s -X POST http://localhost:8000/api/social/reply \
                 -H 'Content-Type: application/json' \
                 -d '{"tweet_id": "123456", "text": "Bless up bredren!"}'
        """
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        if not req.text.strip():
            raise HTTPException(status_code=400, detail="Empty reply text")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()
            result = await client.reply_to(req.tweet_id, req.text)
            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "url": f"https://x.com/GanjaMonAI/status/{result.tweet_id}" if result.tweet_id else None,
                "replied_to": req.tweet_id,
                "error": result.error,
            }
        except Exception as e:
            logger.error(f"Reply failed: {e}")
            return {"success": False, "tweet_id": None, "url": None, "error": str(e)}

    # -----------------------------------------------------------------
    # Quote tweet with uploaded image (for irie QT pipeline)
    # -----------------------------------------------------------------
    @app.post("/api/social/quote-with-image")
    async def quote_tweet_with_image_internal(
        tweet_id: str = Form(...),
        text: str = Form(...),
        image: UploadFile = File(...),
        request: Request = None,
    ):
        """QT a tweet with an uploaded image (localhost only).

        Used by the irie QT pipeline:
        1. Agent downloads original tweet image
        2. Runs nano-banana-pro to irie-fy it
        3. Uploads the irie'd image here with QT text

        Usage:
            curl -s -X POST http://localhost:8000/api/social/quote-with-image \
                 -F 'tweet_id=123456' -F 'text=Ya mon! Dis ting irie!' -F 'image=@/tmp/irie.png'
        """
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty QT text")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()
            image_data = await image.read()
            # Upload image first
            media_id = await client.upload_media(
                image_data, alt_text="GanjaMon irie transformation"
            )
            # Then quote tweet with the image
            result = await client.quote_tweet(
                tweet_id, text, media_ids=[media_id] if media_id else None
            )
            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "url": f"https://x.com/GanjaMonAI/status/{result.tweet_id}" if result.tweet_id else None,
                "quoted": tweet_id,
                "has_image": True,
                "error": result.error,
            }
        except Exception as e:
            logger.error(f"Quote tweet with image failed: {e}")
            return {"success": False, "tweet_id": None, "url": None, "error": str(e)}

    # -----------------------------------------------------------------
    # Tweet with webcam plant image (auto-captures from webcam)
    # -----------------------------------------------------------------
    @app.post("/api/social/tweet-with-image")
    async def tweet_with_image_internal(req: _TweetRequest, request: Request):
        """Post a tweet with current webcam plant image (localhost only).

        Usage:
            curl -s -X POST http://localhost:8000/api/social/tweet-with-image \
                 -H 'Content-Type: application/json' \
                 -d '{"text": "Check out di herb mon!"}'
        """
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        if len(req.text) > 280:
            raise HTTPException(status_code=400, detail=f"Tweet too long: {len(req.text)} chars")

        if not req.text.strip():
            raise HTTPException(status_code=400, detail="Empty tweet text")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()
            image_data = await app.state.camera.capture()
            result = await client.tweet_with_image(
                req.text, image_data, alt_text="GanjaMon autonomous grow cam - GDP Runtz in veg"
            )
            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "url": f"https://x.com/GanjaMonAI/status/{result.tweet_id}" if result.tweet_id else None,
                "has_image": True,
                "error": result.error,
            }
        except Exception as e:
            logger.error(f"Tweet with image failed: {e}")
            return {"success": False, "tweet_id": None, "url": None, "error": str(e)}

    # -----------------------------------------------------------------
    # Get mentions (for reply cycle)
    # -----------------------------------------------------------------
    @app.get("/api/social/mentions")
    async def get_mentions_internal(
        since_id: Optional[str] = Query(default=None),
        request: Request = None,
    ):
        """Get recent @GanjaMonAI mentions (localhost only)."""
        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail=f"Internal only (got {client_ip})")

        try:
            from ..social import TwitterClient
        except ImportError:
            try:
                from social import TwitterClient
            except ImportError:
                raise HTTPException(status_code=501, detail="Twitter client not available")

        try:
            client = TwitterClient()
            mentions = await client.get_mentions(since_id=since_id)
            return {
                "success": True,
                "count": len(mentions),
                "mentions": [
                    {
                        "id": m.id,
                        "text": m.text,
                        "author": m.author_username,
                        "likes": m.likes,
                        "created_at": str(m.created_at) if m.created_at else None,
                    }
                    for m in mentions
                ],
            }
        except Exception as e:
            logger.error(f"Get mentions failed: {e}")
            return {"success": False, "count": 0, "mentions": [], "error": str(e)}

    @app.get("/api/social/preview")
    async def preview_daily_tweet():
        """Preview what a daily tweet would look like"""
        from ..social import format_daily_update

        async with get_db_session() as session:
            repo = GrowRepository(session)
            sensors = await repo.get_sensors_latest()
            stage_data = await repo.get_current_stage()
            daily_stats = await repo.get_daily_stats(
                stage_data.get("current_day", 1) if stage_data else 1
            )

        if not sensors:
            sensors = {"air_temp": 25, "humidity": 50, "vpd": 1.0}

        tweet = format_daily_update(
            day=stage_data.get("current_day", 1) if stage_data else 1,
            stage=stage_data.get("current_stage", "vegetative") if stage_data else "vegetative",
            vpd=sensors.get("vpd", 1.0),
            temp_f=sensors.get("air_temp", 25) * 9/5 + 32,
            humidity=sensors.get("humidity", 50),
            water_ml=daily_stats.get("total_water_ml", 0) if daily_stats else 0,
        )

        return {"preview": tweet, "length": len(tweet)}

    # =========================================================================
    # Timelapse Endpoints
    # =========================================================================

    # =========================================================================
    # SOLTOMATO Pattern: Stats & Plant Progress Endpoints
    # =========================================================================

    @app.get("/api/stats")
    async def get_stats():
        """
        Get total record counts.
        Mirrors SOLTOMATO's /api/stats endpoint.

        Returns:
        {
            "total_records": {
                "sensor_readings": 8386,
                "device_states": 8386,
                "ai_outputs": 8386
            }
        }
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            return await repo.get_stats()

    @app.get("/api/plant-progress")
    async def get_plant_progress(limit: int = Query(default=50, ge=1, le=500)):
        """
        Get hourly aggregated plant progress.
        Mirrors SOLTOMATO's /api/plant-progress endpoint.

        Returns periods with:
        - Hourly averages for all metrics
        - Health flags per metric
        - ATH/ATL values and percentages
        - Auto-generated icon and summary
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            return await repo.get_plant_progress(limit=limit)

    @app.get("/api/predictions/recent")
    async def get_recent_predictions(limit: int = Query(default=10, ge=1, le=50)):
        """
        Get recent watering predictions and their accuracy.
        Used for AI learning and debugging.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            return await repo.get_recent_predictions(limit=limit)

    @app.get("/api/predictions/absorption-rate")
    async def get_absorption_rate():
        """
        Get learned soil absorption rate.
        Returns ml of water needed per 1% moisture increase.
        """
        async with get_db_session() as session:
            repo = GrowRepository(session)
            rate = await repo.get_average_absorption_rate()
            return {
                "absorption_rate_ml_per_pct": rate,
                "interpretation": f"Approximately {rate:.1f}ml of water increases soil moisture by 1%"
            }

    # =========================================================================
    # Grow Review Endpoints
    # =========================================================================

    @app.post("/api/reviews/generate")
    async def generate_review(
        review_type: str = Query(default="daily", pattern="^(daily|weekly|custom)$"),
        hours: Optional[int] = Query(default=None, ge=1, le=720),
        start_time: Optional[str] = Query(default=None),
        end_time: Optional[str] = Query(default=None),
    ):
        """Generate a new grow review for the specified period."""
        from src.review.engine import ReviewEngine
        from src.db.models import ReviewType

        async with get_db_session() as session:
            repo = GrowRepository(session)
            engine = ReviewEngine(repo)

            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None

            result = await engine.generate_review(
                review_type=ReviewType(review_type),
                hours=hours,
                start_time=start_dt,
                end_time=end_dt,
            )

            active = await repo.get_active_session()
            if not active:
                raise HTTPException(status_code=404, detail="No active grow session")

            review = await engine.store_review(result, active.id)
            await session.commit()

            return repo._review_to_dict(review)

    @app.get("/api/reviews/latest")
    async def get_latest_review(
        review_type: Optional[str] = Query(default=None),
    ):
        """Get the most recent review."""
        async with get_db_session() as session:
            repo = GrowRepository(session)
            review = await repo.get_latest_review(review_type=review_type)
            if not review:
                raise HTTPException(status_code=404, detail="No reviews found")
            return review

    @app.get("/api/reviews/history")
    async def get_review_history(
        limit: int = Query(default=10, ge=1, le=100),
    ):
        """Get review history (summaries only)."""
        async with get_db_session() as session:
            repo = GrowRepository(session)
            return await repo.get_review_history(limit=limit)

    @app.get("/api/reviews/{review_id}")
    async def get_review(review_id: int):
        """Get a specific review by ID with full data."""
        async with get_db_session() as session:
            repo = GrowRepository(session)
            review = await repo.get_review_by_id(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Review not found")
            return review

    @app.get("/api/reviews/{review_id}/markdown")
    async def get_review_markdown(review_id: int):
        """Get just the markdown report for a review."""
        async with get_db_session() as session:
            repo = GrowRepository(session)
            review = await repo.get_review_by_id(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Review not found")
            return Response(
                content=review["report_markdown"],
                media_type="text/markdown",
            )

    @app.post("/api/reviews/{review_id}/feed-to-ai")
    async def feed_review_to_ai(review_id: int):
        """Mark a review as fed to AI and return the context block."""
        from src.review.engine import ReviewEngine

        async with get_db_session() as session:
            repo = GrowRepository(session)
            review = await repo.get_review_by_id(review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Review not found")

            engine = ReviewEngine(repo)
            context_block = engine.format_for_ai_context_from_dict(review)

            await repo.mark_review_fed_to_ai(review_id)
            await session.commit()

            return {
                "status": "fed_to_ai",
                "review_id": review_id,
                "context_block": context_block,
            }

    @app.post("/api/reviews/visual-audit")
    async def visual_audit():
        """Run a live visual health audit on the current plant image.

        Captures or retrieves the latest webcam image and sends it to
        Grok vision for a comprehensive plant health analysis.
        Uses the enhanced analysis frame (white-balance corrected,
        CLAHE contrast, sharpened) for better deficiency detection.
        """
        from src.review.visual import VisualAnalyzer
        import base64 as b64

        # Get latest image — prefer analysis-enhanced frame
        image_bytes = None

        # Try continuous webcam's enhanced analysis frame first
        if hasattr(app.state.camera, "get_analysis_frame"):
            frame = app.state.camera.get_analysis_frame()
            if frame:
                image_bytes = frame

        # Fallback: try capture from camera API (no enhancement available)
        if image_bytes is None:
            try:
                from src.hardware.webcam import USBWebcam
                cam = USBWebcam()
                if await cam.connect():
                    image_bytes = await cam.capture()
            except Exception:
                pass

        if image_bytes is None:
            raise HTTPException(status_code=503, detail="No camera image available")

        image_b64 = b64.b64encode(image_bytes).decode("utf-8")

        # Get grow context
        async with get_db_session() as session:
            repo = GrowRepository(session)
            grow_session = await repo.get_active_session()
            stage_name = "vegetative"
            grow_day = 1
            strain = "Cannabis"
            sensor_snapshot = None

            if grow_session:
                stage_name = (
                    grow_session.current_stage.value
                    if hasattr(grow_session.current_stage, "value")
                    else str(grow_session.current_stage)
                )
                grow_day = grow_session.current_day or 1
                strain = grow_session.strain_name or "Cannabis"

            # Get latest sensor data for context
            latest = await repo.get_sensors_latest()
            if latest:
                sensor_snapshot = {
                    "environment": {
                        "temperature_f": latest.get("temperature_f", 75),
                        "humidity_percent": latest.get("humidity", 50),
                        "vpd_kpa": latest.get("vpd", 1.0),
                    }
                }

        analyzer = VisualAnalyzer()
        result = await analyzer.audit_plant_health(
            image_b64=image_b64,
            stage_name=stage_name,
            grow_day=grow_day,
            strain=strain,
            sensor_snapshot=sensor_snapshot,
        )

        return result

    @app.post("/api/reviews/image-quality")
    async def check_image_quality():
        """Assess the current camera image quality for plant analysis."""
        from src.review.visual import VisualAnalyzer
        import base64 as b64

        image_bytes = None

        if hasattr(app.state.camera, "get_frame"):
            frame = app.state.camera.get_frame()
            if frame:
                image_bytes = frame

        if image_bytes is None:
            try:
                from src.hardware.webcam import USBWebcam
                cam = USBWebcam()
                if await cam.connect():
                    image_bytes = await cam.capture()
            except Exception:
                pass

        if image_bytes is None:
            raise HTTPException(status_code=503, detail="No camera image available")

        image_b64 = b64.b64encode(image_bytes).decode("utf-8")

        analyzer = VisualAnalyzer()
        return await analyzer.assess_image_quality(image_b64)

    # =========================================================================
    # Timelapse Endpoints
    # =========================================================================

    @app.get("/api/timelapse/latest")
    async def get_latest_timelapse():
        """Get the most recent timelapse GIF"""
        timelapse_dir = Path(__file__).parent.parent / "media" / "timelapse"
        if not timelapse_dir.exists():
            raise HTTPException(status_code=404, detail="No timelapse available")

        # Find most recent GIF
        gifs = sorted(timelapse_dir.glob("*.gif"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not gifs:
            raise HTTPException(status_code=404, detail="No timelapse GIF found")

        return FileResponse(gifs[0], media_type="image/gif")

    @app.post("/api/timelapse/generate")
    async def generate_timelapse(
        days: int = Query(default=7, ge=1, le=30),
        fps: int = Query(default=10, ge=5, le=30),
        current_user: User = Depends(get_current_user),
    ):
        """Generate a timelapse GIF from recent images"""
        try:
            from ..media.timelapse import generate_timelapse_gif

            output_path = await generate_timelapse_gif(days=days, fps=fps)
            return {
                "status": "generated",
                "path": str(output_path),
                "days": days,
                "fps": fps,
            }
        except ImportError:
            raise HTTPException(status_code=501, detail="Timelapse module not available")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # =========================================================================
    # Banner Generation Endpoint
    # =========================================================================

    @app.post("/api/banner/generate")
    async def generate_banner(
        current_user: User = Depends(get_current_user),
    ):
        """Generate a DexScreener-style animated banner"""
        try:
            from ..media.banner import BannerGenerator

            generator = BannerGenerator()

            async with get_db_session() as session:
                repo = GrowRepository(session)
                sensors = await repo.get_sensors_latest()
                stage_data = await repo.get_current_stage()

            banner_bytes = await generator.generate(
                day=stage_data.get("current_day", 1) if stage_data else 1,
                stage=stage_data.get("current_stage", "vegetative") if stage_data else "vegetative",
                vpd=sensors.get("vpd", 1.0) if sensors else 1.0,
            )

            return Response(content=banner_bytes, media_type="image/gif")
        except ImportError:
            raise HTTPException(status_code=501, detail="Banner module not available")

    # =========================================================================
    # Unified Agent State Endpoints (the soul of the Rasta Mon)
    # =========================================================================

    # Import unified context aggregator for reading trading/social/task data
    try:
        from ..brain.unified_context import (
            UnifiedContextAggregator,
            _parse_entry_timestamp,
            _safe_read_json,
            _safe_read_jsonl_tail,
        )
    except ImportError:
        from brain.unified_context import (
            UnifiedContextAggregator,
            _parse_entry_timestamp,
            _safe_read_json,
            _safe_read_jsonl_tail,
        )

    _agent_ctx = UnifiedContextAggregator()

    # Data paths for trading agent files
    _PROJECT_ROOT = Path(__file__).parent.parent.parent
    _TRADING_DATA = _PROJECT_ROOT / "cloned-repos" / "ganjamon-agent" / "data"
    _DATA_DIR = _PROJECT_ROOT / "data"
    _CONSCIOUSNESS_FILE = _TRADING_DATA / "consciousness.json"

    @app.get("/api/agent/state")
    async def agent_unified_state():
        """The entire soul of the unified Rasta Mon agent — everything in one call."""
        trading = _agent_ctx.gather_trading_summary()
        social = _agent_ctx.gather_social_summary()
        email = _agent_ctx.gather_email_summary()
        tasks = _agent_ctx.gather_agent_tasks()
        suggestions = _agent_ctx.gather_community_suggestions()
        consciousness = _safe_read_json(_CONSCIOUSNESS_FILE) or {}

        # Get grow data from existing endpoints
        grow = {}
        try:
            async with get_db_session() as session:
                repo = GrowRepository(session)
                stage_data = await repo.get_current_stage()
                if stage_data:
                    grow = dict(stage_data)
        except Exception:
            pass

        return {
            "soul": "Rasta Mon",
            "identity": {
                "name": "GanjaMon",
                "agent_id": 4,
                "chain": "Monad",
                "erc8004": "https://8004scan.io/agents/monad/4",
                "voice": "Western Jamaican stoner rasta",
            },
            "grow": grow,
            "trading": trading,
            "social": social,
            "email": email,
            "tasks": tasks,
            "suggestions": suggestions,
            "consciousness": consciousness,
        }

    @app.get("/api/agent/trading")
    async def agent_trading():
        """Trading agent portfolio, PnL, brain state, and domain signals."""
        trading = _agent_ctx.gather_trading_summary()

        # Read full brain state for domain-level detail
        brain = _safe_read_json(_TRADING_DATA / "unified_brain_state.json") or {}
        domains = {}
        for name, data in brain.get("domains", {}).items():
            domains[name] = {
                "signals_seen": data.get("signals_seen", 0),
            }

        # Read portfolio for trade details
        portfolio = _safe_read_json(_TRADING_DATA / "paper_portfolio.json") or {}
        trades = portfolio.get("trades", [])
        open_trades = [t for t in trades if t.get("is_open")]
        recent_closed = sorted(
            [t for t in trades if not t.get("is_open")],
            key=lambda t: t.get("exit_time", ""),
            reverse=True,
        )[:10]

        total_signals = sum(d.get("signals_seen", 0) for d in domains.values())

        return {
            **trading,
            "domains": domains,
            "total_signals": total_signals,
            "started_at": brain.get("started_at"),
            "open_trades": [
                {
                    "id": t.get("id", "")[:8],
                    "symbol": t.get("token_symbol", "?"),
                    "chain": t.get("chain", "?"),
                    "entry_price": t.get("entry_price", 0),
                    "current_price": t.get("current_price", 0),
                    "pnl_pct": round(t.get("pnl_percent", 0), 1),
                    "pnl_usd": round(t.get("pnl_usd", 0), 2),
                    "entry_time": t.get("entry_time", ""),
                }
                for t in open_trades
            ],
            "recent_closed": [
                {
                    "id": t.get("id", "")[:8],
                    "symbol": t.get("token_symbol", "?"),
                    "chain": t.get("chain", "?"),
                    "pnl_pct": round(t.get("pnl_percent", 0), 1),
                    "pnl_usd": round(t.get("pnl_usd", 0), 2),
                    "exit_reason": t.get("exit_reason", ""),
                }
                for t in recent_closed
            ],
        }

    @app.get("/api/agent/signals")
    async def agent_signals():
        """Signal source overview — all 5 brain domains with signal counts."""
        brain = _safe_read_json(_TRADING_DATA / "unified_brain_state.json") or {}
        domains = brain.get("domains", {})
        total = sum(d.get("signals_seen", 0) for d in domains.values())

        signal_balance = {}
        for name, data in domains.items():
            count = data.get("signals_seen", 0)
            signal_balance[name] = {
                "signals": count,
                "pct": round(count / total, 4) if total > 0 else 0,
            }

        # Detect imbalance
        max_pct = max((d["pct"] for d in signal_balance.values()), default=0)
        dominant = max(signal_balance, key=lambda k: signal_balance[k]["pct"]) if signal_balance else None

        return {
            "total_signals": total,
            "research_cycles": brain.get("total_research_cycles", 0),
            "domains": signal_balance,
            "imbalanced": max_pct > 0.8,
            "dominant_source": dominant if max_pct > 0.8 else None,
            "dominant_pct": round(max_pct * 100, 1),
        }

    @app.get("/api/agent/learning")
    async def agent_learning():
        """Self-improvement metrics — Ralph loops, pattern extraction, experience DB."""
        # Ralph loop stats
        upgrade_requests = _safe_read_json(_TRADING_DATA / "upgrade_requests.json")
        ralph = {"total": 0, "pending": 0, "deployed": 0, "in_progress": 0}
        if isinstance(upgrade_requests, list):
            ralph["total"] = len(upgrade_requests)
            for r in upgrade_requests:
                status = r.get("status", "")
                if status == "deployed":
                    ralph["deployed"] += 1
                elif status == "pending":
                    ralph["pending"] += 1
                elif status == "in_progress":
                    ralph["in_progress"] += 1

        # Self-assessment data
        assessments = _safe_read_json(_TRADING_DATA / "self_assessments.json")
        latest_assessment = None
        if isinstance(assessments, list) and assessments:
            latest_assessment = assessments[-1].get("summary", "")

        # Domain performance
        domain_perf = _safe_read_json(_TRADING_DATA / "domain_performance.json") or {}

        return {
            "ralph": ralph,
            "latest_assessment": latest_assessment,
            "domain_performance": domain_perf,
        }

    @app.get("/api/agent/social")
    async def agent_social():
        """Social engagement across all platforms."""
        social = _agent_ctx.gather_social_summary()
        email = _agent_ctx.gather_email_summary()

        # Read social post log for per-platform breakdown
        posts = _safe_read_jsonl_tail(_TRADING_DATA / "social_post_log.jsonl", max_lines=100)
        platform_counts = {}
        for p in posts:
            ch = p.get("channel", p.get("kind", "unknown"))
            platform_counts[ch] = platform_counts.get(ch, 0) + 1

        # Telegram community stats
        telegram_profiles = _safe_read_json(_DATA_DIR / "telegram_user_profiles.json")
        og_count = len(telegram_profiles) if isinstance(telegram_profiles, dict) else 0

        return {
            **social,
            "email": email,
            "platform_post_counts": platform_counts,
            "telegram_og_profiles": og_count,
        }

    @app.get("/api/agent/tasks")
    async def agent_tasks():
        """Pending agent goals and tasks."""
        tasks = _agent_ctx.gather_agent_tasks()
        suggestions = _agent_ctx.gather_community_suggestions()
        return {
            "tasks": tasks,
            "task_count": len(tasks),
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
        }

    @app.get("/api/agent/consciousness")
    async def agent_consciousness():
        """Self-awareness: focus, stuck detection, goal progress, inner monologue."""
        # Read consciousness file written by stuck detector
        consciousness = _safe_read_json(_CONSCIOUSNESS_FILE)
        if consciousness:
            return consciousness

        # Fallback: compute basic awareness from available data
        brain = _safe_read_json(_TRADING_DATA / "unified_brain_state.json") or {}
        domains = brain.get("domains", {})
        total = sum(d.get("signals_seen", 0) for d in domains.values())

        signal_balance = {}
        for name, data in domains.items():
            count = data.get("signals_seen", 0)
            signal_balance[name] = {
                "pct": round(count / total, 4) if total > 0 else 0,
                "signals": count,
            }

        max_pct = max((d["pct"] for d in signal_balance.values()), default=0)
        dominant = max(signal_balance, key=lambda k: signal_balance[k]["pct"]) if signal_balance else None
        stuck = max_pct > 0.8

        # Goal progress
        trading = _agent_ctx.gather_trading_summary()
        social = _agent_ctx.gather_social_summary()
        pnl_pct = trading.get("total_pnl_pct", 0)

        return {
            "timestamp": datetime.now().isoformat(),
            "focus": "trading_signals",
            "signal_balance": signal_balance,
            "stuck": stuck,
            "stuck_on": dominant if stuck else None,
            "stuck_reason": f"{round(max_pct*100)}% of signals from {dominant}" if stuck else None,
            "goal_progress": {
                "make_money": {
                    "score": max(0, min(1, (pnl_pct + 100) / 200)),
                    "detail": f"Portfolio {pnl_pct:+.1f}%",
                },
                "grow_plant": {
                    "score": 0.8,
                    "detail": "Mon healthy in veg",
                },
                "build_community": {
                    "score": min(1, social.get("total_posts_24h", 0) / 10),
                    "detail": f"{social.get('total_posts_24h', 0)} posts in 24h",
                },
            },
            "last_trade": None,
            "last_social_post": None,
            "last_grow_decision": None,
            "ralph_status": None,
            "inner_monologue": "Consciousness file not yet written by stuck detector. Using computed fallback.",
        }

    @app.get("/api/agent/identity")
    async def agent_identity():
        """ERC-8004 on-chain identity, MCP tools, A2A status."""
        return {
            "name": "GanjaMon",
            "agent_id": 4,
            "chain": "Monad",
            "registry": "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
            "owner": "0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
            "agent_uri": "ipfs://QmXoSTMYsLsfqqsC2jShVhEa3HrVLxCi9tvx2i7dAKD5Zf",
            "scanner_url": "https://8004scan.io/agents/monad/4",
            "services": {
                "a2a": {"url": "https://grokandmon.com/a2a/v1", "status": "active"},
                "mcp": {"tools_count": 20, "status": "active"},
            },
            "token": {
                "symbol": "$MON",
                "monad": "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b",
                "base": "0xE390612D7997B538971457cfF29aB4286cE97BE2",
            },
            "bridge": {
                "protocol": "Wormhole NTT",
                "monad_to_base": "working",
                "base_to_monad": "working",
            },
            "reputation": {
                "registry": "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63",
                "cron": "30 */4 * * *",
            },
        }

    # =========================================================================
    # Agent Brain Dashboard API
    # =========================================================================

    @app.get("/api/agent/conversations")
    async def agent_conversations(limit: int = Query(50, ge=1, le=200)):
        """A2A conversation threads with follow-ups."""
        interactions_file = Path("data/a2a_interactions.json")
        reliability_file = Path("data/a2a_reliability.json")
        result = {"conversations": [], "stats": {}, "quality_breakdown": {}}

        if interactions_file.exists():
            try:
                data = json.loads(interactions_file.read_text())
                interactions = data.get("interactions", [])
                # Filter to successful interactions (response_data is optional)
                convos = [i for i in interactions if i.get("success")]
                # Most recent first
                convos = convos[-limit:][::-1]
                result["conversations"] = convos
                result["stats"] = {
                    "total_rounds": data.get("total_rounds", 0),
                    "total_calls": data.get("total_calls", 0),
                    "total_successes": data.get("total_successes", 0),
                    "x402_spent_today": data.get("x402_spent_today", 0),
                    "success_rate": round(data.get("total_successes", 0) / max(data.get("total_calls", 1), 1) * 100, 1),
                }
                result["quality_breakdown"] = data.get("agent_quality_breakdown", {})
                result["valuable_agents"] = data.get("valuable_agents", [])
            except Exception as e:
                logger.warning("Failed to load conversations: %s", e)

        if reliability_file.exists():
            try:
                rel_data = json.loads(reliability_file.read_text())
                result["agents_tracked"] = len(rel_data)
                result["agents_blacklisted"] = sum(
                    1 for r in rel_data.values()
                    if r.get("consecutive_failures", 0) >= 3
                )
            except Exception:
                pass

        return result

    @app.get("/api/agent/emails")
    async def agent_emails(limit: int = Query(50, ge=1, le=200)):
        """Email inbox and outbox threads."""
        inbox_file = Path("data/email_inbox.json")
        outbox_file = Path("data/email_outbox.json")
        state_file = Path("data/email_state.json")
        result = {"inbox": [], "outbox": [], "state": {}}

        if inbox_file.exists():
            try:
                inbox = json.loads(inbox_file.read_text())
                if isinstance(inbox, list):
                    result["inbox"] = inbox[-limit:][::-1]
                elif isinstance(inbox, dict):
                    result["inbox"] = inbox.get("emails", [])[-limit:][::-1]
            except Exception:
                pass

        if outbox_file.exists():
            try:
                outbox = json.loads(outbox_file.read_text())
                if isinstance(outbox, list):
                    result["outbox"] = outbox[-limit:][::-1]
                elif isinstance(outbox, dict):
                    result["outbox"] = outbox.get("emails", outbox.get("queue", []))[-limit:][::-1]
            except Exception:
                pass

        if state_file.exists():
            try:
                result["state"] = json.loads(state_file.read_text())
            except Exception:
                pass

        return result

    @app.get("/api/agent/social-feed")
    async def agent_social_feed(limit: int = Query(50, ge=1, le=500)):
        """Social media post feed from all platforms and runtimes."""
        log_file = Path("data/engagement_log.jsonl")
        state_file = Path("data/engagement_state.json")
        trading_log_file = _TRADING_DATA / "social_post_log.jsonl"
        result = {"posts": [], "state": {}, "platforms": {}}

        def _normalize_post(entry: dict, source: str) -> dict:
            ts = entry.get("timestamp") or entry.get("ts") or entry.get("time") or entry.get("created_at")
            dt = _parse_entry_timestamp(entry)

            meta = entry.get("meta")
            if not isinstance(meta, dict):
                meta = entry.get("metadata")
            if not isinstance(meta, dict):
                meta = {}

            platform = entry.get("platform") or entry.get("channel")
            if not platform:
                kind = str(entry.get("kind", "")).lower()
                platform = "twitter" if kind in {"short", "long"} else "unknown"

            post_type = entry.get("post_type") or entry.get("action") or entry.get("kind") or "post"
            content = entry.get("content") or entry.get("text") or entry.get("message")
            tweet_id = entry.get("tweet_id") or meta.get("tweet_id")
            url = entry.get("url") or meta.get("url")
            if not url and tweet_id:
                url = f"https://x.com/GanjaMonAI/status/{tweet_id}"

            return {
                "timestamp": ts or (dt.isoformat() if dt else None),
                "platform": platform,
                "post_type": post_type,
                "content": content,
                "tweet_id": tweet_id,
                "url": url,
                "source": source,
                "meta": meta,
                "_sort_ts": dt.timestamp() if dt else 0.0,
            }

        posts: List[dict] = []

        try:
            for entry in _safe_read_jsonl_tail(log_file, max_lines=1200):
                if isinstance(entry, dict):
                    posts.append(_normalize_post(entry, source="engagement_log"))
        except Exception:
            pass

        try:
            for entry in _safe_read_jsonl_tail(trading_log_file, max_lines=1200):
                if isinstance(entry, dict):
                    posts.append(_normalize_post(entry, source="trading_social_log"))
        except Exception:
            pass

        posts.sort(key=lambda p: p.get("_sort_ts", 0.0), reverse=True)
        trimmed = posts[:limit]
        for p in trimmed:
            p.pop("_sort_ts", None)
        result["posts"] = trimmed

        platforms: dict[str, int] = {}
        for p in posts:
            plat = str(p.get("platform") or "unknown")
            platforms[plat] = platforms.get(plat, 0) + 1
        result["platforms"] = platforms

        if state_file.exists():
            try:
                result["state"] = json.loads(state_file.read_text())
            except Exception:
                pass

        return result

    @app.get("/api/agent/brain-activity")
    async def agent_brain_activity(limit: int = Query(20, ge=1, le=100)):
        """Brain decisions, episodic memory, and learning state."""
        result = {
            "latest_decision": None,
            "decision_history": [],
            "episodic_memory": [],
            "learning": {},
            "consciousness": {},
        }

        # Latest AI decision
        decision_file = Path("data/latest_decision.json")
        if decision_file.exists():
            try:
                result["latest_decision"] = json.loads(decision_file.read_text())
            except Exception:
                pass

        # Episodic memory
        memory_file = Path("data/logs/episodic_memory.json")
        if memory_file.exists():
            try:
                mem = json.loads(memory_file.read_text())
                if isinstance(mem, list):
                    result["episodic_memory"] = mem[-limit:][::-1]
                elif isinstance(mem, dict):
                    result["episodic_memory"] = mem.get("entries", mem.get("memories", []))[-limit:][::-1]
            except Exception:
                pass

        # Decision log (today's JSONL)
        from datetime import date
        today_log = Path(f"data/logs/decisions_{date.today().strftime('%Y%m%d')}.jsonl")
        if today_log.exists():
            try:
                decisions = []
                for line in today_log.read_text().strip().split("\n"):
                    if line.strip():
                        try:
                            decisions.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                result["decision_history"] = decisions[-limit:][::-1]
            except Exception:
                pass

        # Self-assessments
        assess_file = Path("data/self_assessments.json")
        if assess_file.exists():
            try:
                assessments = json.loads(assess_file.read_text())
                if isinstance(assessments, list):
                    result["self_assessments"] = assessments[-5:][::-1]
            except Exception:
                pass

        # Agentic metadata from latest decision
        if result["latest_decision"]:
            d = result["latest_decision"]
            result["agentic"] = {
                "tool_rounds": d.get("tool_rounds", 0),
                "total_tool_calls": d.get("total_tool_calls", 0),
                "trigger": d.get("trigger", "scheduled"),
                "actions_taken": d.get("actions_taken", []),
            }

        return result

    @app.get("/api/agent/activity-timeline")
    async def agent_activity_timeline(limit: int = Query(100, ge=1, le=500)):
        """Unified timeline of all agent activity: A2A, social, email, decisions."""
        timeline = []

        # A2A conversations
        interactions_file = Path("data/a2a_interactions.json")
        if interactions_file.exists():
            try:
                data = json.loads(interactions_file.read_text())
                for i in data.get("interactions", [])[-50:]:
                    if i.get("success"):
                        timeline.append({
                            "type": "a2a",
                            "timestamp": i.get("timestamp", ""),
                            "title": f"A2A: {i.get('agent_name', '?')}",
                            "detail": _extract_message(i.get("response_data")),
                            "quality": i.get("response_quality"),
                            "followup": bool(i.get("followup_sent")),
                            "chain": i.get("agent_chain"),
                        })
            except Exception:
                pass

        # Social posts
        log_file = Path("data/engagement_log.jsonl")
        if log_file.exists():
            try:
                for line in log_file.read_text().strip().split("\n")[-50:]:
                    if line.strip():
                        try:
                            p = json.loads(line)
                            timeline.append({
                                "type": "social",
                                "timestamp": p.get("timestamp", p.get("ts", "")),
                                "title": f"{p.get('platform', p.get('channel', '?')).title()}: {p.get('action', 'post')}",
                                "detail": (p.get("content", p.get("text", p.get("message", ""))))[:300],
                                "platform": p.get("platform", p.get("channel")),
                                "url": p.get("url", p.get("link")),
                            })
                        except json.JSONDecodeError:
                            continue
            except Exception:
                pass

        # Emails
        inbox_file = Path("data/email_inbox.json")
        if inbox_file.exists():
            try:
                inbox = json.loads(inbox_file.read_text())
                emails = inbox if isinstance(inbox, list) else inbox.get("emails", [])
                for e in emails[-20:]:
                    timeline.append({
                        "type": "email",
                        "timestamp": e.get("timestamp", e.get("received_at", "")),
                        "title": f"Email from {e.get('from', e.get('sender', '?'))}",
                        "detail": (e.get("subject", "") + ": " + e.get("body", e.get("text", ""))[:200]),
                        "direction": "inbound",
                    })
            except Exception:
                pass

        # AI decisions
        decision_file = Path("data/latest_decision.json")
        if decision_file.exists():
            try:
                d = json.loads(decision_file.read_text())
                timeline.append({
                    "type": "decision",
                    "timestamp": d.get("timestamp", ""),
                    "title": "AI Decision",
                    "detail": (d.get("summary", d.get("reasoning", "")))[:300],
                })
            except Exception:
                pass

        # Sort by timestamp descending
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"timeline": timeline[:limit]}

    def _extract_message(data: Any) -> str:
        """Extract human-readable message from response data."""
        if not data:
            return ""
        if isinstance(data, dict):
            msg = data.get("message", data.get("text", ""))
            if msg:
                return str(msg)[:300]
            preview = data.get("preview", "")
            if preview:
                return str(preview)[:300]
            return json.dumps(data)[:300]
        return str(data)[:300]

    @app.get("/api/agent/alpha-hunts")
    async def agent_alpha_hunts(limit: int = Query(50, ge=1, le=200)):
        """Alpha hunting: targets, sources, observations, signal pipeline."""
        targets = _safe_read_json(_TRADING_DATA / "hunting_targets.json") or []
        sources = _safe_read_json(_TRADING_DATA / "hunted_sources.json") or []
        discovered = _safe_read_json(_TRADING_DATA / "discovered_sources.json") or []

        # Observations can be large (1.5MB) — only return last N
        obs_file = _TRADING_DATA / "observations.json"
        observations = []
        obs_stats = {"total": 0, "acted": 0, "ignored": 0}
        if obs_file.exists():
            try:
                all_obs = json.loads(obs_file.read_text())
                if isinstance(all_obs, list):
                    obs_stats["total"] = len(all_obs)
                    obs_stats["acted"] = sum(1 for o in all_obs if o.get("acted"))
                    obs_stats["ignored"] = obs_stats["total"] - obs_stats["acted"]
                    observations = all_obs[-limit:][::-1]
            except Exception:
                pass

        return {
            "hunting_targets": targets[:20] if isinstance(targets, list) else targets,
            "hunted_sources": sources[:20] if isinstance(sources, list) else sources,
            "discovered_sources": discovered[:20] if isinstance(discovered, list) else discovered,
            "observations": observations,
            "observation_stats": obs_stats,
        }

    @app.get("/api/agent/onchain")
    async def agent_onchain_activity():
        """All on-chain activity: $GANJA token, TWAP buys, reputation, NFTs, grow logs."""
        # $GANJA deployment
        ganja = _safe_read_json(_TRADING_DATA / "ganja_deployment.json") or {}

        # TWAP buying state
        twap = _safe_read_json(_TRADING_DATA / "twap_state.json") or {}

        # Reputation publishes
        rep = _safe_read_json(_DATA_DIR / "last_reputation_publish.json") or {}

        # GrowRing NFT mints
        nft_mints = _safe_read_jsonl_tail(_DATA_DIR / "growring" / "mint_log.jsonl", 20)

        # On-chain grow logs
        grow_logs = _safe_read_jsonl_tail(_DATA_DIR / "onchain_grow_log.jsonl", 20)

        # Build unified chronological feed
        feed = []
        for buy in twap.get("buys", []):
            feed.append({
                "type": "twap_buy",
                "timestamp": buy.get("time", ""),
                "tx_hash": buy.get("tx", ""),
                "detail": f"TWAP buy #{buy.get('chunk', '?')}: {buy.get('mon', 0):.1f} MON -> {buy.get('tokens', 0):,.0f} $GANJA",
            })
        if rep.get("tx_hash"):
            feed.append({
                "type": "reputation",
                "timestamp": rep.get("timestamp", rep.get("published_at", "")),
                "tx_hash": rep.get("tx_hash", ""),
                "detail": f"Published {rep.get('signal_count', rep.get('signals_count', '?'))} reputation signals",
            })
        for mint in nft_mints:
            feed.append({
                "type": "nft_mint",
                "timestamp": mint.get("timestamp", mint.get("minted_at", "")),
                "tx_hash": mint.get("tx_hash", ""),
                "detail": f"Minted GrowRing #{mint.get('token_id', '?')} — {mint.get('milestone', mint.get('type', 'daily'))}",
            })
        for log in grow_logs:
            feed.append({
                "type": "grow_log",
                "timestamp": log.get("timestamp", ""),
                "tx_hash": log.get("tx_hash", ""),
                "detail": f"Logged {log.get('action_count', log.get('batch_size', '?'))} grow actions on-chain",
            })
        if ganja.get("tx_hash"):
            feed.append({
                "type": "token_launch",
                "timestamp": ganja.get("deployed_at", ""),
                "tx_hash": ganja.get("tx_hash", ""),
                "detail": f"Launched $GANJA on nad.fun (deploy fee: {ganja.get('deploy_fee_mon', 10)} MON)",
            })

        feed.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "ganja": {k: ganja.get(k) for k in ("deployed", "token_address", "pool_address", "deployed_at", "deployer", "initial_buy_mon", "deploy_fee_mon") if ganja.get(k) is not None},
            "twap": {
                "started": twap.get("started", False),
                "chunks_completed": twap.get("chunks_completed", 0),
                "total_chunks": twap.get("total_chunks", 10),
                "total_mon_spent": twap.get("total_mon_spent", 0),
                "total_tokens_bought": twap.get("total_tokens_bought", 0),
                "buys": twap.get("buys", []),
            },
            "reputation": rep,
            "nft_mints": nft_mints,
            "grow_logs": grow_logs,
            "feed": feed[:50],
        }

    @app.get("/api/agent/capabilities")
    async def agent_capabilities():
        """Agent capabilities: status, health, discovery."""
        status = _safe_read_json(_TRADING_DATA / "capability_status.json") or {}
        discovered = _safe_read_json(_TRADING_DATA / "discovered_capabilities.json") or {}
        gaps = _safe_read_json(_TRADING_DATA / "capability_gaps.json") or []

        # Count statuses
        caps = status.get("capabilities", status) if isinstance(status, dict) else {}
        counts = {"working": 0, "broken": 0, "not_implemented": 0, "total": 0}
        if isinstance(caps, dict):
            for k, v in caps.items():
                s = v.get("status", "unknown") if isinstance(v, dict) else str(v)
                counts["total"] += 1
                if s in counts:
                    counts[s] += 1
        elif isinstance(caps, list):
            counts["total"] = len(caps)
            for c in caps:
                s = c.get("status", "unknown") if isinstance(c, dict) else "unknown"
                if s in counts:
                    counts[s] += 1

        return {
            "capabilities": caps,
            "discovered": discovered,
            "gaps": gaps[:20] if isinstance(gaps, list) else gaps,
            "counts": counts,
            "health_pct": round(counts["working"] / max(counts["total"], 1) * 100, 1),
        }

    @app.get("/api/agent/research")
    async def agent_research():
        """Edge research, cross-domain learnings, strategy insights."""
        edge = _safe_read_json(_TRADING_DATA / "edge_research.json") or {}
        cross_domain = _safe_read_json(_TRADING_DATA / "cross_domain_learnings.json") or {}
        strategy = _safe_read_json(_TRADING_DATA / "strategy_learnings.json") or {}

        # Latest learning sessions
        sessions_dir = _TRADING_DATA / "learning_sessions"
        recent_sessions = []
        if sessions_dir.exists():
            session_files = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
            for sf in session_files:
                try:
                    recent_sessions.append(json.loads(sf.read_text()))
                except Exception:
                    pass

        return {
            "edge_research": edge,
            "cross_domain_learnings": cross_domain,
            "strategy_learnings": strategy,
            "recent_sessions": recent_sessions,
            "session_count": len(list(sessions_dir.glob("*.json"))) if sessions_dir.exists() else 0,
        }

    @app.get("/api/agent/market-regime")
    async def agent_market_regime():
        """Market regime analysis and capital allocation."""
        regime = _safe_read_json(_TRADING_DATA / "regime_analysis.json") or {}
        brain = _safe_read_json(_TRADING_DATA / "unified_brain_state.json") or {}

        # Extract attention weights
        attention = {}
        for name, data in brain.get("domains", {}).items():
            attention[name] = {
                "weight": data.get("attention_weight", data.get("weight", 0)),
                "signals_seen": data.get("signals_seen", 0),
            }

        return {
            "regime": regime.get("regime", regime.get("current_regime", "unknown")),
            "confidence": regime.get("confidence", 0),
            "allocation": regime.get("allocation", {}),
            "attention_weights": attention,
            "analysis": regime,
            "brain_started_at": brain.get("started_at"),
            "total_rounds": brain.get("round", brain.get("total_rounds", 0)),
        }

    @app.get("/api/agent/self-improvement")
    async def agent_self_improvement():
        """Self-improvement: upgrades, assessments, capability gaps."""
        upgrades = _safe_read_json(_TRADING_DATA / "upgrade_requests.json")
        assessments = _safe_read_json(_TRADING_DATA / "self_assessments.json")
        tool_acq = _safe_read_json(_TRADING_DATA / "tool_acquisition.json") or {}

        # Count upgrade status
        upgrade_list = []
        upgrade_stats = {"total": 0, "pending": 0, "completed": 0, "rejected": 0}
        if isinstance(upgrades, list):
            upgrade_list = upgrades
        elif isinstance(upgrades, dict):
            upgrade_list = upgrades.get("requests", upgrades.get("upgrades", []))

        upgrade_stats["total"] = len(upgrade_list) if isinstance(upgrade_list, list) else 0
        for u in (upgrade_list if isinstance(upgrade_list, list) else []):
            s = u.get("status", "pending") if isinstance(u, dict) else "pending"
            if s in upgrade_stats:
                upgrade_stats[s] += 1

        # Recent assessments
        assess_list = []
        if isinstance(assessments, list):
            assess_list = assessments[-10:][::-1]
        elif isinstance(assessments, dict):
            assess_list = assessments.get("assessments", [])[-10:][::-1]

        return {
            "upgrade_stats": upgrade_stats,
            "recent_upgrades": (upgrade_list[-20:][::-1]) if isinstance(upgrade_list, list) else [],
            "assessments": assess_list,
            "tool_acquisition": tool_acq,
        }

    @app.get("/brain")
    async def brain_dashboard():
        """Serve the Agent Brain dashboard."""
        brain_path = Path(__file__).parent.parent / "web" / "brain.html"
        if brain_path.exists():
            return FileResponse(brain_path)
        raise HTTPException(status_code=404, detail="Brain dashboard not found")

    # =========================================================================
    # WebSocket for Real-time Updates
    # =========================================================================

    @app.websocket("/ws/sensors")
    async def websocket_sensors(websocket: WebSocket, token: Optional[str] = Query(default=None)):
        """
        WebSocket endpoint for real-time sensor updates.
        Broadcasts sensor readings every 5 seconds.

        Authentication: Pass JWT token as query param: /ws/sensors?token=xxx
        If no token, connection is read-only with limited data.
        """
        from jose import jwt, JWTError
        from .auth import SECRET_KEY, ALGORITHM

        MAX_WS_CONNECTIONS = 50  # Prevent resource exhaustion

        # Check connection limit before accepting
        if len(app.state.ws_connections) >= MAX_WS_CONNECTIONS:
            logger.warning(f"WebSocket connection rejected: max {MAX_WS_CONNECTIONS} reached")
            await websocket.close(code=4029, reason="Too many connections")
            return

        # Validate token if provided
        authenticated = False
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if username:
                    authenticated = True
            except JWTError:
                logger.warning(f"WebSocket auth failed: invalid token")
                await websocket.close(code=4001, reason="Invalid token")
                return

        await websocket.accept()
        app.state.ws_connections.append(websocket)
        logger.debug(f"WebSocket connected. Total: {len(app.state.ws_connections)}")

        try:
            while True:
                # Read sensors
                reading = await app.state.sensors.read_all()
                state = await app.state.actuators.get_state()

                sensor_payload = reading.to_dict()
                # Add compatibility fields for frontend expectations
                if reading.air_temp is not None:
                    sensor_payload["temperature_f"] = reading.air_temp * 9 / 5 + 32
                sensor_payload["humidity_percent"] = reading.humidity
                sensor_payload["vpd_kpa"] = reading.vpd
                sensor_payload["co2_ppm"] = reading.co2
                sensor_payload["soil_moisture_percent"] = reading.soil_moisture

                # Authenticated users get full data, others get limited
                if authenticated:
                    await websocket.send_json({
                        "type": "sensor_update",
                        "sensors": sensor_payload,
                        "devices": state.to_dict(),
                        "authenticated": True,
                    })
                else:
                    # Limited public data
                    await websocket.send_json({
                        "type": "sensor_update",
                        "sensors": {
                            "air_temp": reading.air_temp,
                            "humidity": reading.humidity,
                            "vpd": reading.vpd,
                            "temperature_f": sensor_payload.get("temperature_f"),
                            "humidity_percent": sensor_payload.get("humidity_percent"),
                            "vpd_kpa": sensor_payload.get("vpd_kpa"),
                        },
                        "authenticated": False,
                    })

                # Wait before next update
                await asyncio.sleep(5)

        except WebSocketDisconnect:
            pass
        finally:
            if websocket in app.state.ws_connections:
                app.state.ws_connections.remove(websocket)
            logger.debug(f"WebSocket disconnected. Total: {len(app.state.ws_connections)}")

    # =========================================================================
    # WebSocket Chat (Public - no auth required)
    # =========================================================================

    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """
        WebSocket endpoint for public chat.
        Simple local chat - messages are not persisted.
        """
        MAX_CHAT_CONNECTIONS = 100

        # Track chat connections separately
        if not hasattr(app.state, 'chat_connections'):
            app.state.chat_connections = []

        if len(app.state.chat_connections) >= MAX_CHAT_CONNECTIONS:
            logger.warning(f"Chat connection rejected: max {MAX_CHAT_CONNECTIONS} reached")
            await websocket.close(code=4029, reason="Too many connections")
            return

        await websocket.accept()
        app.state.chat_connections.append(websocket)
        logger.debug(f"Chat connected. Total: {len(app.state.chat_connections)}")

        try:
            # Send online count to new user
            await websocket.send_json({
                "type": "online_count",
                "count": len(app.state.chat_connections)
            })

            # Broadcast to all that someone joined
            for conn in app.state.chat_connections:
                if conn != websocket:
                    try:
                        await conn.send_json({
                            "type": "online_count",
                            "count": len(app.state.chat_connections)
                        })
                    except Exception:
                        pass

            while True:
                # Wait for messages from client
                data = await websocket.receive_json()

                # Handle ping/keepalive (for Cloudflare timeout prevention)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                # Broadcast message to all OTHER connected clients (not sender)
                message = {
                    "type": "chat_message",
                    "user": data.get("user", "Anon"),
                    "message": data.get("message", "")[:500],  # Limit message length
                    "timestamp": datetime.utcnow().isoformat()
                }

                for conn in app.state.chat_connections:
                    if conn != websocket:  # Don't send back to sender
                        try:
                            await conn.send_json(message)
                        except Exception:
                            pass

        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.warning(f"Chat WebSocket error: {e}")
        finally:
            if websocket in app.state.chat_connections:
                app.state.chat_connections.remove(websocket)
            logger.debug(f"Chat disconnected. Total: {len(app.state.chat_connections)}")

            # Broadcast updated count
            for conn in app.state.chat_connections:
                try:
                    await conn.send_json({
                        "type": "online_count",
                        "count": len(app.state.chat_connections)
                    })
                except Exception:
                    pass

    # =========================================================================
    # Paperclip Game — Autonomous Bartering Experiment
    # =========================================================================

    @app.get("/api/paperclip")
    async def paperclip_scoreboard():
        """
        Public scoreboard for the Paperclip Game.
        Shows portfolio, trades, milestones, and progress toward goal.
        """
        try:
            from src.experiments.paperclip import get_paperclip_game
            game = get_paperclip_game()
            return await game.get_scoreboard()
        except Exception as e:
            logger.warning(f"Paperclip API error: {e}")
            return {
                "error": "Game not initialized",
                "detail": str(e),
                "game_start": None,
                "total_value_usd": 0,
                "goal_usd": 300,
                "progress_pct": 0,
                "total_trades": 0,
            }

    @app.post("/api/paperclip/x402-revenue")
    async def paperclip_record_revenue(data: dict):
        """Record incoming x402 revenue for the Paperclip Game."""
        try:
            from src.experiments.paperclip import get_paperclip_game
            game = get_paperclip_game()
            amount = float(data.get("amount_usd", 0))
            service = data.get("service", "unknown")
            counterparty = data.get("counterparty", "")
            if amount > 0:
                game.record_x402_revenue(amount, service, counterparty)
            return {"success": True, "new_balance": game.portfolio.cash_usdc}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.post("/api/paperclip/strategy-cycle")
    async def paperclip_run_strategy(current_user: User = Depends(get_current_admin)):
        """Manually trigger a strategy cycle (admin only)."""
        try:
            from src.experiments.paperclip import get_paperclip_game
            game = get_paperclip_game()
            result = await game.run_strategy_cycle()
            return result
        except Exception as e:
            return {"error": str(e)}

    @app.get("/paperclip")
    async def serve_paperclip():
        """Serve the Paperclip Game scoreboard page."""
        page_path = Path(__file__).parent.parent / "web" / "paperclip.html"
        if page_path.exists():
            return FileResponse(page_path)
        raise HTTPException(status_code=404, detail="Paperclip page not found")

    # =========================================================================
    # Analytics Endpoints
    # =========================================================================

    @app.post("/api/analytics/heartbeat")
    async def analytics_heartbeat():
        """Accept heartbeat pings from frontend for analytics."""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    @app.get("/api/analytics/heartbeat")
    async def analytics_heartbeat_get():
        """GET fallback for heartbeat."""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    @app.post("/api/analytics/session")
    async def analytics_session():
        """Accept session start events from frontend."""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    @app.post("/api/analytics/event")
    async def analytics_event():
        """Accept analytics events from frontend (page views, clicks, etc)."""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    # =========================================================================
    # Voice Pipeline Control Endpoints (LOCALHOST ONLY)
    # =========================================================================

    def check_localhost(request: Request):
        """Verify request is from localhost"""
        client_host = request.client.host if request.client else None
        if client_host not in ("127.0.0.1", "localhost", "::1"):
            raise HTTPException(status_code=403, detail="Voice API is localhost only")

    @app.get("/api/voice/status")
    async def get_voice_status(request: Request):
        """Get current voice pipeline status (localhost only)"""
        check_localhost(request)
        try:
            from voice.manager import get_voice_manager
            manager = get_voice_manager()
            return manager.get_status()
        except ImportError:
            return {"running": False, "error": "Voice module not available"}

    @app.post("/api/voice/start")
    async def start_voice_pipeline(request: Request):
        """Start the voice pipeline (localhost only)"""
        check_localhost(request)
        try:
            from voice.manager import get_voice_manager
            manager = get_voice_manager()
            result = await manager.start()
            return result
        except ImportError:
            return {"success": False, "error": "Voice module not available"}

    @app.post("/api/voice/stop")
    async def stop_voice_pipeline(request: Request):
        """Stop the voice pipeline (localhost only)"""
        check_localhost(request)
        try:
            from voice.manager import get_voice_manager
            manager = get_voice_manager()
            result = await manager.stop()
            return result
        except ImportError:
            return {"success": False, "error": "Voice module not available"}

    @app.get("/api/voice/events")
    async def get_voice_events(request: Request, limit: int = Query(default=20, ge=1, le=100)):
        """Get recent voice events (localhost only)"""
        check_localhost(request)
        try:
            from voice.manager import get_voice_manager
            manager = get_voice_manager()
            return {"events": manager.get_recent_events(limit=limit)}
        except ImportError:
            return {"events": [], "error": "Voice module not available"}

    @app.websocket("/ws/voice")
    async def websocket_voice(websocket: WebSocket, token: Optional[str] = Query(default=None)):
        """
        WebSocket endpoint for real-time voice pipeline updates (localhost only).
        Streams transcripts, rasta outputs, and latency in real-time.
        """
        # Only allow localhost access
        client_host = websocket.client.host if websocket.client else None
        if client_host not in ("127.0.0.1", "localhost", "::1"):
            await websocket.close(code=4003, reason="Voice WebSocket is localhost only")
            return

        await websocket.accept()

        # Track voice WebSocket connections
        if not hasattr(app.state, 'voice_ws_connections'):
            app.state.voice_ws_connections = []
        app.state.voice_ws_connections.append(websocket)

        try:
            from voice.manager import get_voice_manager
            manager = get_voice_manager()

            # Callback to forward events to this WebSocket
            async def on_event(event):
                try:
                    await websocket.send_json({
                        "type": "voice_event",
                        "event": event.to_dict()
                    })
                except Exception:
                    pass

            # Since callback needs to be sync, we'll poll instead
            last_event_count = len(manager.events)

            while True:
                # Check for new events
                current_count = len(manager.events)
                if current_count > last_event_count:
                    new_events = list(manager.events)[last_event_count:]
                    for event in new_events:
                        await websocket.send_json({
                            "type": "voice_event",
                            "event": event.to_dict()
                        })
                    last_event_count = current_count

                # Send status update
                await websocket.send_json({
                    "type": "voice_status",
                    "status": manager.get_status()
                })

                # Handle ping/pong
                try:
                    # Non-blocking receive with timeout
                    data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=1.0
                    )
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except asyncio.TimeoutError:
                    pass
                except WebSocketDisconnect:
                    break

        except ImportError:
            await websocket.send_json({"type": "error", "error": "Voice module not available"})
        except WebSocketDisconnect:
            pass
        finally:
            if websocket in app.state.voice_ws_connections:
                app.state.voice_ws_connections.remove(websocket)

    # =========================================================================
    # Lead Capture (Email List) - With Input Validation
    # =========================================================================

    import re
    import html

    def _sanitize_input(value: Optional[str], max_length: int = 200) -> Optional[str]:
        """Sanitize user input: strip HTML tags, limit length, escape."""
        if not value:
            return None
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', str(value))
        # Escape HTML entities
        clean = html.escape(clean)
        # Limit length
        return clean[:max_length].strip() or None

    def _validate_email(email: str) -> bool:
        """Basic email validation."""
        if not email or len(email) > 254:
            return False
        # Simple regex for email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_phone(phone: Optional[str]) -> Optional[str]:
        """Validate and clean phone number."""
        if not phone:
            return None
        # Remove all non-digit characters except + at start
        clean = re.sub(r'[^\d+]', '', phone)
        if clean.startswith('+'):
            clean = '+' + re.sub(r'[^\d]', '', clean[1:])
        else:
            clean = re.sub(r'[^\d]', '', clean)
        # Basic length check (7-15 digits)
        digits = re.sub(r'[^\d]', '', clean)
        if len(digits) < 7 or len(digits) > 15:
            return None
        return clean[:20]

    @app.post("/api/leads")
    async def create_lead(lead_data: dict):
        """
        Save email signup from website.
        Input is sanitized to prevent XSS and injection attacks.
        """
        from src.db.models import Lead

        email = (lead_data.get("email") or "").strip().lower()
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Valid email required")

        # Sanitize all inputs
        phone = _validate_phone(lead_data.get("phone"))
        company = _sanitize_input(lead_data.get("company"), 100)
        role = _sanitize_input(lead_data.get("role"), 100)
        interest = _sanitize_input(lead_data.get("interest"), 500)
        timezone = _sanitize_input(lead_data.get("timezone"), 50)
        city = _sanitize_input(lead_data.get("city"), 100)
        session_id = _sanitize_input(lead_data.get("session_id"), 64)

        async with get_db_session() as session:
            # Check if already exists
            from sqlalchemy import select
            existing = await session.execute(
                select(Lead).where(Lead.email == email)
            )
            lead = existing.scalar_one_or_none()

            if lead:
                # Update existing lead with any new info
                if phone:
                    lead.phone = phone
                if company:
                    lead.company = company
                if role:
                    lead.role = role
                if interest:
                    lead.interest = interest
                if timezone:
                    lead.timezone = timezone
                if city:
                    lead.city = city
            else:
                # Create new lead
                lead = Lead(
                    email=email,
                    phone=phone,
                    company=company,
                    role=role,
                    interest=interest,
                    timezone=timezone,
                    city=city,
                    session_id=session_id,
                    source="website"
                )
                session.add(lead)

            await session.commit()
            return {"success": True, "message": "Subscribed!"}

    @app.post("/api/leads/partial")
    async def save_partial_lead(lead_data: dict):
        """
        Save partial lead data (just email from step 1).
        Input is sanitized to prevent XSS and injection attacks.
        """
        from src.db.models import Lead

        email = (lead_data.get("email") or "").strip().lower()
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Valid email required")

        # Sanitize inputs
        timezone = _sanitize_input(lead_data.get("timezone"), 50)
        city = _sanitize_input(lead_data.get("city"), 100)
        session_id = _sanitize_input(lead_data.get("session_id"), 64)

        async with get_db_session() as session:
            from sqlalchemy import select
            existing = await session.execute(
                select(Lead).where(Lead.email == email)
            )
            lead = existing.scalar_one_or_none()

            if not lead:
                lead = Lead(
                    email=email,
                    timezone=timezone,
                    city=city,
                    session_id=session_id,
                    source="website"
                )
                session.add(lead)
                await session.commit()

            return {"success": True}

    # =========================================================================
    # Email Webhook (Resend inbound)
    # =========================================================================

    @app.post("/api/webhooks/email/inbound")
    async def email_inbound_webhook(request: Request):
        """Receive inbound emails from Resend webhook.

        Classifies intent via Grok, persists to data/email_inbox.json,
        and queues auto-replies when appropriate.
        """
        import os

        # Validate webhook secret if configured
        webhook_secret = os.environ.get("EMAIL_WEBHOOK_SECRET", "")
        if webhook_secret:
            auth_header = request.headers.get("authorization", "")
            if auth_header != f"Bearer {webhook_secret}":
                raise HTTPException(status_code=401, detail="Invalid webhook secret")

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Delegate to the full classification + persistence pipeline
        try:
            from src.mailer.inbox import process_inbound_email
            result = await process_inbound_email(body)
            logger.info(
                f"Email webhook processed: id={result['id']} "
                f"intent={result['intent']} auto_reply={result['auto_reply']}"
            )
            return {
                "status": "received",
                "id": result["id"],
                "intent": result["intent"],
                "auto_reply": result["auto_reply"],
            }
        except Exception as exc:
            # Fallback: store raw if classification pipeline fails
            logger.error(f"Email classification pipeline error: {exc}")
            import uuid as _uuid
            from datetime import datetime as _dt

            inbox_path = Path("data/email_inbox.json")
            inbox_path.parent.mkdir(parents=True, exist_ok=True)
            inbox = []
            if inbox_path.exists():
                try:
                    inbox = json.loads(inbox_path.read_text())
                except Exception:
                    pass

            email_entry = {
                "id": str(_uuid.uuid4())[:8],
                "from": body.get("from", ""),
                "to": body.get("to", ""),
                "subject": body.get("subject", ""),
                "text": body.get("text", ""),
                "html": body.get("html", ""),
                "received_at": _dt.now().isoformat(),
                "intent": "unknown",
                "read": False,
                "raw_headers": body.get("headers", {}),
            }
            inbox.append(email_entry)
            inbox = inbox[-200:]
            inbox_path.write_text(json.dumps(inbox, indent=2))

            return {"status": "received", "id": email_entry["id"], "intent": "unknown"}

    @app.post("/api/webhooks/email")
    async def email_webhook_alias(request: Request):
        """Alias for /api/webhooks/email/inbound -- same pipeline."""
        return await email_inbound_webhook(request)

    # =========================================================================
    # Static File Serving (Website)
    # =========================================================================

    @app.get("/")
    async def serve_index():
        """Serve the main website with Cloudflare edge caching"""
        # Serve the full website (index.html) as the landing page
        index_path = Path(__file__).parent.parent / "web" / "index.html"
        if index_path.exists():
            # Cache for 5 min in browser, 1 hour at Cloudflare edge
            # This reduces load on Chromebook significantly
            return FileResponse(
                index_path,
                headers={
                    "Cache-Control": "public, max-age=300, s-maxage=3600",
                    "CDN-Cache-Control": "public, max-age=3600",
                }
            )
        # Fallback to dashboard
        dashboard_path = Path(__file__).parent.parent / "web" / "dashboard.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        return {"message": "Grok & Mon API", "docs": "/docs"}

    @app.get("/dashboard")
    async def serve_dashboard():
        """Serve the monitoring dashboard"""
        dashboard_path = Path(__file__).parent.parent / "web" / "dashboard.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        raise HTTPException(status_code=404, detail="Dashboard not found")

    @app.get("/hud")
    async def serve_hud():
        """Serve the Irie Bloomberg HUD dashboard"""
        hud_path = Path(__file__).parent.parent / "web" / "hud.html"
        if hud_path.exists():
            return FileResponse(hud_path)
        raise HTTPException(status_code=404, detail="HUD not found")

    @app.get("/hud-lite")
    async def serve_hud_lite():
        """Serve lightweight kiosk HUD for low-power devices"""
        hud_path = Path(__file__).parent.parent / "web" / "hud-lite.html"
        if hud_path.exists():
            return FileResponse(hud_path)
        raise HTTPException(status_code=404, detail="HUD lite not found")

    @app.get("/telegram")
    async def redirect_telegram():
        """Redirect to the Ganja Mon Telegram group"""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="https://t.me/ganjamonai", status_code=301)

    @app.get("/voice")
    async def serve_voice_dashboard(request: Request):
        """Serve the voice control dashboard (localhost only)"""
        # Only allow localhost access
        client_host = request.client.host if request.client else None
        if client_host not in ("127.0.0.1", "localhost", "::1"):
            raise HTTPException(status_code=403, detail="Voice dashboard is localhost only")
        voice_path = Path(__file__).parent.parent / "web" / "voice.html"
        if voice_path.exists():
            return FileResponse(voice_path)
        raise HTTPException(status_code=404, detail="Voice dashboard not found")

    @app.get("/irie")
    @app.get("/iriemilady")
    async def serve_irie_milady():
        """Serve the Irie Milady NFT collection landing page"""
        irie_path = Path(__file__).parent.parent / "web" / "iriemilady.html"
        if irie_path.exists():
            return FileResponse(
                irie_path,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            )
        raise HTTPException(status_code=404, detail="Irie Milady page not found")

    @app.get("/{path:path}")
    async def serve_static(path: str):
        """Serve static files or fall back to index"""
        web_dir = Path(__file__).parent.parent / "web"

        # SECURITY: Prevent path traversal attacks
        # Reject paths containing .. or starting with /
        if ".." in path or path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid path")

        file_path = (web_dir / path).resolve()

        # SECURITY: Ensure resolved path is within web_dir
        try:
            file_path.relative_to(web_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

        if file_path.exists() and file_path.is_file():
            # Set cache headers based on file type
            suffix = file_path.suffix.lower()
            if suffix in {'.js', '.css', '.woff', '.woff2', '.ttf', '.eot'}:
                # Long cache for static assets (1 year)
                cache_headers = {"Cache-Control": "public, max-age=31536000, immutable"}
            elif suffix in {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp'}:
                # Long cache for images (1 week)
                cache_headers = {"Cache-Control": "public, max-age=604800"}
            elif suffix == '.html':
                # Short cache for HTML (5 min browser, 1 hour edge)
                cache_headers = {"Cache-Control": "public, max-age=300, s-maxage=3600"}
            else:
                # Default: moderate cache (1 hour)
                cache_headers = {"Cache-Control": "public, max-age=3600"}
            return FileResponse(file_path, headers=cache_headers)

        # Fall back to index for SPA routing
        index_path = web_dir / "index.html"
        if index_path.exists():
            return FileResponse(
                index_path,
                headers={"Cache-Control": "public, max-age=300, s-maxage=3600"}
            )

        raise HTTPException(status_code=404, detail="Not found")


# =============================================================================
# Default Application Instance
# =============================================================================

app = create_app()


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
