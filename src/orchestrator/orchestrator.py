"""
Grok & Mon Orchestrator
=======================

The main control loop that ties everything together:
1. Poll sensors on a regular interval
2. Store readings in database
3. Call Grok AI for decisions every 2 hours
4. Execute AI actions through safety layer
5. Log everything for the website

Based on SOLTOMATO's 2-hour decision cycle pattern.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, time
from typing import Optional
import signal
from pathlib import Path

# Load environment variables (critical for API keys in subprocess)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


def safe_print(msg: str):
    """Print with Windows-safe encoding and flush"""
    import sys
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        # Replace non-ASCII characters with ASCII equivalents
        ascii_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(ascii_msg, flush=True)
    sys.stdout.flush()

from src.db.connection import init_database, close_database, get_db_session
from src.db.repository import GrowRepository
from src.db.models import GrowthStage
from src.hardware import MockSensorHub, MockActuatorHub, MockCameraHub, GoveeSensorHub, KasaActuatorHub, USBWebcam, get_logitech_index, TapoActuatorHub
from src.hardware.ecowitt import EcowittSoilHub, MockEcowittSoilHub
from src.safety import SafetyGuardian, SafeActuatorHub, DarkPeriodConfig
from src.safety.guardian import set_growth_stage
from src.ai import GrokBrain, ToolExecutor

try:
    from src.scheduling import PhotoperiodScheduler, PhotoperiodConfig
    SCHEDULING_AVAILABLE = True
except ImportError:
    SCHEDULING_AVAILABLE = False
    PhotoperiodScheduler = None
    PhotoperiodConfig = None

try:
    from src.social import TwitterClient, format_daily_update, format_ai_decision
    SOCIAL_AVAILABLE = True
except ImportError:
    SOCIAL_AVAILABLE = False
    TwitterClient = None

try:
    from src.notifications import AlertManager, alert_temperature_critical, alert_human_action_required
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    AlertManager = None

# Timeouts to prevent persistent stalls
SENSOR_READ_TIMEOUT = 30  # Max time to wait for sensor read
DB_OPERATION_TIMEOUT = 10  # Max time to wait for database operations
STALL_DETECTION_THRESHOLD = 300  # Warn if no successful poll for 5 minutes
RECONNECT_THRESHOLD = 3  # Reconnect after this many consecutive failures
MAX_RECONNECT_ATTEMPTS = 3  # Max reconnection attempts before giving up
SENSOR_STALE_THRESHOLD = 300  # Reject sensor readings older than 5 minutes


class GrokMonOrchestrator:
    """
    Main orchestrator for the Grok & Mon grow system.

    Coordinates sensors, AI, actuators, and database.
    """

    def __init__(
        self,
        sensor_interval_seconds: int = 60,
        ai_interval_seconds: int = 7200,  # 2 hours
        plant_name: str = "Mon"
    ):
        self.sensor_interval = sensor_interval_seconds
        self.ai_interval = ai_interval_seconds
        self.plant_name = plant_name

        # Components (initialized in start())
        self.sensors: Optional[MockSensorHub] = None
        self.soil_sensors: Optional[EcowittSoilHub] = None  # Ecowitt WH51
        self.actuators: Optional[MockActuatorHub] = None  # Kasa plugs
        self.tapo_actuators: Optional[TapoActuatorHub] = None  # Tapo plugs (grow light)
        self.camera: Optional[MockCameraHub] = None
        self.guardian: Optional[SafetyGuardian] = None
        self.safe_actuators: Optional[SafeActuatorHub] = None
        self.brain: Optional[GrokBrain] = None
        self.tool_executor: Optional[ToolExecutor] = None
        self.photoperiod: Optional[PhotoperiodScheduler] = None
        self.twitter: Optional[TwitterClient] = None
        self.alerts: Optional[AlertManager] = None

        # Unified context aggregator (cross-system awareness)
        try:
            from src.brain.unified_context import UnifiedContextAggregator
            self.unified_ctx = UnifiedContextAggregator()
        except Exception:
            self.unified_ctx = None

        # Episodic memory (SOLTOMATO pattern — auto-persists to data/episodic_memory.json)
        from src.brain.memory import EpisodicMemory
        self.memory = EpisodicMemory(
            max_entries=100,
            persist_path=str(Path(__file__).parent.parent / "data" / "episodic_memory.json"),
        )

        # State
        self._running = False
        self._last_ai_decision = None
        self._sensor_task = None
        self._ai_task = None
        self._last_successful_poll: Optional[datetime] = None
        self._consecutive_failures = 0
        self._reconnect_attempts = 0

        # Reactive trigger queue — sensor anomalies push here, AI loop pulls
        self._reactive_queue: asyncio.Queue = asyncio.Queue(maxsize=5)
        self._last_reactive_decision: Optional[datetime] = None
        self._reactive_cooldown_seconds = 600  # 10 min between reactive cycles

        # Mock sensor tracking (for AI context)
        self._using_mock_sensors = False
        self._using_mock_actuators = False
        self._using_mock_soil = False
        self._last_sensor_timestamp: Optional[datetime] = None

    async def start(self):
        """Initialize and start the orchestrator"""
        safe_print(f"[*] Starting Grok & Mon Orchestrator for {self.plant_name}...")

        # Register with watchdog for liveness tracking
        from src.core.watchdog import get_watchdog
        wd = get_watchdog()
        wd.register("orchestrator", threshold=300)
        wd.register("sensor_loop", threshold=180)
        wd.register("ai_loop", threshold=3600)

        # Initialize database
        await init_database()

        # Initialize hardware - use real sensors!
        try:
            self.sensors = GoveeSensorHub()
            connected = await self.sensors.connect()
            if connected:
                safe_print("[OK] Using real Govee sensors")
            else:
                raise ConnectionError("Govee sensors failed to connect")
        except Exception as e:
            safe_print(f"[WARN] Govee sensors failed ({e}), using mock")
            self.sensors = MockSensorHub()
            self._using_mock_sensors = True

        # Initialize Ecowitt soil sensors (WH51 via GW1100 gateway)
        try:
            ecowitt_ip = os.environ.get("ECOWITT_GATEWAY_IP")
            if ecowitt_ip:
                self.soil_sensors = EcowittSoilHub(ecowitt_ip)
                healthy = await self.soil_sensors.health_check()
                if healthy:
                    safe_print(f"[OK] Ecowitt soil sensors connected ({ecowitt_ip})")
                else:
                    safe_print(f"[WARN] Ecowitt gateway not responding at {ecowitt_ip}")
                    self.soil_sensors = MockEcowittSoilHub(ecowitt_ip)
            else:
                safe_print("[WARN] ECOWITT_GATEWAY_IP not set, soil sensors disabled")
                self.soil_sensors = None
        except Exception as e:
            safe_print(f"[WARN] Ecowitt setup failed ({e}), using mock")
            self.soil_sensors = MockEcowittSoilHub("192.168.1.100")
            self._using_mock_soil = True

        try:
            # Load Kasa device IPs from environment
            # Actual mapping (identified via power cycling):
            #   .181 = co2_solenoid (Vivosun regulator)
            #   .129 = water_pump (CAREFUL - powerful pump!)
            #   .203 = exhaust_fan (inline fan)
            #   .133 = circulation_fan
            kasa_ips = {}

            co2_ip = os.environ.get("KASA_CO2_SOLENOID_IP")
            pump_ip = os.environ.get("KASA_WATER_PUMP_IP")
            exhaust_ip = os.environ.get("KASA_EXHAUST_FAN_IP")
            circ_ip = os.environ.get("KASA_CIRC_FAN_IP")
            light_ip = os.environ.get("KASA_GROW_LIGHT_IP")

            if co2_ip:
                kasa_ips["co2_solenoid"] = co2_ip
            if pump_ip:
                kasa_ips["water_pump"] = pump_ip
            if exhaust_ip:
                kasa_ips["exhaust_fan"] = exhaust_ip
            if circ_ip:
                kasa_ips["circulation_fan"] = circ_ip
            if light_ip:
                kasa_ips["grow_light"] = light_ip

            if kasa_ips:
                self.actuators = KasaActuatorHub(kasa_ips)
                connected = await self.actuators.connect()
                if connected:
                    safe_print(f"[OK] Using real Kasa actuators ({len(kasa_ips)} plugs)")
                else:
                    raise ConnectionError("Kasa plugs failed to connect")
            else:
                safe_print("[WARN] No Kasa plug IPs configured in .env")
                self.actuators = MockActuatorHub()
        except Exception as e:
            safe_print(f"[WARN] Kasa actuators failed ({e}), using mock")
            self.actuators = MockActuatorHub()
            self._using_mock_actuators = True

        # Initialize Tapo actuators (grow light)
        try:
            tapo_user = os.environ.get("TAPO_USERNAME")
            tapo_pass = os.environ.get("TAPO_PASSWORD")
            tapo_light = os.environ.get("TAPO_GROW_LIGHT_IP")

            if tapo_user and tapo_pass and tapo_light:
                self.tapo_actuators = TapoActuatorHub()
                connected = await self.tapo_actuators.connect()
                if connected:
                    safe_print(f"[OK] Tapo grow light connected ({tapo_light})")
                else:
                    safe_print("[WARN] Tapo grow light failed to connect")
                    self.tapo_actuators = None
            else:
                safe_print("[WARN] Tapo not configured (TAPO_USERNAME/PASSWORD/GROW_LIGHT_IP)")
                self.tapo_actuators = None
        except Exception as e:
            safe_print(f"[WARN] Tapo actuators failed ({e})")
            self.tapo_actuators = None

        try:
            # Get Logitech camera index (defaults to 2 on Chromebook)
            camera_index = get_logitech_index()
            safe_print(f"[*] Trying webcam at device index {camera_index}")
            self.camera = USBWebcam(device_index=camera_index)
            # Test capture to verify camera works, then release it for other processes
            test_capture = await self.camera.capture(release_after=True)
            if test_capture:
                safe_print("[OK] Using USB webcam (verified)")
            else:
                raise ConnectionError("Webcam test capture failed")
        except Exception as e:
            safe_print(f"[WARN] Webcam failed ({e}), using mock")
            self.camera = MockCameraHub()

        if hasattr(self.actuators, 'link_sensors') and isinstance(self.sensors, MockSensorHub):
            self.actuators.link_sensors(self.sensors)

        # Initialize safety layer
        # For 24/0 veg (clone phase): NO dark period
        # Will switch to 12/12 when transitioning to flower
        self.guardian = SafetyGuardian(
            dark_config=DarkPeriodConfig(
                enabled=False,  # Disabled for 24/0 veg - lights always on
                hours_dark=0,   # No dark period during clone/veg
            )
        )
        self.safe_actuators = SafeActuatorHub(self.actuators, self.guardian)

        # Initialize AI
        async with get_db_session() as session:
            repo = GrowRepository(session)
            # Pass Govee sensors for humidifier control (H7145 is cloud-controlled)
            self.tool_executor = ToolExecutor(
                self.safe_actuators,
                self.camera,
                repo,
                govee_sensors=self.sensors if hasattr(self.sensors, 'has_humidifier') else None
            )

        self.brain = GrokBrain(
            tool_executor=self.tool_executor,
            plant_name=self.plant_name
        )

        # Episodic memory auto-loads from disk via the new persistence layer
        safe_print(f"[OK] Episodic memory: {len(self.memory.entries)} entries loaded from disk")

        # Initialize photoperiod scheduler (if APScheduler available)
        if SCHEDULING_AVAILABLE:
            async def light_callback(intensity: int):
                """Callback to control grow light through Tapo (or Kasa fallback)"""
                on = intensity > 0
                success = False
                if self.tapo_actuators:
                    success = await self.tapo_actuators.set_device("grow_light", on)
                if not success:
                    # Tapo failed or not available — try Kasa fallback
                    try:
                        await self.safe_actuators.set_grow_light(on)
                        success = True
                    except Exception as e:
                        safe_print(f"[ERR] Light callback failed (both Tapo and Kasa): {e}")
                if not success:
                    safe_print(f"[ERR] LIGHT {'ON' if on else 'OFF'} COMMAND FAILED - manual intervention needed")

            async def safety_callback(action: str) -> bool:
                """Check if light action is safe"""
                if action == "lights_on" and self.guardian.dark_config.is_dark_period():
                    return False  # Don't turn on lights during forced dark period
                return True

            self.photoperiod = PhotoperiodScheduler(
                light_callback=light_callback,
                safety_callback=safety_callback,
            )

            # Load photoperiod from database based on current growth stage
            # NOTE: sunrise_minutes=0 to avoid 30-min startup delay
            photoperiod_config = PhotoperiodConfig(
                light_on_hour=6, hours_on=18, hours_off=6,
                sunrise_minutes=0, sunset_minutes=0
            )
            photoperiod_name = "18/6 (vegetative)"

            try:
                async with get_db_session() as session:
                    repo = GrowRepository(session)
                    stage_data = await repo.get_current_stage()
                    if stage_data:
                        current_stage = stage_data.get("current_stage", "vegetative")
                        db_photoperiod = stage_data.get("photoperiod", "18/6")

                        # Map growth stage to photoperiod config
                        if current_stage in ["flowering", "late_flower"]:
                            photoperiod_config = PhotoperiodConfig(
                                light_on_hour=6, hours_on=12, hours_off=12,
                                sunrise_minutes=0, sunset_minutes=0
                            )
                            photoperiod_name = "12/12 (flowering)"
                        elif current_stage == "transition":
                            photoperiod_config = PhotoperiodConfig(
                                light_on_hour=6, hours_on=12, hours_off=12,
                                sunrise_minutes=0, sunset_minutes=0
                            )
                            photoperiod_name = "12/12 (transition)"
                        elif db_photoperiod == "24/0":
                            # Clone/early veg - 24 hour light
                            photoperiod_config = PhotoperiodConfig(
                                light_on_hour=0, hours_on=24, hours_off=0,
                                sunrise_minutes=0, sunset_minutes=0
                            )
                            photoperiod_name = "24/0 (clone)"
                        elif db_photoperiod == "20/4":
                            photoperiod_config = PhotoperiodConfig(
                                light_on_hour=4, hours_on=20, hours_off=4,
                                sunrise_minutes=0, sunset_minutes=0
                            )
                            photoperiod_name = "20/4 (vegetative)"
                        # else: keep default 18/6

                        safe_print(f"[DB] Loaded growth stage: {current_stage}, photoperiod: {db_photoperiod}")
                        self._sync_dark_period_config(current_stage, db_photoperiod)
            except Exception as e:
                safe_print(f"[WARN] Could not load stage from DB ({e}), using default 18/6")

            await self.photoperiod.start(photoperiod_config)
            safe_print(f"[OK] Photoperiod scheduler active: {photoperiod_name}")
        else:
            safe_print("[WARN] APScheduler not installed - photoperiod automation disabled")

        # Initialize Twitter client for social posting
        if SOCIAL_AVAILABLE:
            self.twitter = TwitterClient()
            safe_print("[OK] Twitter client initialized")
        else:
            safe_print("[WARN] Tweepy not installed - social posting disabled")

        # Initialize alert manager for notifications
        if NOTIFICATIONS_AVAILABLE:
            self.alerts = AlertManager()
            safe_print("[OK] Alert manager initialized (Discord/Telegram)")
        else:
            safe_print("[WARN] Notifications not available")

        self._running = True

        # Start background tasks
        self._sensor_task = asyncio.create_task(self._sensor_loop())
        self._ai_task = asyncio.create_task(self._ai_loop())
        self._reactive_task = asyncio.create_task(self._reactive_loop())
        self._light_watchdog_task = asyncio.create_task(self._light_watchdog_loop())

        # Start unified subsystems (signals, learning, engagement)
        unified_tasks = await self._start_unified_subsystems()

        safe_print("[OK] Orchestrator started!")
        safe_print(f"   - Sensor polling: every {self.sensor_interval}s")
        safe_print(f"   - AI decisions: every {self.ai_interval}s ({self.ai_interval // 3600}h)")
        safe_print(f"   - Reactive decisions: anomaly-driven (10 min cooldown)")

        # Wait for tasks
        try:
            all_tasks = [self._sensor_task, self._ai_task, self._reactive_task, self._light_watchdog_task] + unified_tasks
            await asyncio.gather(*all_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            print("Orchestrator tasks cancelled")

    def _queue_decision_ipc(self, decision: dict, sensor_data: dict, image_b64: str = None):
        """Write a decision to the file-based IPC queue for the social daemon process."""
        ipc_file = Path(__file__).parent.parent / "data" / "social_decision_queue.jsonl"
        entry = json.dumps({
            "decision": decision,
            "sensor_data": sensor_data,
            "image_b64": image_b64,
            "timestamp": datetime.now().isoformat(),
        })
        try:
            ipc_file.parent.mkdir(parents=True, exist_ok=True)
            with open(ipc_file, "a") as f:
                f.write(entry + "\n")
        except Exception as e:
            safe_print(f"[WARN] Failed to write decision IPC: {e}")

    def _sync_dark_period_config(self, growth_stage: str, photoperiod: str) -> None:
        """Enable dark-period protection when in flowering/12-12."""
        if not self.guardian:
            return

        stage = (growth_stage or "").lower()
        photo = (photoperiod or "").strip()
        should_enable = stage in {"transition", "flowering", "late_flower"} or photo.startswith("12")

        if should_enable:
            self.guardian.dark_config.enabled = True
            self.guardian.dark_config.hours_dark = 12
            self.guardian.dark_config.dark_start = time(18, 0)
            self.guardian.dark_config.dark_end = time(6, 0)
        else:
            self.guardian.dark_config.enabled = False
            self.guardian.dark_config.hours_dark = 0

    async def stop(self):
        """Stop the orchestrator gracefully"""
        safe_print("[*] Stopping orchestrator...")
        self._running = False

        if self._sensor_task:
            self._sensor_task.cancel()
        if self._ai_task:
            self._ai_task.cancel()

        # Stop photoperiod scheduler
        if self.photoperiod:
            await self.photoperiod.stop()

        # Save learning state
        try:
            from src.learning.grimoire import save_all_grimoires
            save_all_grimoires()
            safe_print("[OK] Grimoires saved")
        except Exception:
            pass

        # Episodic memory auto-saves on every store() call — no manual save needed
        safe_print(f"[OK] Episodic memory: {len(self.memory.entries)} entries (auto-persisted)")

        # Stop outbound A2A daemon
        if hasattr(self, '_a2a_daemon') and self._a2a_daemon:
            await self._a2a_daemon.stop()
            safe_print("[OK] Outbound A2A daemon stopped")

        await close_database()
        safe_print("[OK] Orchestrator stopped")

    async def _light_watchdog_loop(self):
        """
        Periodically verify grow light matches photoperiod schedule.

        Catches stale Tapo connections, missed CronTrigger fires, and
        any other silent failures that leave the light in the wrong state.
        Runs every 5 minutes.
        """
        await asyncio.sleep(120)  # Let system initialize
        safe_print("[OK] Light watchdog started (5-min verification cycle)")

        while self._running:
            try:
                # Only check if photoperiod scheduler is active
                if not self.photoperiod or not self.photoperiod.is_running:
                    await asyncio.sleep(300)
                    continue

                # Determine expected state from schedule
                expected_on = not self.photoperiod.is_dark_period()

                # Check actual Tapo light state
                actual_on = None
                if self.tapo_actuators:
                    try:
                        tapo_state = await asyncio.wait_for(
                            self.tapo_actuators.get_state(),
                            timeout=10.0
                        )
                        actual_on = tapo_state.grow_light
                    except Exception as e:
                        safe_print(f"[WATCHDOG] Failed to read Tapo state: {e}")

                if actual_on is not None and actual_on != expected_on:
                    safe_print(
                        f"[WATCHDOG] Light mismatch! Expected={'ON' if expected_on else 'OFF'}, "
                        f"Actual={'ON' if actual_on else 'OFF'}. Correcting..."
                    )
                    success = False
                    if self.tapo_actuators:
                        success = await self.tapo_actuators.set_device("grow_light", expected_on)
                    if not success:
                        try:
                            await self.safe_actuators.set_grow_light(expected_on)
                            success = True
                        except Exception:
                            pass

                    if success:
                        safe_print(f"[WATCHDOG] Light corrected to {'ON' if expected_on else 'OFF'}")
                    else:
                        safe_print("[WATCHDOG] CRITICAL: Failed to correct light state!")

            except asyncio.CancelledError:
                break
            except Exception as e:
                safe_print(f"[WATCHDOG] Error: {e}")

            await asyncio.sleep(300)  # 5 minutes

    async def _reconnect_hardware(self) -> bool:
        """
        Attempt to reconnect failed hardware.
        Returns True if at least one component reconnected.
        """
        safe_print("[*] Attempting hardware reconnection...")
        reconnected = False

        # Reconnect Govee sensors
        try:
            if hasattr(self.sensors, 'connect'):
                await asyncio.wait_for(self.sensors.connect(), timeout=SENSOR_READ_TIMEOUT)
                safe_print("[OK] Govee sensors reconnected")
                reconnected = True
        except asyncio.TimeoutError:
            safe_print("[WARN] Govee reconnect timeout")
        except Exception as e:
            safe_print(f"[WARN] Govee reconnect failed: {e}")

        # Reconnect Kasa actuators
        try:
            if hasattr(self.actuators, 'connect'):
                await asyncio.wait_for(self.actuators.connect(), timeout=SENSOR_READ_TIMEOUT)
                safe_print("[OK] Kasa actuators reconnected")
                reconnected = True
        except asyncio.TimeoutError:
            safe_print("[WARN] Kasa reconnect timeout")
        except Exception as e:
            safe_print(f"[WARN] Kasa reconnect failed: {e}")

        # Reconnect Ecowitt soil sensors
        if self.soil_sensors:
            try:
                if hasattr(self.soil_sensors, 'health_check'):
                    healthy = await asyncio.wait_for(
                        self.soil_sensors.health_check(),
                        timeout=SENSOR_READ_TIMEOUT
                    )
                    if healthy:
                        safe_print("[OK] Ecowitt sensors healthy")
                        reconnected = True
            except asyncio.TimeoutError:
                safe_print("[WARN] Ecowitt health check timeout")
            except Exception as e:
                safe_print(f"[WARN] Ecowitt check failed: {e}")

        return reconnected

    async def _start_unified_subsystems(self) -> list:
        """Start Phase 2-4 subsystems: signals, learning, engagement."""
        tasks = []

        # Signal sources handled by trading agent subprocess (not duplicated here)

        # Phase 3: Learning subsystems
        try:
            from src.learning.regime_detector import get_regime_detector
            detector = get_regime_detector()
            tasks.append(asyncio.create_task(self._regime_detection_loop(detector)))
            safe_print("[OK] Market regime detector started")
        except Exception as e:
            safe_print(f"[WARN] Regime detector failed: {e}")

        try:
            from src.learning.grimoire import save_all_grimoires
            # Grimoires auto-load; periodic save handled in learning loop
            safe_print("[OK] Grimoire memory system loaded")
        except Exception as e:
            safe_print(f"[WARN] Grimoire system failed: {e}")

        # Phase 3: Learning loop (compound learning + strategy tracking)
        tasks.append(asyncio.create_task(self._learning_loop()))
        safe_print("[OK] Learning loop started (compound learning + strategy tracking)")

        # Phase 4: Engagement — handled by separate social daemon process (run.py all).
        # Do NOT start EngagementEngine here; it duplicates the daemon's posting loops
        # and creates independent rate-limit tracking, risking double-posts.
        # AI decisions are handed off to the daemon via file-based IPC (see _queue_decision_ipc).

        # Outbound A2A daemon — proactively calls other agents every 30 min
        try:
            from src.a2a.outbound_daemon import get_outbound_daemon
            self._a2a_daemon = get_outbound_daemon()
            await self._a2a_daemon.start()
            safe_print("[OK] Outbound A2A daemon started (30-min outreach rounds)")
        except Exception as e:
            self._a2a_daemon = None
            safe_print(f"[WARN] Outbound A2A daemon failed to start: {e}")

        return tasks

    async def _regime_detection_loop(self, detector):
        """Periodically check market regime (every 30 min)."""
        await asyncio.sleep(30)  # Initial delay
        while self._running:
            try:
                await detector._detect()
            except Exception as e:
                safe_print(f"[WARN] Regime detection error: {e}")
            await asyncio.sleep(1800)  # 30 minutes

    async def _learning_loop(self):
        """Run learning subsystems periodically."""
        await asyncio.sleep(120)  # Let system warm up 2 min
        cycle = 0
        while self._running:
            try:
                cycle += 1

                # Every 6 cycles (~3h): save grimoires to disk
                if cycle % 6 == 0:
                    try:
                        from src.learning.grimoire import save_all_grimoires
                        save_all_grimoires()
                    except Exception as e:
                        safe_print(f"[WARN] Grimoire save error: {e}")

                # Every 12 cycles (~6h): run compound learning + grow pattern extraction
                if cycle % 12 == 0:
                    try:
                        from src.learning.compound_learning import get_compound_learning
                        cl = get_compound_learning()
                        cl.decay_promoted(rate=0.98)
                    except Exception as e:
                        safe_print(f"[WARN] Compound learning error: {e}")

                    # Extract grow stage patterns from accumulated decisions
                    try:
                        from src.learning.grow_learning import get_grow_learning
                        gl = get_grow_learning()
                        for stage in ["seedling", "vegetative", "transition", "flowering", "late_flower"]:
                            pattern = gl.extract_stage_patterns(stage)
                            if pattern:
                                safe_print(f"[LEARN] Grow pattern for {stage}: temp={pattern.optimal_temp:.1f}, RH={pattern.optimal_humidity:.0f}%, confidence={pattern.confidence:.2f}")
                    except Exception as e:
                        safe_print(f"[WARN] Grow pattern extraction error: {e}")

                    # Auto-review engine: generate periodic grow review
                    try:
                        from src.review.engine import ReviewEngine, ReviewType
                        async with get_db_session() as session:
                            repo = GrowRepository(session)
                            engine = ReviewEngine(repo)
                            review = await engine.generate_review(review_type=ReviewType.DAILY)
                            if review:
                                review_path = Path(__file__).parent.parent / "data" / "historical_review.json"
                                with open(review_path, "w") as f:
                                    json.dump(review, f, indent=2, default=str)
                                safe_print(f"[REVIEW] Auto-review generated: grade={review.get('grade', 'N/A')}")
                    except Exception as e:
                        safe_print(f"[WARN] Auto-review engine error: {e}")

                # ERC-8004 reputation publishing (Pattern #27 — on-chain proof-of-work)
                # Every 24 learning cycles (~12h): publish metrics to ReputationRegistry
                if cycle % 24 == 0:
                    try:
                        from src.blockchain.reputation_publisher import run_publish_cycle
                        publish_results = run_publish_cycle()
                        if publish_results:
                            safe_print(f"[REPUTATION] Published {len(publish_results)} on-chain signals")
                        else:
                            safe_print("[REPUTATION] No signals published (check balance/RPC)")
                    except Exception as e:
                        safe_print(f"[WARN] Reputation publish failed: {e}")

                # Every 24 cycles (~12h): check for stalled goals
                if cycle % 24 == 0:
                    try:
                        from src.learning.strategy_tracker import get_strategy_tracker
                        tracker = get_strategy_tracker()
                        stalled = tracker.get_stalled_goals()
                        if stalled:
                            safe_print(f"[ALERT] Stalled goals: {[g.goal_id for g in stalled]}")
                    except Exception as e:
                        safe_print(f"[WARN] Strategy tracker error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                safe_print(f"[ERR] Learning loop error: {e}")

            await asyncio.sleep(1800)  # 30 minutes per cycle

    async def _sensor_loop(self):
        """Background task: poll sensors and store readings"""
        safe_print("[*] Starting sensor polling loop...")

        while self._running:
            # Watchdog heartbeat
            from src.core.watchdog import get_watchdog
            get_watchdog().heartbeat("sensor_loop")

            poll_start = datetime.now()
            try:
                # Read all sensors (Govee for temp/humidity/CO2) with circuit breaker + timeout
                try:
                    from src.core.circuit_breaker import get_breaker
                    govee_breaker = get_breaker("govee_api")
                    async with govee_breaker:
                        reading = await asyncio.wait_for(
                            self.sensors.read_all(),
                            timeout=SENSOR_READ_TIMEOUT
                        )
                except asyncio.TimeoutError:
                    safe_print(f"[WARN] Sensor read timeout (>{SENSOR_READ_TIMEOUT}s)")
                    self._consecutive_failures += 1
                    await asyncio.sleep(10)
                    continue
                except Exception as cb_err:
                    if "Circuit open" in str(cb_err):
                        safe_print(f"[WARN] Govee circuit open: {cb_err}")
                        await asyncio.sleep(30)
                        continue
                    raise

                # Read Ecowitt soil sensors (WH51) and merge into reading
                soil_moisture_avg = reading.soil_moisture  # Default from Govee/mock
                soil_probe1 = reading.soil_moisture_probe1
                soil_probe2 = reading.soil_moisture_probe2

                if self.soil_sensors:
                    try:
                        from src.core.circuit_breaker import get_breaker
                        ecowitt_breaker = get_breaker("ecowitt_lan")
                        async with ecowitt_breaker:
                            soil_data = await asyncio.wait_for(
                                self.soil_sensors.read(),
                                timeout=SENSOR_READ_TIMEOUT
                            )
                        if soil_data and soil_data.sensors:
                            # Use Ecowitt data for soil moisture
                            soil_moisture_avg = soil_data.average_moisture
                            # Map individual probes if available
                            if len(soil_data.sensors) >= 1:
                                soil_probe1 = soil_data.sensors[0].moisture_percent
                            if len(soil_data.sensors) >= 2:
                                soil_probe2 = soil_data.sensors[1].moisture_percent
                    except asyncio.TimeoutError:
                        safe_print(f"[WARN] Ecowitt read timeout (>{SENSOR_READ_TIMEOUT}s)")
                    except Exception as e:
                        safe_print(f"[WARN] Ecowitt read failed: {e}")

                # Skip logging if core sensor data is unavailable
                core_values = (
                    reading.air_temp,
                    reading.humidity,
                    reading.vpd,
                    soil_moisture_avg,
                    reading.co2,
                    reading.leaf_temp_delta,
                )
                if any(v is None for v in core_values):
                    safe_print("[WARN] Sensor data missing core fields - skipping DB log")
                    self._consecutive_failures += 1
                    await asyncio.sleep(self.sensor_interval)
                    continue

                # Store in database with timeout protection
                try:
                    async with get_db_session() as session:
                        repo = GrowRepository(session)
                        await asyncio.wait_for(
                            repo.log_sensor_reading(
                                air_temp=reading.air_temp,
                                humidity=reading.humidity,
                                vpd=reading.vpd,
                                soil_moisture=soil_moisture_avg,
                                co2=reading.co2,
                                leaf_temp_delta=reading.leaf_temp_delta,
                                soil_moisture_probe1=soil_probe1,
                                soil_moisture_probe2=soil_probe2,
                            ),
                            timeout=DB_OPERATION_TIMEOUT
                        )

                        # Also get device state with timeout
                        try:
                            state = await asyncio.wait_for(
                                self.safe_actuators.get_state(),
                                timeout=SENSOR_READ_TIMEOUT
                            )

                            # Get grow_light state from Tapo if available
                            grow_light_on = state.grow_light  # Default from Kasa
                            if self.tapo_actuators:
                                try:
                                    tapo_state = await asyncio.wait_for(
                                        self.tapo_actuators.get_state(),
                                        timeout=5.0
                                    )
                                    grow_light_on = tapo_state.grow_light
                                except Exception:
                                    pass  # Keep Kasa state if Tapo fails

                            # Get humidifier state from Govee (H7145 is cloud-controlled)
                            humidifier_on = state.humidifier  # Default from Kasa
                            if hasattr(self.sensors, 'has_humidifier') and self.sensors.has_humidifier():
                                try:
                                    humidifier_status = await asyncio.wait_for(
                                        self.sensors.get_humidifier_status(),
                                        timeout=5.0
                                    )
                                    humidifier_on = humidifier_status.get('power_on', False)
                                except Exception:
                                    pass  # Keep Kasa state if Govee fails

                            await asyncio.wait_for(
                                repo.log_device_state(
                                    grow_light=grow_light_on,
                                    heat_mat=state.heat_mat,
                                    circulation_fan=state.circulation_fan,
                                    exhaust_fan=state.exhaust_fan,
                                    water_pump=state.water_pump,
                                    humidifier=humidifier_on,
                                    dehumidifier=state.dehumidifier,
                                ),
                                timeout=DB_OPERATION_TIMEOUT
                            )
                        except asyncio.TimeoutError:
                            safe_print(f"[WARN] Device state timeout - continuing without state log")
                except asyncio.TimeoutError:
                    safe_print(f"[WARN] Database write timeout (>{DB_OPERATION_TIMEOUT}s)")
                    self._consecutive_failures += 1
                    await asyncio.sleep(10)
                    continue

                # Poll succeeded - reset failure counter and update last poll time
                self._last_successful_poll = datetime.now()
                self._last_sensor_timestamp = datetime.now()  # Track for staleness check
                self._consecutive_failures = 0

                # Track sensor reliability for grow learning
                try:
                    from src.learning.grow_learning import get_grow_learning
                    gl = get_grow_learning()
                    if reading.air_temp is not None:
                        gl.record_sensor_reading("air_temp", reading.air_temp, 15.0, 40.0)
                    if reading.humidity is not None:
                        gl.record_sensor_reading("humidity", reading.humidity, 20.0, 90.0)
                    if reading.co2 is not None:
                        gl.record_sensor_reading("co2", reading.co2, 300.0, 2000.0)
                    if soil_moisture_avg is not None:
                        gl.record_sensor_reading("soil_moisture", soil_moisture_avg, 5.0, 80.0)
                except Exception:
                    pass  # Never crash sensor loop for learning

                # Compute hourly aggregates (for plant progress)
                # Run this once at the start of each hour
                current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
                if not hasattr(self, '_last_aggregate_hour') or self._last_aggregate_hour != current_hour:
                    try:
                        # Compute aggregate for the previous hour
                        prev_hour = current_hour - timedelta(hours=1)
                        stage_data = await repo.get_current_stage()
                        growth_stage = stage_data.get("current_stage", "vegetative") if stage_data else "vegetative"
                        aggregate = await repo.compute_hourly_aggregate(prev_hour, growth_stage=growth_stage)
                        if aggregate:
                            await session.commit()
                            safe_print(f"[OK] Computed hourly aggregate for {prev_hour.strftime('%H:%M')}")
                        self._last_aggregate_hour = current_hour
                    except Exception as e:
                        safe_print(f"[WARN] Failed to compute hourly aggregate: {e}")

                # Check environmental safety
                safety_check = self.guardian.check_environment(
                    temp=reading.air_temp,
                    humidity=reading.humidity,
                    co2=reading.co2,
                    vpd=reading.vpd
                )

                if not safety_check["ok"]:
                    safe_print(f"[WARN] Safety alert: {safety_check['critical']}")

                    # Send critical notification
                    if self.alerts and NOTIFICATIONS_AVAILABLE:
                        for critical in safety_check.get("critical", []):
                            await self.alerts.critical(
                                "Safety Alert!",
                                critical,
                                temperature=f"{reading.air_temp:.1f}F",
                                humidity=f"{reading.humidity:.0f}%",
                                co2=f"{reading.co2} ppm",
                            )

                    # Execute emergency actions
                    for action in safety_check["actions"]:
                        try:
                            await self.safe_actuators.set_device(
                                action["device"],
                                action["state"]
                            )
                            safe_print(f"   [>] {action['reason']}: {action['device']} -> {'ON' if action['state'] else 'OFF'}")
                        except Exception as e:
                            safe_print(f"   [FAIL] Failed: {e}")

                    # Trigger reactive AI decision on critical anomalies
                    if safety_check.get("critical"):
                        anomaly_desc = "; ".join(safety_check["critical"])
                        try:
                            self._reactive_queue.put_nowait({
                                "reason": "sensor_anomaly",
                                "description": anomaly_desc,
                                "sensor_snapshot": {
                                    "air_temp": reading.air_temp,
                                    "humidity": reading.humidity,
                                    "vpd": reading.vpd,
                                    "co2": reading.co2,
                                    "soil_moisture": soil_moisture_avg,
                                },
                            })
                            safe_print(f"[REACTIVE] Queued anomaly trigger: {anomaly_desc[:80]}")
                        except asyncio.QueueFull:
                            safe_print("[REACTIVE] Queue full, skipping anomaly trigger")

                # CO2 solenoid control (Vivosun regulator)
                # Only inject CO2 during light period when levels are low
                co2_target = 1000  # Target ppm for cannabis (800-1200 range)
                co2_hysteresis = 100  # Prevent rapid cycling
                is_dark = self.guardian.dark_config.is_dark_period()

                if hasattr(self.actuators, 'devices') and 'co2_solenoid' in getattr(self.actuators, 'devices', {}):
                    try:
                        current_co2 = reading.co2 or 400  # Default ambient
                        co2_state = await asyncio.wait_for(
                            self.actuators.get_state(),
                            timeout=SENSOR_READ_TIMEOUT
                        )
                        solenoid_on = getattr(co2_state, 'co2_solenoid', False) if hasattr(co2_state, 'co2_solenoid') else False

                        if is_dark:
                            # Never inject CO2 during dark period
                            if solenoid_on:
                                await asyncio.wait_for(
                                    self.actuators.set_device('co2_solenoid', False),
                                    timeout=SENSOR_READ_TIMEOUT
                                )
                                safe_print("[CO2] Solenoid OFF (dark period)")
                        elif current_co2 < (co2_target - co2_hysteresis) and not solenoid_on:
                            # CO2 too low, turn on injection
                            await asyncio.wait_for(
                                self.actuators.set_device('co2_solenoid', True),
                                timeout=SENSOR_READ_TIMEOUT
                            )
                            safe_print(f"[CO2] Solenoid ON ({current_co2} ppm < {co2_target})")
                        elif current_co2 > (co2_target + co2_hysteresis) and solenoid_on:
                            # CO2 high enough, turn off injection
                            await asyncio.wait_for(
                                self.actuators.set_device('co2_solenoid', False),
                                timeout=SENSOR_READ_TIMEOUT
                            )
                            safe_print(f"[CO2] Solenoid OFF ({current_co2} ppm > {co2_target})")
                    except asyncio.TimeoutError:
                        safe_print(f"[WARN] CO2 control timeout - skipping")
                    except Exception as e:
                        safe_print(f"[WARN] CO2 control error: {e}")

                # Stall detection and automatic reconnection
                if self._consecutive_failures >= RECONNECT_THRESHOLD:
                    safe_print(f"[ALERT] {self._consecutive_failures} consecutive failures - attempting reconnect...")

                    if self._reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
                        self._reconnect_attempts += 1
                        reconnected = await self._reconnect_hardware()
                        if reconnected:
                            safe_print(f"[OK] Reconnection successful (attempt {self._reconnect_attempts})")
                            self._consecutive_failures = 0
                            # Don't reset reconnect_attempts - keep track for this session
                        else:
                            safe_print(f"[WARN] Reconnection failed (attempt {self._reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})")
                            # Exponential backoff before next attempt
                            await asyncio.sleep(30 * self._reconnect_attempts)
                    else:
                        # Max attempts reached, log alert but continue trying with longer delays
                        if self._consecutive_failures % 10 == 0:
                            safe_print(f"[ALERT] Sensor polling degraded - {self._consecutive_failures} failures, max reconnects exhausted")
                        # Reset reconnect attempts periodically to allow recovery
                        if self._consecutive_failures % 30 == 0:
                            self._reconnect_attempts = 0
                            safe_print("[*] Resetting reconnect counter - will retry hardware connection")

                # Check time since last successful poll
                if self._last_successful_poll:
                    seconds_since_success = (datetime.now() - self._last_successful_poll).total_seconds()
                    if seconds_since_success > STALL_DETECTION_THRESHOLD:
                        safe_print(f"[ALERT] No successful poll in {int(seconds_since_success)}s - possible stall!")

                await asyncio.sleep(self.sensor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_failures += 1
                safe_print(f"[ERR] Sensor loop error ({self._consecutive_failures} consecutive): {e}")
                await asyncio.sleep(10)

    async def _ai_loop(self):
        """Background task: scheduled AI decision cycle"""
        safe_print("[*] Starting AI decision loop...")

        # Initial delay to let sensors populate
        await asyncio.sleep(10)

        while self._running:
            try:
                from src.core.watchdog import get_watchdog
                get_watchdog().heartbeat("ai_loop")

                await self._run_ai_decision(trigger="scheduled")
                await asyncio.sleep(self.ai_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                safe_print(f"[ERR] AI loop error: {e}")
                await asyncio.sleep(60)

    async def _reactive_loop(self):
        """Background task: process anomaly-triggered reactive decisions."""
        safe_print("[*] Starting reactive decision loop...")

        while self._running:
            try:
                # Wait for an anomaly trigger (blocks until one arrives)
                anomaly = await asyncio.wait_for(
                    self._reactive_queue.get(),
                    timeout=60.0,  # Check running flag every 60s
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            # Cooldown check: don't spam reactive decisions
            now = datetime.now()
            if self._last_reactive_decision:
                elapsed = (now - self._last_reactive_decision).total_seconds()
                if elapsed < self._reactive_cooldown_seconds:
                    safe_print(f"[REACTIVE] Cooldown active ({int(elapsed)}s / {self._reactive_cooldown_seconds}s), skipping")
                    continue

            safe_print(f"[REACTIVE] Processing anomaly trigger: {anomaly.get('reason', 'unknown')}")
            try:
                self._last_reactive_decision = now
                await self._run_ai_decision(trigger="anomaly")
            except Exception as e:
                safe_print(f"[ERR] Reactive decision failed: {e}")

    async def _run_ai_decision(self, trigger: str = "scheduled"):
        """Run a single AI decision cycle.

        Args:
            trigger: What initiated this cycle.
                     "scheduled" — regular 2-hour timer
                     "anomaly"   — sensor anomaly detected
                     "api"       — force_ai_decision() or API call
                     "telegram"  — Telegram command
        """
        safe_print("\n" + "=" * 60)
        safe_print(f"[AI] Trigger: {trigger}")
        safe_print(f"[AI] Grok Decision Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        safe_print("=" * 60)

        async with get_db_session() as session:
            repo = GrowRepository(session)

            # Get current state with detailed error handling
            try:
                sensors_data = await repo.get_sensors_latest()
                safe_print(f"[DEBUG] sensors_data type: {type(sensors_data)}")
            except Exception as e:
                safe_print(f"[ERR] Failed to get sensors: {e}")
                return

            try:
                devices_data = await repo.get_devices_latest()
                safe_print(f"[DEBUG] devices_data type: {type(devices_data)}")
            except Exception as e:
                safe_print(f"[ERR] Failed to get devices: {e}")
                devices_data = {}

            try:
                stage_data = await repo.get_current_stage()
                safe_print(f"[DEBUG] stage_data type: {type(stage_data)}, value: {stage_data}")
            except Exception as e:
                safe_print(f"[ERR] Failed to get stage: {e}")
                stage_data = None

            if not sensors_data:
                safe_print("[WARN] No sensor data available, skipping decision")
                return

            # Timestamp validation: reject stale sensor data
            sensor_is_stale = False
            if self._last_sensor_timestamp:
                sensor_age = (datetime.now() - self._last_sensor_timestamp).total_seconds()
                if sensor_age > SENSOR_STALE_THRESHOLD:
                    safe_print(f"[WARN] Sensor data is stale ({int(sensor_age)}s old > {SENSOR_STALE_THRESHOLD}s threshold)")
                    sensor_is_stale = True

            current_day = stage_data.get("current_day", 1) if stage_data else 1
            growth_stage = stage_data.get("current_stage", "seedling") if stage_data else "seedling"
            photoperiod = stage_data.get("photoperiod", "18/6") if stage_data else "18/6"
            safe_print(f"[DEBUG] current_day={current_day}, growth_stage={growth_stage}, photoperiod={photoperiod}")

            # Sync growth stage to SafetyGuardian for stage-specific water limits
            set_growth_stage(growth_stage)

            # Check dark period
            self._sync_dark_period_config(growth_stage, photoperiod)
            is_dark = self.guardian.dark_config.is_dark_period()
            safe_print(f"[DEBUG] is_dark={is_dark}")

            # Get water stats
            try:
                daily_stats = await repo.get_daily_stats(current_day)
                safe_print(f"[DEBUG] daily_stats type: {type(daily_stats)}, value: {daily_stats}")
            except Exception as e:
                safe_print(f"[ERR] get_daily_stats failed: {e}")
                daily_stats = {}
            water_today = daily_stats.get("total_water_ml", 0) if isinstance(daily_stats, dict) else 0
            safe_print(f"[DEBUG] water_today: {water_today}")

            # Build cross-system awareness context
            recent_events_parts = []

            # Episodic memory: recent decision history
            try:
                mem_ctx = self.memory.format_context(count=3)
                if mem_ctx and "No previous memories" not in mem_ctx:
                    recent_events_parts.append(mem_ctx)
            except Exception as e:
                safe_print(f"[WARN] Episodic memory context failed: {e}")

            # Grimoire: accumulated grow knowledge (Pattern #5 grounding)
            try:
                from src.learning.grimoire import get_all_grimoire_context
                grimoire_ctx = get_all_grimoire_context(min_confidence=0.4, limit_per_domain=8)
                if grimoire_ctx:
                    recent_events_parts.append(grimoire_ctx)
            except Exception as e:
                safe_print(f"[WARN] Grimoire context failed: {e}")

            # Pitfalls: machine-readable gotchas (Pattern #14 guardrails)
            try:
                import yaml
                pitfalls_path = Path(__file__).parent.parent / "config" / "pitfalls.yaml"
                if pitfalls_path.exists():
                    with open(pitfalls_path, encoding="utf-8") as f:
                        pitfalls_data = yaml.safe_load(f)
                    # Only inject critical/high pitfalls relevant to grow decisions
                    relevant = [
                        p for p in pitfalls_data.get("pitfalls", [])
                        if p.get("severity") in ("critical", "high")
                        and p.get("id") not in ("twitter-no-hashtags", "twitter-no-leaf-emoji", "moltbook-content-field")
                    ]
                    if relevant:
                        pitfalls_lines = ["## Known Pitfalls (AVOID THESE)"]
                        for p in relevant:
                            pitfalls_lines.append(f"- **{p['id']}**: {p['description']}")
                        recent_events_parts.append("\n".join(pitfalls_lines))
            except Exception as e:
                safe_print(f"[WARN] Pitfalls injection failed: {e}")

            # Principles: machine-readable constraints (Pattern #15)
            try:
                import yaml as _yaml
                principles_path = Path(__file__).parent.parent / "config" / "principles.yaml"
                if principles_path.exists():
                    with open(principles_path, encoding="utf-8") as f:
                        principles_data = _yaml.safe_load(f)
                    # Only inject hard-enforcement principles (keep context lean)
                    hard_rules = [
                        p for p in principles_data.get("principles", [])
                        if p.get("enforcement") == "hard"
                    ]
                    if hard_rules:
                        principles_lines = ["## Hard Constraints (MUST OBEY)"]
                        for p in hard_rules:
                            principles_lines.append(f"- **{p['id']}**: {p['rule']}")
                        recent_events_parts.append("\n".join(principles_lines))
            except Exception as e:
                safe_print(f"[WARN] Principles injection failed: {e}")

            # Unified context: trading, social, blockchain, email, events
            # This is passed as a DEDICATED parameter so it appears
            # prominently in the decision prompt (not buried in recent_events)
            cross_domain_str = None
            if self.unified_ctx:
                try:
                    cross_domain_str = await self.unified_ctx.format_unified_context()
                except Exception as e:
                    safe_print(f"[WARN] Unified context failed: {e}")

            recent_events = "\n\n".join(recent_events_parts) if recent_events_parts else None

            # Run AI decision
            safe_print("[DEBUG] Calling brain.decide()...")
            try:
                # Build sensor context with reliability info
                sensor_context = {
                    "using_mock_sensors": self._using_mock_sensors,
                    "using_mock_actuators": self._using_mock_actuators,
                    "using_mock_soil": self._using_mock_soil,
                    "sensor_data_stale": sensor_is_stale,
                }
                if sensor_is_stale:
                    sensor_context["stale_warning"] = f"CAUTION: Sensor data is {int(sensor_age)}s old. Make conservative decisions."
                if self._using_mock_sensors:
                    sensor_context["mock_warning"] = "CAUTION: Using MOCK sensors - real sensor data unavailable. Readings are synthetic."

                result = await self.brain.decide(
                    sensors=sensors_data,
                    devices=devices_data or {},
                    current_day=current_day,
                    growth_stage=growth_stage,
                    photoperiod=photoperiod,
                    is_dark_period=is_dark,
                    water_today_ml=water_today,
                    recent_events=recent_events,
                    sensor_context=sensor_context,
                    trigger=trigger,
                    cross_domain_context=cross_domain_str,
                )
            except Exception as e:
                import traceback
                safe_print(f"[ERR] brain.decide() failed: {e}")
                safe_print(f"[TRACEBACK] {traceback.format_exc()}")
                # Don't crash - log error and return to retry next cycle
                safe_print("[WARN] Skipping this decision cycle due to error. Will retry in next interval.")
                return

            # Log AI output to database
            await repo.log_ai_decision(
                grow_day=current_day,
                output_text=result.output_text,
                actions_taken=result.actions_taken,
                tokens_used=result.tokens_used
            )

            self._last_ai_decision = result

            # Record decision for grow learning (Phase 3)
            try:
                from src.learning.grow_learning import get_grow_learning
                gl = get_grow_learning()
                # Build conditions from sensor data
                conditions = {
                    "temp": sensors_data.get("air_temp", 0),
                    "humidity": sensors_data.get("humidity", 0),
                    "co2": sensors_data.get("co2", 0),
                    "vpd": sensors_data.get("vpd", 0),
                    "soil_moisture_avg": sensors_data.get("soil_moisture", 0),
                }
                for action in (result.actions_taken or []):
                    if action.get("success"):
                        # Map tool names to decision types
                        tool = action.get("tool", "unknown")
                        decision_type = {
                            "water_plant": "water",
                            "inject_co2": "co2",
                            "set_exhaust_fan": "exhaust",
                            "set_grow_light": "light",
                            "set_circulation_fan": "exhaust",
                        }.get(tool, tool)
                        action_str = f"{decision_type}:{json.dumps(action.get('arguments', {}))}"
                        gl.record_decision(
                            grow_day=current_day,
                            stage=growth_stage,
                            decision_type=decision_type,
                            action=action_str,
                            conditions=conditions,
                            notes=f"AI decision cycle {datetime.now().isoformat()}",
                        )
            except Exception as e:
                safe_print(f"[WARN] Grow learning record failed: {e}")

            # Store episodic memory entry
            try:
                actions_list = []
                observations = []
                for action in (result.actions_taken or []):
                    tool = action.get("tool", "unknown")
                    args = action.get("arguments", {})
                    if action.get("success"):
                        if tool == "water_plant":
                            actions_list.append(f"water:{args.get('amount_ml', 0)}ml")
                        elif tool == "inject_co2":
                            actions_list.append(f"co2:inject")
                        else:
                            actions_list.append(f"{tool}:{json.dumps(args)}")
                    else:
                        observations.append(f"{tool} failed: {action.get('message', 'unknown')}")

                self.memory.store(
                    grow_day=current_day,
                    conditions={
                        "temp_c": sensors_data.get("air_temp", 0),
                        "humidity": sensors_data.get("humidity", 0),
                        "co2": sensors_data.get("co2", 0),
                        "vpd": sensors_data.get("vpd", 0),
                        "soil_moisture": sensors_data.get("soil_moisture", 0),
                    },
                    actions_taken=actions_list,
                    observations=observations or [result.output_text[:200]],
                    next_actions=[],
                )

                # Disk persistence is now automatic via EpisodicMemory._save_to_disk()
            except Exception as e:
                safe_print(f"[WARN] Episodic memory store failed: {e}")

            # Feed decision to social daemon via file-based IPC
            # (social runs in a separate process, so in-memory queue_decision is unreachable)
            try:
                self._queue_decision_ipc(
                    decision={"output_text": result.output_text, "actions_taken": result.actions_taken},
                    sensor_data=sensors_data,
                )
            except Exception as e:
                safe_print(f"[WARN] Social queue_decision IPC failed: {e}")

            # Write to shared event log (unified Mon narrative)
            try:
                from src.core.event_log import log_event
                action_summary = ", ".join(
                    f"{a['tool']}({'OK' if a['success'] else 'FAIL'})"
                    for a in (result.actions_taken or [])
                ) or "no actions"
                log_event(
                    "grow", "decision",
                    f"AI decision cycle: {action_summary}",
                    {"output_preview": result.output_text[:200], "actions_count": len(result.actions_taken or [])}
                )
            except Exception as e:
                safe_print(f"[WARN] Event log write failed: {e}")

            # Measure outcomes for pending grow decisions (compare conditions now vs before)
            try:
                from src.learning.grow_learning import get_grow_learning
                gl = get_grow_learning()
                pending = gl.get_pending_outcomes()
                if pending:
                    current_conditions = {
                        "temp": sensors_data.get("air_temp", 0),
                        "humidity": sensors_data.get("humidity", 0),
                        "co2": sensors_data.get("co2", 0),
                        "vpd": sensors_data.get("vpd", 0),
                        "soil_moisture_avg": sensors_data.get("soil_moisture", 0),
                    }
                    for decision_id in pending[:5]:  # Measure up to 5 per cycle
                        effectiveness = gl.measure_outcome(decision_id, current_conditions)
                        if abs(effectiveness) > 0.1:
                            safe_print(f"[LEARN] Decision #{decision_id} effectiveness: {effectiveness:+.2f}")
            except Exception as e:
                safe_print(f"[WARN] Grow outcome measurement failed: {e}")

            # Print output
            safe_print("\n[OUTPUT] Grok's Output:")
            safe_print("-" * 40)
            safe_print(result.output_text[:500] + "..." if len(result.output_text) > 500 else result.output_text)

            if result.actions_taken:
                safe_print("\n[ACTIONS] Actions Taken:")
                for action in result.actions_taken:
                    status = "[OK]" if action["success"] else "[FAIL]"
                    safe_print(f"   {status} {action['tool']}: {action['message']}")

            safe_print("=" * 60 + "\n")

            # If Grok requested a human action, notify immediately
            if self.alerts and NOTIFICATIONS_AVAILABLE and result.actions_taken:
                for action in result.actions_taken:
                    if action.get("tool") == "request_human_help" and action.get("success"):
                        args = action.get("arguments") or {}
                        task = args.get("task") or "Human action requested"
                        urgency = args.get("urgency") or "medium"
                        details = args.get("details") or ""

                        msg = task if not details else f"{task}\n\nDetails: {details}"
                        await alert_human_action_required(
                            self.alerts,
                            title="Human action needed for Mon",
                            message=msg,
                            day=current_day,
                            stage=growth_stage,
                            urgency=urgency,
                        )

            # Post to Twitter (every 6th decision = ~12 hours, with date guard)
            if self.twitter and SOCIAL_AVAILABLE:
                decision_count = len(self.brain.decisions) if self.brain else 0
                # Use a date-based guard to prevent double-posting on restart
                today_str = datetime.now().strftime("%Y-%m-%d")
                last_twitter_day = getattr(self, '_last_twitter_post_day', None)
                should_tweet = (
                    decision_count > 0
                    and decision_count % 6 == 0
                    and last_twitter_day != today_str
                )
                safe_print(f"[DEBUG] Twitter: decision_count={decision_count}, will post={should_tweet}")
                if should_tweet:
                    safe_print(f"[*] Posting Twitter update (decision #{decision_count})...")
                    try:
                        await self._post_daily_update(
                            day=current_day,
                            stage=growth_stage,
                            sensors=sensors_data,
                            water_ml=water_today,
                        )
                        self._last_twitter_post_day = today_str
                    except Exception as e:
                        # Twitter errors should never crash the grow system
                        safe_print(f"[ERR] Twitter posting failed (non-fatal): {e}")
            else:
                if not self.twitter:
                    safe_print("[DEBUG] Twitter: client not initialized")
                if not SOCIAL_AVAILABLE:
                    safe_print("[DEBUG] Twitter: SOCIAL_AVAILABLE=False")

    async def force_ai_decision(self):
        """Manually trigger an AI decision (for testing/API)."""
        await self._run_ai_decision(trigger="api")

    async def handle_interactive_query(
        self,
        query: str,
        user_context: Optional[str] = None,
    ) -> dict:
        """
        Handle an interactive query from Telegram, API, etc.

        Routes through GrokBrain.interactive_query() which has full
        tool access — the agent can read sensors, check history,
        and even take actions in response.

        Returns:
            dict with keys: output_text, actions_taken, tool_rounds, trigger
        """
        if not self.brain:
            return {"output_text": "Agent brain not initialized.", "actions_taken": [], "tool_rounds": 0, "trigger": "interactive"}

        # Get current grow state for context
        growth_stage = "vegetative"
        current_day = 1
        try:
            async with get_db_session() as session:
                repo = GrowRepository(session)
                stage_data = await repo.get_current_stage()
                if stage_data:
                    growth_stage = stage_data.get("current_stage", "vegetative")
                    current_day = stage_data.get("current_day", 1)
        except Exception as e:
            safe_print(f"[WARN] Could not fetch stage for interactive query: {e}")

        # Build extra context
        context_parts = []
        if user_context:
            context_parts.append(user_context)

        # Add recent sensor snapshot
        try:
            async with get_db_session() as session:
                repo = GrowRepository(session)
                sensors = await repo.get_sensors_latest()
                if sensors:
                    context_parts.append(
                        f"Current sensors: temp={sensors.get('air_temp')}°C, "
                        f"RH={sensors.get('humidity')}%, VPD={sensors.get('vpd')} kPa, "
                        f"CO2={sensors.get('co2')} ppm, soil={sensors.get('soil_moisture')}%"
                    )
        except Exception:
            pass

        combined_context = "\n".join(context_parts) if context_parts else None

        # Run through the agentic brain
        result = await self.brain.interactive_query(
            query=query,
            context=combined_context,
            growth_stage=growth_stage,
            current_day=current_day,
        )

        return {
            "output_text": result.output_text,
            "actions_taken": result.actions_taken or [],
            "tool_rounds": result.tool_rounds,
            "total_tool_calls": result.total_tool_calls,
            "tokens_used": result.tokens_used,
            "trigger": result.trigger,
        }

    async def _generate_ganja_mon_tweet(
        self,
        day: int,
        stage: str,
        vpd: float,
        temp_f: float,
        humidity: float,
        water_ml: int,
    ) -> str:
        """
        Generate a Twitter update using Grok AI in Ganja Mon voice.

        Returns the tweet text (max 280 chars).
        """
        import httpx
        import os

        # Prepare the prompt for Grok
        prompt = f"""You are Ganja Mon - a hilarious Jamaican rasta stoner character who posts updates about "Mon", a cannabis plant being grown autonomously by AI. Think Bob Marley meets Cheech & Chong meets crypto Twitter degen.

YOUR PERSONALITY (CRITICAL - THIS IS THE WHOLE POINT):
- You're HIGH AS HELL and it shows in how you write
- You laugh constantly: "yahaha", "ahahaha", "wahahaa"
- You use Jamaican patois naturally: "mon", "irie", "bumbaclot", "bloodclaat", "mi", "ya", "fi", "nuff", "tings"
- You call the plant "likkle Mon" or "mi baby Mon" with affection
- You're chill but ENTHUSIASTIC about the grow
- You make weed jokes and references
- You roast anyone who doubts AI growing weed
- Example phrases: "Jah bless di grow!", "Mon looking IRIE today!", "Raasclaat she thicc!", "One love, one plant mon!"

TODAY'S DATA:
- Day {day} of {stage} stage
- Temperature: {temp_f:.1f}F
- Humidity: {humidity:.0f}%
- VPD: {vpd:.2f} kPa
- Watered: {water_ml}ml today

EXAMPLES OF GOOD TWEETS (match this energy):
- "Yahaha Day 7 and likkle Mon looking IRIE! VPD locked at 1.05... she be transpirin like a champ mon. Jah provide! 🌱"
- "Mi baby Mon thirsty today - gave her 150ml of dat sweet water. RH holding at 68%... bumbaclot she loves it! Ahahaha"
- "Day 15 and Mon's leaves reaching fi di sky! Temperature vibin at 77F, humidity perfect. AI grow hit different ya know 🔥"
- "Bloodclaat! VPD dropped to 0.8 but we good mon, we GOOD. Humidifier doing di ting. One love! Wahaha"

RULES:
- NO HASHTAGS (no # anything)
- NO 🌿 leaf emoji (it's not cannabis)
- Keep under 280 characters
- MUST have personality - no boring corporate updates
- Include 1-2 data points but make it FUN

Write ONLY the tweet, nothing else:"""

        try:
            # Call Grok API
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                safe_print("[WARN] No XAI_API_KEY, using template fallback")
                # Fallback to template if no API key
                from src.social import format_daily_update
                return format_daily_update(day, stage, vpd, temp_f, humidity, water_ml, self.plant_name)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-4-1-fast-non-reasoning",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.9,
                        "max_tokens": 150
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    tweet_text = data["choices"][0]["message"]["content"].strip()

                    # Remove any quotes that Grok might have added
                    tweet_text = tweet_text.strip('"\'')

                    # Ensure it's under 280 chars
                    if len(tweet_text) > 280:
                        tweet_text = tweet_text[:277] + "..."

                    safe_print(f"[OK] Grok generated tweet ({len(tweet_text)} chars)")
                    return tweet_text
                else:
                    safe_print(f"[WARN] Grok API error {response.status_code}, using template")
                    from src.social import format_daily_update
                    return format_daily_update(day, stage, vpd, temp_f, humidity, water_ml, self.plant_name)

        except Exception as e:
            safe_print(f"[ERR] Failed to generate Ganja Mon tweet: {e}")
            # Fallback to template
            from src.social import format_daily_update
            return format_daily_update(day, stage, vpd, temp_f, humidity, water_ml, self.plant_name)

    async def _post_daily_update(
        self,
        day: int,
        stage: str,
        sensors: dict,
        water_ml: int,
    ):
        """Post a daily update to Twitter"""
        if not self.twitter or not SOCIAL_AVAILABLE:
            return

        try:
            # Prepare data for Grok
            vpd = sensors.get("vpd", 1.0)
            temp_f = sensors.get("air_temp", 25) * 9/5 + 32  # Convert to F if in C
            humidity = sensors.get("humidity", 50)

            # Generate tweet using Grok AI with Ganja Mon persona
            safe_print(f"[*] Asking Grok to write tweet in Ganja Mon voice...")
            tweet_text = await self._generate_ganja_mon_tweet(
                day=day,
                stage=stage,
                vpd=vpd,
                temp_f=temp_f,
                humidity=humidity,
                water_ml=water_ml,
            )

            # Check if it's dark period - skip images during nighttime
            is_dark = self.guardian.dark_config.is_dark_period()
            
            # Capture image from web server API (camera is already in use by web server)
            # Skip image capture during dark periods to avoid posting dark/meaningless photos
            image_data = None
            if is_dark:
                safe_print("[INFO] Skipping webcam image (dark period - mon sleeping 🌙)")
            else:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:8000/api/webcam/latest", timeout=10.0)
                        if response.status_code == 200:
                            image_data = response.content
                            safe_print(f"[OK] Fetched webcam image from API ({len(image_data)} bytes)")
                        else:
                            safe_print(f"[WARN] Failed to fetch webcam: HTTP {response.status_code}")
                except Exception as e:
                    safe_print(f"[WARN] Could not fetch webcam image: {e}")

            # Post tweet with or without image
            if image_data and len(image_data) > 1000:  # Ensure it's not a tiny mock image
                result = await self.twitter.tweet_with_image(
                    text=tweet_text,
                    image_data=image_data,
                    alt_text=f"Cannabis plant {self.plant_name} on day {day}",
                )
            else:
                safe_print("[INFO] Posting tweet without image (camera unavailable)")
                result = await self.twitter.tweet(tweet_text)

            if result.success:
                safe_print(f"[OK] Posted daily update: {result.tweet_id}")
            else:
                safe_print(f"[WARN] Tweet failed: {result.error}")

        except Exception as e:
            safe_print(f"[ERR] Social posting error: {e}")

    def get_status(self) -> dict:
        """Get current orchestrator status"""
        # Calculate seconds since last successful poll
        seconds_since_poll = None
        if self._last_successful_poll:
            seconds_since_poll = int((datetime.now() - self._last_successful_poll).total_seconds())

        return {
            "running": self._running,
            "sensor_interval": self.sensor_interval,
            "ai_interval": self.ai_interval,
            "last_ai_decision": self._last_ai_decision.timestamp.isoformat() if self._last_ai_decision else None,
            "safety_status": self.guardian.get_status() if self.guardian else None,
            "photoperiod": self.photoperiod.get_status() if self.photoperiod else None,
            # Stall detection metrics
            "last_successful_poll": self._last_successful_poll.isoformat() if self._last_successful_poll else None,
            "seconds_since_poll": seconds_since_poll,
            "consecutive_failures": self._consecutive_failures,
            "reconnect_attempts": self._reconnect_attempts,
            "is_stalled": seconds_since_poll is not None and seconds_since_poll > STALL_DETECTION_THRESHOLD,
        }


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Main entry point for running the orchestrator"""

    orchestrator = GrokMonOrchestrator(
        sensor_interval_seconds=60,      # Poll sensors every minute
        ai_interval_seconds=7200,        # AI decision every 2 hours
        plant_name="Mon"
    )

    # Handle shutdown gracefully
    loop = asyncio.get_event_loop()

    def shutdown():
        safe_print("\n[*] Shutdown signal received...")
        asyncio.create_task(orchestrator.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
