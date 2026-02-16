# ARCHIVED 2026-02-08: Features merged into src/orchestrator.py
# This file is kept for reference only. The orchestrator now handles:
# - Unified context (src/brain/unified_context.py)
# - Episodic memory (src/brain/memory.py)
# - Auto-review engine (src/review/engine.py)
# - All 14 grow tools (src/ai/tools.py)
# - GrowLearning integration (src/learning/grow_learning.py)

"""
Grok & Mon - AI Agent Core (LEGACY)
=====================================
Main decision loop for autonomous cannabis cultivation.
Reads sensors, analyzes with Grok, executes actions.

Enhanced with SOLTOMATO patterns:
- Episodic memory for context persistence
- Day totals tracking (watering, CO2 injections)
- Sleep/wake cycle pattern
- Structured decision logging
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
import sys
from rich.console import Console
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table

# Force ASCII-safe output on Windows
if sys.platform == 'win32':
    console = Console(force_terminal=True, no_color=False, legacy_windows=False)
else:
    console = Console()


def sanitize_for_windows(text: str) -> str:
    """Replace Unicode characters that Windows console can't display"""
    if sys.platform != 'win32':
        return text
    replacements = {
        'μ': 'u',  # mu -> u (umol -> umol)
        '°': ' deg',  # degree symbol
        '→': '->',
        '←': '<-',
        '✓': '[OK]',
        '✗': '[X]',
        '…': '...',
        '—': '--',
        '–': '-',
        ''': "'",
        ''': "'",
        '"': '"',
        '"': '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-ASCII
    return text.encode('ascii', 'replace').decode('ascii')

from .memory import EpisodicMemory, create_memory_entry
from .unified_context import UnifiedContextAggregator

# Import review engine for automatic periodic reviews
try:
    from ..review.engine import ReviewEngine
    from ..db.models import ReviewType
    REVIEW_ENGINE_AVAILABLE = True
except ImportError:
    REVIEW_ENGINE_AVAILABLE = False

# Import transparency/audit module
try:
    from ..api.transparency import log_device_change, transparency_api
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    def log_device_change(*args, **kwargs): pass  # No-op fallback

# Import cultivation utilities for VPD calculation
# Try absolute imports (works when src is in sys.path)
# Falls back to relative imports for package compatibility
try:
    from cultivation import calculate_vpd, get_stage_parameters
    CULTIVATION_AVAILABLE = True
except ImportError:
    try:
        from ..cultivation import calculate_vpd, get_stage_parameters
        CULTIVATION_AVAILABLE = True
    except ImportError:
        CULTIVATION_AVAILABLE = False

# Import hardware modules
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

try:
    from hardware.webcam import USBWebcam, get_logitech_index
    WEBCAM_AVAILABLE = True
except ImportError:
    try:
        from ..hardware.webcam import USBWebcam, get_logitech_index
        WEBCAM_AVAILABLE = True
    except ImportError:
        WEBCAM_AVAILABLE = False
        get_logitech_index = lambda: 2  # Fallback

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "src" / "brain" / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# xAI/Grok API configuration
XAI_API_BASE = "https://api.x.ai/v1"

# Available Grok models (as of Jan 2026):
# - grok-4-1-fast-non-reasoning : Fastest, cheapest, best for tool calling
# - grok-4-1-fast-reasoning     : With reasoning/thinking mode  
# - grok-4-0709                 : Vision supported, more expensive
# - grok-2-vision-1212          : Dedicated vision model
# - grok-3, grok-3-mini         : Legacy models

DEFAULT_MODEL = "grok-4-1-fast-non-reasoning"  # Best for agentic tool calling
VISION_MODEL = "grok-4-0709"                    # Use this when analyzing images


def load_system_prompt() -> str:
    """Load the system prompt from markdown file"""
    prompt_path = PROMPTS_DIR / "system_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding='utf-8')
    return "You are Mon's Grok, an AI cannabis cultivation assistant with attitude."


# =============================================================================
# Grok API Client
# =============================================================================

class GrokClient:
    """Simple client for xAI Grok API"""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set")
        
        self.client = httpx.AsyncClient(
            base_url=XAI_API_BASE,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    async def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        max_tokens: int = 4096,
        system: str | None = None
    ) -> dict:
        """Send a chat completion request to Grok"""
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        
        if system:
            # Grok uses system message in messages array
            payload["messages"] = [{"role": "system", "content": system}] + messages
        
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# Safety & Safeguards
# =============================================================================

class WateringSafeguard:
    """
    Safety system to prevent over/under watering.
    Enforces cool-downs and daily limits regardless of AI decision.
    """
    def __init__(self):
        self.last_water_time = 0
        self.daily_total_ml = 0
        self.last_reset_day = datetime.now().day
        
        # Daily volume limits (ml)
        self.limits = {
            "clone": 500,     # Buffer: target is 300, allow 500
            "seedling": 300,
            "veg": 1500,
            "flower": 1500,
            "late_flower": 1000
        }

    def can_water(self, amount_ml: int, grow_stage: str | None) -> tuple[bool, str]:
        now = datetime.now()
        
        # Reset daily counter if new day
        if now.day != self.last_reset_day:
            self.daily_total_ml = 0
            self.last_reset_day = now.day

        # 1. Cooldown Check (Safety against sensor glitches/loops)
        # Minimum 45 mins between waterings to allow drainage/sensor update
        # Exception: Micro-doses (<50ml) can happen every 15 mins if needed
        time_since = now.timestamp() - self.last_water_time
        
        if amount_ml > 50:
            # Regular watering -> 45 min cooldown
            if time_since < 2700: 
                minutes_left = int((2700 - time_since) / 60)
                return False, f"Safety Cooldown: Wait {minutes_left} min for drainage (prev large watering)"
        else:
            # Micro-dose -> 15 min cooldown
            if time_since < 900:
                minutes_left = int((900 - time_since) / 60)
                return False, f"Safety Cooldown: Wait {minutes_left} min (prev micro-dose)"

        # 2. Daily Limit Check
        stage = (grow_stage or "veg").lower()
        
        # Match partial keys (e.g. "early_veg" -> "veg")
        limit = 1500 # Default
        for key, val in self.limits.items():
            if key in stage:
                limit = val
                break
            
        if self.daily_total_ml + amount_ml > limit:
            return False, f"Daily Safety Limit Reached ({self.daily_total_ml}/{limit}ml)"

        return True, "OK"

    def record_watering(self, amount_ml: int):
        self.last_water_time = datetime.now().timestamp()
        self.daily_total_ml += amount_ml


# =============================================================================
# Agent Class
# =============================================================================

class GrokAndMonAgent:
    """
    Main agent for autonomous cannabis grow management.
    Powered by Grok AI.

    Enhanced with SOLTOMATO patterns:
    - Episodic memory for context between cycles
    - Day totals tracking
    - Sleep/wake cycle logging
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        vision_model: str = VISION_MODEL,
        decision_interval_minutes: int = 30,
        grow_day: int = 1,
        use_hardware: bool = False,
        kasa_ips: dict | None = None,
    ):
        self.grok = GrokClient()
        self.model = model                    # grok-4.1-fast for text/decisions
        self.vision_model = vision_model      # grok-4 for image analysis
        self.decision_interval = decision_interval_minutes * 60  # seconds
        self.system_prompt = load_system_prompt()
        self.running = False
        self.use_hardware = use_hardware

        # Safeguards
        self.safeguard = WateringSafeguard()

        # Hardware modules (initialized on demand)
        self._govee: GoveeSensorHub | None = None
        self._kasa: KasaActuatorHub | None = None
        self._webcam: USBWebcam | None = None
        self._kasa_ips = kasa_ips or {}
        self._hardware_initialized = False

        # SOLTOMATO patterns: Episodic memory and day tracking
        self.memory = EpisodicMemory(max_entries=100)
        self.grow_day = grow_day
        self.current_stage = None  # Populated from DB in read_sensors()
        self.cycle_count = 0

        # Unified context aggregator: gives Grok cross-system awareness by
        # reading data files from the trading agent, engagement daemon, and
        # Farcaster client.  See src/brain/unified_context.py for details.
        self.unified_ctx = UnifiedContextAggregator()

        # Review system: pending context to inject into next Grok decision
        self._pending_review_context: str | None = None

        # Load persisted memory if exists
        self._load_memory()

        hardware_status = "ENABLED" if use_hardware else "MOCK MODE"
        console.print(Panel(
            f"[green]Grok & Mon Agent Initialized[/green]\n"
            f"Text Model: {model}\n"
            f"Vision Model: {vision_model}\n"
            f"Decision Interval: {decision_interval_minutes} min\n"
            f"Grow Day: {grow_day}\n"
            f"Memory Entries: {len(self.memory.entries)}\n"
            f"Hardware: {hardware_status}\n"
            f"[dim]\"Grok grows your herb, mon\"[/dim]",
            title="Grok & Mon"
        ))

    def _load_memory(self):
        """Load persisted episodic memory"""
        memory_file = LOGS_DIR / "episodic_memory.json"
        if memory_file.exists():
            try:
                self.memory = EpisodicMemory.from_json(memory_file.read_text())
                console.print(f"[dim]Loaded {len(self.memory.entries)} memory entries[/dim]")
            except Exception as e:
                console.print(f"[yellow]Could not load memory: {e}[/yellow]")

    def _save_memory(self):
        """Persist episodic memory to disk"""
        memory_file = LOGS_DIR / "episodic_memory.json"
        try:
            memory_file.write_text(self.memory.to_json())
        except Exception as e:
            console.print(f"[yellow]Could not save memory: {e}[/yellow]")
    
    async def _init_hardware(self):
        """Initialize hardware connections if enabled"""
        if self._hardware_initialized or not self.use_hardware:
            return

        console.print("[dim]Initializing hardware connections...[/dim]")

        # Initialize Govee sensor
        if GOVEE_AVAILABLE:
            try:
                self._govee = GoveeSensorHub()
                if await self._govee.connect():
                    console.print("[green][OK] Govee sensor connected[/green]")
                else:
                    console.print("[yellow]! Govee sensor failed to connect[/yellow]")
                    self._govee = None
            except Exception as e:
                console.print(f"[yellow]! Govee init failed: {e}[/yellow]")
                self._govee = None
        else:
            console.print("[dim]Govee module not available[/dim]")

        # Initialize Kasa smart plugs
        if KASA_AVAILABLE and self._kasa_ips:
            try:
                self._kasa = KasaActuatorHub(self._kasa_ips)
                if await self._kasa.connect():
                    console.print("[green][OK] Kasa smart plugs connected[/green]")
                else:
                    console.print("[yellow]! Kasa plugs failed to connect[/yellow]")
                    self._kasa = None
            except Exception as e:
                console.print(f"[yellow]! Kasa init failed: {e}[/yellow]")
                self._kasa = None
        else:
            console.print("[dim]Kasa plugs not configured[/dim]")

        # Initialize webcam (auto-detect Logitech C270)
        if WEBCAM_AVAILABLE:
            try:
                logitech_idx = get_logitech_index()
                self._webcam = USBWebcam(device_index=logitech_idx)
                if await self._webcam.connect():
                    console.print("[green][OK] Webcam connected[/green]")
                else:
                    console.print("[yellow]! Webcam failed to connect[/yellow]")
                    self._webcam = None
            except Exception as e:
                console.print(f"[yellow]! Webcam init failed: {e}[/yellow]")
                self._webcam = None
        else:
            console.print("[dim]Webcam module not available[/dim]")

        self._hardware_initialized = True

    async def gather_sensor_data(self) -> dict:
        """Collect all sensor readings from hardware or mock"""
        # Try hardware first if enabled
        if self.use_hardware and not self._hardware_initialized:
            await self._init_hardware()

        # Initialize as None - only populate with REAL sensor data
        temp_f = None
        humidity = None
        vpd_kpa = None
        co2_ppm = None
        lights_on = None
        soil_moisture = None
        sensor_source = "unavailable"

        # Read from Govee sensors (REAL DATA ONLY)
        if self._govee and await self._govee.is_connected():
            try:
                reading = await self._govee.read_all()
                temp_f = reading.air_temp * 9/5 + 32  # Convert C to F
                humidity = reading.humidity
                vpd_kpa = reading.vpd
                co2_ppm = reading.co2 if reading.co2 > 0 else None
                sensor_source = "govee"
                console.print(f"[green]Govee: {temp_f:.1f}F, {humidity:.0f}% RH, VPD {vpd_kpa:.2f}[/green]")
            except Exception as e:
                console.print(f"[red]Govee read failed: {e}[/red]")
        else:
            console.print("[red]No Govee sensors connected - environment data unavailable[/red]")

        # Read soil moisture from API (consolidates all sensor sources)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/sensors/latest", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        sensor_data = await resp.json()
                        soil_moisture = sensor_data.get("soil_moisture")
                        if soil_moisture is not None:
                            console.print(f"[green]Soil: {soil_moisture:.1f}%[/green]")
                        # Also grab environment data if not already from Govee
                        if temp_f is None and sensor_data.get("air_temp") is not None:
                            temp_f = sensor_data["air_temp"] * 9/5 + 32
                            humidity = sensor_data.get("humidity")
                            vpd_kpa = sensor_data.get("vpd")
                            co2_ppm = sensor_data.get("co2")
                            sensor_source = "api"
        except Exception as e:
            console.print(f"[yellow]Could not read from API: {e}[/yellow]")

        # Read device states from Kasa if available
        if self._kasa and await self._kasa.is_connected():
            try:
                state = await self._kasa.get_state()
                lights_on = state.grow_light
                console.print(f"[green]Kasa: lights {'ON' if lights_on else 'OFF'}[/green]")
            except Exception as e:
                console.print(f"[red]Kasa read failed: {e}[/red]")
        else:
            console.print("[red]No Kasa devices connected - light state unavailable[/red]")

        # Get grow session info from database (NOT hardcoded)
        grow_stage = None
        photoperiod = None
        try:
            from db.connection import get_db_session
            from db.models import GrowSession
            from sqlalchemy import select
            async with get_db_session() as session:
                result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = result.scalar_one_or_none()
                if grow_session:
                    grow_stage = grow_session.current_stage.value if grow_session.current_stage else None
                    self.current_stage = grow_stage  # Cache for hardware action limits
                    photoperiod = grow_session.photoperiod.value if grow_session.photoperiod else None
        except Exception as e:
            console.print(f"[yellow]Could not read grow session from DB: {e}[/yellow]")

        return {
            "timestamp": datetime.now().isoformat(),
            "sensor_source": sensor_source,
            "environment": {
                "temperature_f": temp_f,
                "humidity_percent": humidity,
                "vpd_kpa": vpd_kpa,
                "co2_ppm": co2_ppm
            },
            "light": {
                "ppfd_umol": None,  # No PAR sensor yet - need to add one
                "lights_on": lights_on,
                "schedule": photoperiod
            },
            "substrate": {
                "moisture_percent": soil_moisture,
                "last_watered": None,
                "watering_threshold": 45 if grow_stage in ["clone", "seedling"] else 30,
                "note": f"Ecowitt WH51 soil sensor - clones need water when below 45%, veg/flower below 30%"
            },
            "growth_stage": {
                "stage": grow_stage,
                "days_in_stage": self.grow_day
            }
        }

    async def capture_image(self) -> str | None:
        """Capture image from camera, return base64"""
        import base64

        # First try fetching enhanced analysis frame from API (white-balance
        # corrected, CLAHE contrast, sharpened — better for detecting yellowing,
        # spots, curling under grow lights).  Falls back to raw frame if the
        # /analysis endpoint isn't available.
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Prefer enhanced analysis frame
                async with session.get("http://localhost:8000/api/webcam/analysis", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        b64_image = base64.b64encode(image_bytes).decode('utf-8')
                        console.print("[dim]Webcam: Enhanced analysis frame from API[/dim]")
                        return b64_image
                # Fallback to raw frame
                async with session.get("http://localhost:8000/api/webcam/latest", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        b64_image = base64.b64encode(image_bytes).decode('utf-8')
                        console.print("[dim]Webcam: Raw frame from API[/dim]")
                        return b64_image
        except Exception as e:
            # API not available, try direct camera access
            pass

        # Fallback to direct camera access
        if self.use_hardware and not self._hardware_initialized:
            await self._init_hardware()

        if self._webcam and await self._webcam.is_connected():
            try:
                _, b64_image = await self._webcam.capture_for_analysis()
                console.print("[dim]Webcam: Image captured directly[/dim]")
                return b64_image
            except Exception as e:
                console.print(f"[yellow]Webcam capture failed: {e}[/yellow]")
                return None
        else:
            console.print("[dim]Camera: Not available[/dim]")
            return None
    
    def build_context_message(self, sensor_data: dict, image_b64: str | None,
                              unified_context: str = "") -> list:
        """Build the user message with current context and episodic memory.

        Assembles a multimodal prompt for Grok containing sensor readings,
        episodic grow memory, any pending review findings, the unified
        cross-system context (trading/social/Farcaster), and optionally a
        plant image.

        Args:
            sensor_data: Current sensor readings dict (temp, humidity, VPD, etc.)
            image_b64: Base64-encoded JPEG plant photo, or None if camera offline.
            unified_context: Pre-formatted markdown from UnifiedContextAggregator.
                Injected between the review findings and the analysis prompt so
                Grok sees trading + social status alongside grow data.

        Returns:
            A list of OpenAI-style content blocks (text + optional image_url).
        """
        content = []

        # Get episodic memory context (SOLTOMATO pattern)
        memory_context = self.memory.format_context(count=3)
        day_summary = self.memory.get_day_summary(self.grow_day)

        # Camera status section - CRITICAL for preventing hallucinations
        if image_b64:
            camera_status = "**Camera:** ONLINE - Image attached below"
            analysis_prompt = "How's Mon looking? Analyze both the sensor data AND the attached image. Give me your analysis and any actions needed."
        else:
            camera_status = "**Camera:** OFFLINE - NO IMAGE AVAILABLE. Do NOT make any claims about visual appearance, leaf condition, or plant health that would require seeing the plant. Only analyze sensor data."
            analysis_prompt = "Analyze the sensor data ONLY. Since there is NO camera image, do NOT make visual observations about leaves, cotyledons, color, or plant appearance. Only analyze environmental conditions."

        # Add sensor data as text with memory context
        message_text = f"""## Current Grow Status - Day {self.grow_day}

**Timestamp:** {sensor_data['timestamp']}

### Camera Status
{camera_status}

### Environment
- Temperature: {sensor_data['environment']['temperature_f']}°F
- Humidity: {sensor_data['environment']['humidity_percent']}%
- VPD: {sensor_data['environment']['vpd_kpa']} kPa
- CO2: {sensor_data['environment'].get('co2_ppm', 'N/A')} ppm

### Lighting
- PPFD: {sensor_data['light']['ppfd_umol']} μmol/m²/s
- Lights On: {sensor_data['light']['lights_on']}
- Schedule: {sensor_data['light']['schedule']}

### Substrate
- Moisture: {sensor_data['substrate']['moisture_percent']}%
- Last Watered: {sensor_data['substrate']['last_watered']}

### Growth Stage
- Current Stage: {sensor_data['growth_stage']['stage']}
- Days in Stage: {sensor_data['growth_stage']['days_in_stage']}

### Day {self.grow_day} Totals So Far
- Water: {day_summary.get('totals', {}).get('water_ml', 0)}ml
- CO2 Injections: {day_summary.get('totals', {}).get('co2_injections', 0)}
- Decision Cycles Today: {day_summary.get('entries', 0)}

---

{memory_context}

---

{self._consume_review_context()}

{unified_context}

---

{analysis_prompt}
Respond with your structured JSON analysis.

Remember to include episodic memory format at the end:
```
Episodic Memory Stored:
*** DAY {self.grow_day} - [TIME_LABEL] ([TIME]) ***
CONDITIONS: [temp], [humidity], [co2]
ACTIONS TAKEN: [actions]
OBSERVATION: [key observation]
NEXT: [what to check next]
```"""
        
        content.append({
            "type": "text",
            "text": message_text
        })
        
        # Add image if available (Grok supports vision)
        if image_b64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"
                }
            })
        
        return content

    def _consume_review_context(self) -> str:
        """Return pending review context for AI injection, then clear it."""
        if self._pending_review_context:
            ctx = self._pending_review_context
            self._pending_review_context = None
            return f"### Recent Grow Review Findings\n{ctx}\n"
        return ""

    async def get_ai_decision(self, sensor_data: dict, image_b64: str | None,
                              unified_context: str = "") -> dict:
        """Send context to Grok and get a structured JSON decision.

        Delegates to :meth:`build_context_message` to assemble the prompt,
        then calls the xAI Grok API.  Model selection is automatic:

        - **With image:** ``grok-4`` (vision model, more expensive but can
          analyse plant photos)
        - **Text only:** ``grok-4.1-fast`` (cheaper, faster, better at tool
          calling)

        Args:
            sensor_data: Current sensor readings dict.
            image_b64: Base64-encoded JPEG plant photo, or None.
            unified_context: Pre-formatted cross-system context string from
                :class:`~src.brain.unified_context.UnifiedContextAggregator`.

        Returns:
            Parsed JSON decision dict, or ``{"error": ...}`` on failure.
        """

        user_content = self.build_context_message(sensor_data, image_b64, unified_context)
        
        # Choose model based on whether we have an image
        # Vision model is more expensive but can analyze plant photos
        model_to_use = self.vision_model if image_b64 else self.model
        
        try:
            console.print(f"[dim]Using model: {model_to_use}[/dim]")
            response = await self.grok.chat(
                messages=[
                    {"role": "user", "content": user_content}
                ],
                model=model_to_use,
                max_tokens=4096,
                system=self.system_prompt
            )
            
            # Extract text response
            response_text = response["choices"][0]["message"]["content"]
            
            # Try to parse as JSON
            try:
                # Find JSON block in response
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                elif "{" in response_text:
                    # Try to extract JSON object
                    start = response_text.index("{")
                    end = response_text.rindex("}") + 1
                    json_str = response_text[start:end]
                else:
                    json_str = response_text
                
                decision = json.loads(json_str)
                # Validate structure
                if not isinstance(decision, dict):
                    decision = {"raw_response": str(decision), "actions": [], "parse_warning": "Non-dict JSON"}
                if "actions" not in decision:
                    decision["actions"] = []
                if not isinstance(decision.get("actions"), list):
                    decision["actions"] = []
            except (json.JSONDecodeError, ValueError):
                console.print("[yellow]! Could not parse Grok response as JSON[/yellow]")
                decision = {
                    "raw_response": response_text[:2000],
                    "commentary": response_text[:200],
                    "actions": [],
                    "parse_error": True
                }
            
            return decision
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            console.print(f"[red]Grok API error ({e.response.status_code}): {error_detail[:200]}[/red]")
            return {"error": error_detail}
        except Exception as e:
            import traceback
            console.print(f"[red]Error getting Grok decision: {type(e).__name__}: {e}[/red]")
            console.print(f"[dim red]{traceback.format_exc()[:500]}[/dim red]")
            return {"error": str(e)}
    
    async def execute_actions(self, decision: dict) -> list:
        """Execute any actions recommended by Grok"""
        results = []
        
        actions = decision.get("actions", [])
        
        for action in actions[:3]:  # Safety limit: max 3 actions per cycle
            tool_name = action.get("tool")
            parameters = action.get("parameters", {})
            reason = action.get("reason", "No reason provided")
            
            console.print(f"\n[yellow]Action:[/yellow] {tool_name}")
            console.print(f"[dim]Reason: {reason}[/dim]")
            console.print(f"[dim]Parameters: {json.dumps(parameters)}[/dim]")

            # Execute the action on real hardware if available
            result = await self._execute_hardware_action(tool_name, parameters)
            
            # SOLTOMATO PATTERN: Log device state change for audit trail
            # This proves we're real - scams don't have audit logs
            device_map = {
                "trigger_irrigation": "water_pump",
                "set_exhaust_speed": "exhaust_fan",
                "set_light_intensity": "grow_light",
                "inject_co2": "co2_injector",
                "control_humidifier": "humidifier"
            }
            if tool_name in device_map:
                log_device_change(
                    device=device_map[tool_name],
                    old_state="off",  # Would check actual state
                    new_state=str(parameters),
                    triggered_by="grok_decision",
                    reason=reason
                )
                console.print(f"[dim green][OK] Logged to device audit trail[/dim green]")
            
            results.append({
                "tool": tool_name,
                "parameters": parameters,
                "result": result
            })
        
        return results

    async def _execute_hardware_action(self, tool_name: str, parameters: dict) -> dict:
        """
        Execute a tool action on real hardware if available.
        Returns result dict with success status and details.
        """
        # If not in hardware mode, return simulated success
        if not self.use_hardware:
            return {"success": True, "simulated": True, "message": "Mock mode - no hardware"}

        try:
            # =====================================================================
            # Irrigation Control (Kasa Smart Plug - Pump)
            # =====================================================================
            if tool_name == "trigger_irrigation":
                # Get grow stage for limits
                grow_stage = self.current_stage or "vegetative"  # From DB via read_sensors()

                # Calculate volume (approx 20ml/sec)
                duration = float(parameters.get("duration_seconds", 0))
                amount_ml = int(duration * 20)
                
                # CHECK SAFEGUARDS
                allowed, reason = self.safeguard.can_water(amount_ml, grow_stage)
                
                if not allowed:
                    console.print(f"[bold red]🚫 BLOCKED by Safeguard: {reason}[/bold red]")
                    return {
                        "success": False, 
                        "simulated": False, 
                        "error": f"Safeguard blocked: {reason}",
                        "blocked": True
                    }

                if self._kasa:
                    success = await self._kasa.water(amount_ml)
                    if success:
                        self.safeguard.record_watering(amount_ml)
                        console.print(f"[green][OK] Watered ~{amount_ml}ml ({duration}s)[/green]")
                        return {
                            "success": True,
                            "simulated": False,
                            "device": "kasa_pump",
                            "amount_ml": amount_ml
                        }
                    return {"success": False, "simulated": False, "error": "Kasa pump command failed"}

                return {"success": False, "simulated": False, "error": "Kasa not configured"}

            # =====================================================================
            # Humidifier Control (Govee H7145)
            # =====================================================================
            if tool_name == "control_humidifier":
                if self._govee and self._govee.has_humidifier():
                    state = parameters.get("state", "off")
                    target = parameters.get("target_humidity")

                    # Set power state
                    power_success = await self._govee.set_humidifier_power(state == "on")

                    # Optionally set target humidity
                    target_success = True
                    if target and state == "on":
                        target_success = await self._govee.set_humidifier_target(int(target))

                    if power_success and target_success:
                        console.print(f"[green][OK] Humidifier {state.upper()}[/green]")
                        return {
                            "success": True,
                            "simulated": False,
                            "device": "govee_humidifier",
                            "state": state,
                            "target_humidity": target
                        }
                    else:
                        return {"success": False, "simulated": False, "error": "Govee command failed"}
                else:
                    console.print("[yellow]! Humidifier not available[/yellow]")
                    return {"success": False, "simulated": False, "error": "No humidifier connected"}

            # =====================================================================
            # CO2 Injection (Kasa Smart Plug - Solenoid)
            # =====================================================================
            elif tool_name == "inject_co2":
                duration = int(parameters.get("duration_seconds", 15))
                duration = max(5, min(30, duration))  # Clamp 5-30s per safety spec
                if self._kasa:
                    success = await self._kasa.inject_co2(duration)
                    if success:
                        console.print(f"[green][OK] CO2 injected for {duration}s[/green]")
                        return {"success": True, "simulated": False, "device": "co2_solenoid", "duration_seconds": duration}
                    return {"success": False, "simulated": False, "error": "CO2 injection failed"}
                return {"success": False, "simulated": False, "error": "Kasa not configured"}

            # =====================================================================
            # Kasa Smart Plug Control (Lights, Fans, etc.)
            # =====================================================================
            elif tool_name == "set_light_intensity":
                if self._kasa:
                    # Kasa plugs are on/off - intensity > 0 means on
                    intensity = parameters.get("intensity_percent", 0)
                    on_off = intensity > 0
                    success = await self._kasa.set_device("grow_light", on_off)
                    if success:
                        console.print(f"[green][OK] Light {'ON' if on_off else 'OFF'}[/green]")
                        return {"success": True, "simulated": False, "device": "kasa_light", "state": "on" if on_off else "off"}
                    return {"success": False, "simulated": False, "error": "Kasa command failed"}
                return {"success": False, "simulated": False, "error": "Kasa not configured"}

            elif tool_name == "set_exhaust_speed":
                if self._kasa:
                    speed = parameters.get("speed_percent", 0)
                    on_off = speed > 0
                    success = await self._kasa.set_device("exhaust_fan", on_off)
                    if success:
                        console.print(f"[green][OK] Exhaust {'ON' if on_off else 'OFF'}[/green]")
                        return {"success": True, "simulated": False, "device": "kasa_exhaust", "state": "on" if on_off else "off"}
                    return {"success": False, "simulated": False, "error": "Kasa command failed"}
                return {"success": False, "simulated": False, "error": "Kasa not configured"}

            # =====================================================================
            # Email (queue outbound email via mailer subsystem)
            # =====================================================================
            elif tool_name == "queue_email":
                try:
                    from ..mailer.client import get_email_client
                    client = get_email_client()
                    to = parameters.get("to", "")
                    subject = parameters.get("subject", "")
                    body = parameters.get("body", "")
                    if to and subject and body:
                        client.queue_send(to=to, subject=subject, body=body)
                        console.print(f"[green][OK] Email queued to {to}: {subject}[/green]")
                        return {"success": True, "simulated": False, "action": "email_queued", "to": to}
                    else:
                        console.print("[yellow]! Email missing required fields (to, subject, body)[/yellow]")
                        return {"success": False, "simulated": False, "error": "Missing email fields"}
                except ImportError:
                    console.print("[yellow]! Email subsystem not available[/yellow]")
                    return {"success": False, "simulated": False, "error": "Mailer not installed"}

            # =====================================================================
            # Allium Blockchain Data API
            # =====================================================================
            elif tool_name == "query_allium":
                try:
                    api_key = os.environ.get("ALLIUM_API_KEY", "")
                    if not api_key:
                        return {"success": False, "error": "ALLIUM_API_KEY not set"}
                    endpoint = parameters.get("endpoint", "prices")
                    chain = parameters.get("chain", "ethereum")
                    params = parameters.get("params", {})

                    endpoint_map = {
                        "prices": "/api/v1/developer/prices",
                        "wallet_balances": "/api/v1/developer/wallet/balances",
                        "wallet_transactions": "/api/v1/developer/wallet/transactions",
                        "wallet_pnl": "/api/v1/developer/wallet/pnl",
                    }
                    url = f"https://api.allium.so{endpoint_map.get(endpoint, endpoint_map['prices'])}"
                    headers = {"Content-Type": "application/json", "X-API-KEY": api_key}

                    if endpoint == "prices":
                        body = params.get("tokens", [{"token_address": "0x0000000000000000000000000000000000000000", "chain": chain}])
                    else:
                        body = {"address": params.get("address", ""), "chain": chain}

                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(url, json=body, headers=headers)
                        resp.raise_for_status()
                        data = resp.json()
                    console.print(f"[green][OK] Allium query: {endpoint} on {chain}[/green]")
                    return {"success": True, "simulated": False, "data": data}
                except Exception as e:
                    console.print(f"[yellow]Allium query failed: {e}[/yellow]")
                    return {"success": False, "error": str(e)}

            # =====================================================================
            # Grow Stage Transition (writes to DB)
            # =====================================================================
            elif tool_name == "update_grow_stage":
                new_stage = parameters.get("stage", "").lower()
                reason = parameters.get("reason", "AI-initiated transition")
                stage_map = {
                    "seedling": "seedling", "veg": "vegetative", "vegetative": "vegetative",
                    "transition": "transition", "flower": "flowering", "flowering": "flowering",
                    "late_flower": "late_flower", "harvest": "harvest",
                }
                mapped = stage_map.get(new_stage)
                if not mapped:
                    return {"success": False, "error": f"Unknown stage: {new_stage}"}
                try:
                    from db.connection import get_db_session
                    from db.models import GrowthStage as GrowthStageEnum
                    from db.repository import GrowRepository
                    async with get_db_session() as session:
                        repo = GrowRepository(session)
                        await repo.transition_stage(to_stage=GrowthStageEnum(mapped), triggered_by="ai", reason=reason)
                        await session.commit()
                    self.current_stage = mapped
                    console.print(f"[green][OK] Stage transition -> {mapped}[/green]")
                    return {"success": True, "simulated": False, "new_stage": mapped}
                except Exception as e:
                    console.print(f"[red]Stage transition failed: {e}[/red]")
                    return {"success": False, "error": str(e)}

            # =====================================================================
            # Web Search & Browse (internet access)
            # =====================================================================
            elif tool_name == "web_search":
                try:
                    from src.tools.web_search import get_web_search
                    ws = get_web_search()
                    query = params.get("query", "")
                    max_results = params.get("max_results", 5)
                    results = await ws.search(query, max_results=max_results)
                    console.print(f"[cyan]Web search: '{query[:60]}' → {len(results)} results[/cyan]")
                    return {"success": True, "results": results}
                except Exception as e:
                    console.print(f"[red]Web search failed: {e}[/red]")
                    return {"success": False, "error": str(e)}

            elif tool_name == "browse_url":
                try:
                    from src.tools.web_search import get_web_search
                    ws = get_web_search()
                    url = params.get("url", "")
                    max_chars = params.get("max_chars", 5000)
                    text = await ws.browse(url, max_chars=max_chars)
                    console.print(f"[cyan]Browsed: {url[:60]} → {len(text)} chars[/cyan]")
                    return {"success": True, "content": text[:5000]}
                except Exception as e:
                    console.print(f"[red]Browse failed: {e}[/red]")
                    return {"success": False, "error": str(e)}

            elif tool_name == "deep_research":
                try:
                    from src.tools.web_search import get_web_search
                    ws = get_web_search()
                    question = params.get("question", "")
                    max_sources = params.get("max_sources", 3)
                    result = await ws.deep_research(question, max_sources=max_sources)
                    findings = result.get("findings", [])
                    console.print(f"[cyan]Deep research: '{question[:60]}' → {len(findings)} findings[/cyan]")
                    return {"success": True, "findings": findings, "action_items": result.get("action_items", [])}
                except Exception as e:
                    console.print(f"[red]Deep research failed: {e}[/red]")
                    return {"success": False, "error": str(e)}

            # =====================================================================
            # Logging/Observation actions (no hardware needed)
            # =====================================================================
            elif tool_name in ["log_observation", "request_human_help"]:
                console.print(f"[dim][OK] Logged: {tool_name}[/dim]")
                return {"success": True, "simulated": False, "action": "logged"}

            # =====================================================================
            # Unknown tool - log warning but don't fail
            # =====================================================================
            else:
                console.print(f"[yellow]! Unknown tool: {tool_name} (no hardware handler)[/yellow]")
                return {"success": True, "simulated": True, "message": f"No handler for {tool_name}"}

        except Exception as e:
            console.print(f"[red]Hardware error: {e}[/red]")
            return {"success": False, "simulated": False, "error": str(e)}

    def log_decision(self, sensor_data: dict, decision: dict, action_results: list):
        """Log the decision cycle for analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sensor_data": sensor_data,
            "grok_decision": decision,
            "action_results": action_results
        }
        
        # Write to daily log file
        log_file = LOGS_DIR / f"decisions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def display_decision(self, decision: dict):
        """Display Grok's decision in a nice format"""

        # SOLTOMATO PATTERN: Show AI reasoning first (transparency!)
        reasoning = decision.get("reasoning", "")
        if reasoning:
            # Escape any markup-like content (e.g., [THINK] tags from Grok)
            safe_reasoning = sanitize_for_windows(rich_escape(reasoning))
            console.print(Panel(
                f"[dim italic]{safe_reasoning}[/dim italic]",
                title="BRAIN: Grok's Reasoning (Transparency Mode)",
                border_style="dim blue"
            ))

        # Show Grok's commentary first (the fun part)
        commentary = decision.get("commentary", "")
        if commentary:
            safe_commentary = sanitize_for_windows(rich_escape(commentary))
            console.print(f"\n[bold green]Grok says:[/bold green] {safe_commentary}")
        
        analysis = decision.get("analysis", {})
        
        # Health status table
        table = Table(title="Mon's Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Overall Health", analysis.get("overall_health", "N/A"))
        table.add_row("Current VPD", str(analysis.get("current_vpd", "N/A")))
        table.add_row("VPD Status", analysis.get("vpd_status", "N/A"))
        
        console.print(table)
        
        # Observations
        if "observations" in analysis:
            console.print("\n[bold]Observations:[/bold]")
            for obs in analysis["observations"]:
                console.print(f"  * {sanitize_for_windows(rich_escape(str(obs)))}")

        # Concerns
        if "concerns" in analysis:
            console.print("\n[bold yellow]Concerns:[/bold yellow]")
            for concern in analysis["concerns"]:
                console.print(f"  ! {sanitize_for_windows(rich_escape(str(concern)))}")

        # Recommendations
        if "recommendations" in decision:
            console.print("\n[bold blue]Recommendations:[/bold blue]")
            for rec in decision["recommendations"]:
                console.print(f"  -> {sanitize_for_windows(rich_escape(str(rec)))}")

        # SOLTOMATO PATTERN: Show what to focus on next
        next_check = decision.get("next_check_focus", "")
        if next_check:
            console.print(f"\n[dim]>> Next check focus: {sanitize_for_windows(rich_escape(str(next_check)))}[/dim]")
    
    async def run_decision_cycle(self):
        """Run a single decision cycle with SOLTOMATO memory pattern"""
        self.cycle_count += 1

        console.print(f"\n{'='*60}")
        console.print(f"[bold green]Grok & Mon Decision Cycle[/bold green] - Day {self.grow_day}")
        console.print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Cycle #{self.cycle_count}")
        console.print(f"{'='*60}\n")

        # 1. Gather sensor data
        console.print("[dim]Gathering sensor data...[/dim]")
        sensor_data = await self.gather_sensor_data()

        # 2. Capture image
        console.print("[dim]Capturing image of Mon...[/dim]")
        image_b64 = await self.capture_image()

        # 2b. Gather cross-system context (trading, social, farcaster).
        #     This async call reads data files from the trading agent and
        #     engagement daemon, plus fetches recent Farcaster cast metrics
        #     (cached 10 min).  The resulting markdown string is injected
        #     into the Grok prompt so the AI brain has full situational
        #     awareness beyond just grow data.
        console.print("[dim]Gathering cross-system context...[/dim]")
        try:
            unified_context = await self.unified_ctx.format_unified_context()
        except Exception as e:
            console.print(f"[dim]Unified context unavailable: {e}[/dim]")
            unified_context = ""

        # 3. Get Grok's decision
        console.print("[dim]Consulting Grok...[/dim]")
        decision = await self.get_ai_decision(sensor_data, image_b64, unified_context)

        # 4. Display decision
        self.display_decision(decision)

        # 5. Execute actions
        if decision.get("actions"):
            console.print("\n[bold]Executing Actions:[/bold]")
            action_results = await self.execute_actions(decision)
        else:
            action_results = []
            console.print("\n[dim]No actions required this cycle. Mon's vibing.[/dim]")

        # 6. Log everything
        self.log_decision(sensor_data, decision, action_results)

        # 7. SOLTOMATO pattern: Store episodic memory
        self._store_episodic_memory(sensor_data, decision, action_results)

        # 7b. Auto-generate grow review every 12 cycles (~6h at 30min intervals)
        #     Writes findings to data/historical_review.json so unified_context
        #     picks them up and injects them into every future Grok prompt.
        if REVIEW_ENGINE_AVAILABLE and self.cycle_count % 12 == 0 and self.cycle_count > 0:
            await self._auto_generate_review()

        # 8. Feed decision to social engagement daemon (posts across all channels)
        try:
            from ..social.engagement_daemon import get_engagement_daemon
            daemon = get_engagement_daemon()
            daemon.queue_decision(decision, sensor_data, image_b64)
            console.print("[dim]Decision queued for social posting[/dim]")
        except Exception as e:
            console.print(f"[dim]Social daemon not available: {e}[/dim]")

        social_post = decision.get("social_post")
        if social_post:
            console.print(Panel(
                f"[bold white]{sanitize_for_windows(social_post)}[/bold white]",
                title="SOCIAL: Social Post Ready",
                border_style="magenta"
            ))

            # Try to post to X if Twitter is configured
            if self._should_post_to_x():
                await self._post_to_x(social_post, image_b64)

        # 9. Display sleep message (SOLTOMATO pattern)
        self._display_sleep_message()

    def _sanitize_memory_display(self, text: str) -> str:
        """Sanitize memory display for Windows"""
        return sanitize_for_windows(text)

    def _store_episodic_memory(self, sensor_data: dict, decision: dict, action_results: list):
        """Store episodic memory entry (SOLTOMATO pattern)"""

        # Build conditions dict
        conditions = {
            "temp_c": round((sensor_data['environment']['temperature_f'] - 32) * 5/9, 1),
            "temp_f": sensor_data['environment']['temperature_f'],
            "humidity": sensor_data['environment']['humidity_percent'],
            "vpd": sensor_data['environment']['vpd_kpa'],
            "co2": sensor_data['environment'].get('co2_ppm'),
            "soil_moisture": sensor_data['substrate']['moisture_percent'],
        }

        # Format actions taken
        actions_taken = []
        for result in action_results:
            tool = result.get("tool", "unknown")
            params = result.get("parameters", {})
            if "irrigation" in tool or "water" in tool:
                ml = params.get("amount_ml", 200)
                actions_taken.append(f"water:{ml}ml")
            elif "co2" in tool:
                actions_taken.append("co2:inject")
            elif "light" in tool:
                actions_taken.append(f"light:{params}")
            elif "exhaust" in tool or "fan" in tool:
                actions_taken.append(f"fan:{params}")
            else:
                actions_taken.append(f"{tool}")

        # Extract observations from decision
        observations = decision.get("analysis", {}).get("observations", [])
        if not observations and decision.get("commentary"):
            observations = [decision["commentary"][:100]]

        # Generate next actions
        next_actions = ["Read sensors"]
        recommendations = decision.get("recommendations", [])
        for rec in recommendations[:2]:
            next_actions.append(rec)

        # Store the memory
        entry = self.memory.store(
            grow_day=self.grow_day,
            conditions=conditions,
            actions_taken=actions_taken,
            observations=observations,
            next_actions=next_actions,
        )

        # Persist to disk
        self._save_memory()

        # Display the formatted memory
        console.print("\n[bold cyan]Episodic Memory Stored:[/bold cyan]")
        console.print(Panel(sanitize_for_windows(entry.format_for_display()), border_style="cyan"))

    async def _auto_generate_review(self):
        """Auto-generate a grow review and write to historical_review.json.

        This closes the feedback loop:
          ReviewEngine → data/historical_review.json → unified_context → Grok prompt
        """
        try:
            from ..db.connection import get_db_session
            from ..db.repository import GrowRepository

            console.print("\n[dim]Running auto grow review...[/dim]")
            async with get_db_session() as session:
                repo = GrowRepository(session)
                engine = ReviewEngine(repo)
                result = await engine.generate_review(review_type=ReviewType.DAILY)

                # Format for AI consumption
                ai_context = engine.format_for_ai_context(result)

                # Write to historical_review.json for unified_context pickup
                review_data = {
                    "insights": [],
                    "patterns": [],
                    "recommendations": [],
                    "last_updated": datetime.now().isoformat(),
                    "score": result.overall_score,
                }

                # Extract insights from review results
                issues = result.results.get("patterns", {}).get("issues", [])
                for issue in issues[:5]:
                    review_data["insights"].append(
                        f"[{issue.get('severity', '?').upper()}] {issue.get('description', '')}"
                    )

                suggestions = result.results.get("suggestions", [])
                for s in suggestions[:5]:
                    review_data["recommendations"].append(
                        f"[{s.get('priority', '?').upper()}] {s.get('title', '')}: {s.get('action', '')}"
                    )

                # Detect patterns
                compliance = result.results.get("compliance", {})
                for metric, data in compliance.items():
                    if isinstance(data, dict) and data.get("grade") in ("D", "F"):
                        review_data["patterns"].append(
                            f"{metric} consistently poor: grade {data['grade']}, "
                            f"{data.get('time_in_range_pct', '?')}% in range"
                        )

                review_path = Path(__file__).parent.parent.parent / "data" / "historical_review.json"
                with open(review_path, "w") as f:
                    json.dump(review_data, f, indent=2)

                console.print(f"[green]Grow review complete: score {result.overall_score:.0f}/100[/green]")
                console.print(f"[dim]Written to {review_path}[/dim]")

                # Also inject into next cycle directly
                self._pending_review_context = ai_context

        except Exception as e:
            console.print(f"[dim]Auto review failed: {e}[/dim]")

    def _should_post_to_x(self) -> bool:
        """Check if we should post to X (compliance + config)"""
        # Check if Twitter credentials are configured
        twitter_key = os.environ.get("TWITTER_API_KEY")
        if not twitter_key:
            return False
        
        # Use compliance system for rate limiting
        try:
            from ..social.compliance import PostingTracker
            tracker = PostingTracker()
            can_post, reason = tracker.can_post_now()
            if not can_post:
                console.print(f"[dim]Skipping X post: {reason}[/dim]")
                return False
            return True
        except ImportError:
            # Fallback: simple cycle-based limiting
            return self.cycle_count % 6 == 0
    
    async def _post_to_x(self, text: str, image_b64: str | None):
        """Post to X/Twitter with optional image"""
        try:
            from ..social.twitter import TwitterClient
            from ..social.compliance import PostingTracker
            
            client = TwitterClient()
            if not client._configured:
                console.print("[dim]Twitter not configured, skipping post[/dim]")
                return
            
            # Convert base64 to bytes if we have an image
            image_data = None
            if image_b64:
                import base64
                image_data = base64.b64decode(image_b64)
            
            if image_data:
                result = await client.tweet_with_image(
                    text=text,
                    image_data=image_data,
                    alt_text=f"Mon the cannabis plant - Day {self.grow_day}"
                )
            else:
                result = await client.tweet(text)
            
            if result.success:
                console.print(f"[green][OK] Posted to X![/green] Tweet ID: {result.tweet_id}")
                # Record successful post for compliance tracking
                try:
                    tracker = PostingTracker()
                    tracker.record_post(result.tweet_id, text)
                    stats = tracker.get_stats()
                    console.print(f"[dim]Posts today: {stats['posts_today']}/{stats['daily_limit']}[/dim]")
                except Exception:
                    pass  # Don't fail if tracking fails
            else:
                console.print(f"[yellow]Tweet failed: {result.error}[/yellow]")
                
        except ImportError:
            console.print("[dim]Twitter module not available[/dim]")
        except Exception as e:
            console.print(f"[yellow]X post error: {e}[/yellow]")

    def _display_sleep_message(self):
        """Display sleep message (SOLTOMATO pattern)"""
        next_wake = datetime.now().timestamp() + self.decision_interval
        next_wake_time = datetime.fromtimestamp(next_wake)

        console.print(Panel(
            f"[bold]ZZZ ENTERING SLEEP MODE[/bold]\n\n"
            f"Sleep Duration: {self.decision_interval // 60} minutes\n"
            f"Next Wake: {next_wake_time.strftime('%I:%M %p')}\n\n"
            f"[dim]Mon's vibing. Grok's resting.[/dim]",
            title="SLEEP",
            border_style="blue"
        ))
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        
        console.print("\n[bold green]Starting Grok & Mon Agent...[/bold green]")
        console.print("Press Ctrl+C to stop.\n")
        
        while self.running:
            try:
                await self.run_decision_cycle()
                await asyncio.sleep(self.decision_interval)
            except KeyboardInterrupt:
                self.running = False
                console.print("\n[yellow]Shutting down agent...[/yellow]")
            except Exception as e:
                console.print(f"[red]Error in decision cycle: {e}[/red]")
                await asyncio.sleep(60)  # Wait a minute before retrying
        
        await self.grok.close()
        console.print("[green]Agent stopped. Mon's on their own now.[/green]")


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Grok & Mon AI Agent")
    parser.add_argument("--once", action="store_true", help="Run single cycle and exit")
    parser.add_argument("--interval", type=int, default=30, help="Decision interval in minutes")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Grok model for text/decisions (default: grok-4.1-fast)")
    parser.add_argument("--vision-model", default=VISION_MODEL, help="Grok model for image analysis (default: grok-4)")
    parser.add_argument("--day", type=int, default=1, help="Current grow day (default: 1)")
    parser.add_argument("--hardware", action="store_true", help="Use real hardware (Govee, Kasa, Webcam)")
    parser.add_argument("--kasa-light", type=str, help="Kasa smart plug IP for grow light")
    parser.add_argument("--kasa-fan", type=str, help="Kasa smart plug IP for exhaust fan")
    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("XAI_API_KEY"):
        console.print("[red]Error: XAI_API_KEY environment variable not set[/red]")
        console.print("Set it with: export XAI_API_KEY='your-key-here'")
        console.print("Get your key at: https://console.x.ai")
        return

    # Build Kasa IPs from args or environment
    kasa_ips = {}
    if args.kasa_light or os.environ.get("KASA_LIGHT_IP"):
        kasa_ips["grow_light"] = args.kasa_light or os.environ.get("KASA_LIGHT_IP")
    if args.kasa_fan or os.environ.get("KASA_FAN_IP"):
        kasa_ips["exhaust_fan"] = args.kasa_fan or os.environ.get("KASA_FAN_IP")

    agent = GrokAndMonAgent(
        model=args.model,
        vision_model=args.vision_model,
        decision_interval_minutes=args.interval,
        grow_day=args.day,
        use_hardware=args.hardware,
        kasa_ips=kasa_ips if kasa_ips else None,
    )

    if args.once:
        asyncio.run(agent.run_decision_cycle())
    else:
        asyncio.run(agent.run())


if __name__ == "__main__":
    main()
