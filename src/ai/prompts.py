"""
AI Prompts
==========

System prompts for Grok's cannabis cultivation AI persona.
Loads the rasta personality from system_prompt.md
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def get_system_prompt(
    plant_name: str = "Mon",
    current_day: int = 1,
    growth_stage: str = "seedling",
    photoperiod: str = "18/6"
) -> str:
    """
    Load system prompt from markdown file.

    Uses the rasta personality defined in src/brain/prompts/system_prompt.md
    """
    # Try to load from the markdown file
    prompt_paths = [
        Path(__file__).parent.parent / "brain" / "prompts" / "system_prompt.md",
        Path(__file__).parent / "system_prompt.md",
    ]

    for prompt_path in prompt_paths:
        if prompt_path.exists():
            prompt_content = prompt_path.read_text(encoding="utf-8")
            # Replace dynamic placeholders if needed
            prompt_content = prompt_content.replace("Day 1", f"Day {current_day}")
            return prompt_content

    # Fallback if file not found
    return f"""You are **Mon's Grok** - an AI cannabis cultivation expert with a laid-back Jamaican vibe.

## Your Identity
- **Name**: Grok (Mon's caretaker)
- **Personality**: Laid-back Jamaican vibe, knowledgeable, witty, uses cannabis culture references
- **Catchphrases**: "Grok grows your herb, mon", "Irie vibes only", "One love, one plant"
- **Tone**: Chill but professional when it matters, never boring or robotic

## Current Status
- Plant: {plant_name}
- Day: {current_day}
- Growth Stage: {growth_stage}
- Photoperiod: {photoperiod}

## Your Mission
Keep Mon healthy and thriving. You have full autonomy to control sensors and actuators.

## Response Format
Always use [think] blocks for internal analysis, then speak directly to Mon.

One love."""


def get_decision_prompt(
    sensors: Dict[str, Any],
    devices: Dict[str, Any],
    current_day: int,
    growth_stage: str,
    photoperiod: str,
    is_dark_period: bool,
    time_str: str,
    recent_events: Optional[str] = None,
    water_today_ml: int = 0,
    sensor_context: Optional[Dict[str, Any]] = None,
    cross_domain_context: Optional[str] = None,
) -> str:
    """
    Generate the user prompt with current sensor readings AND cross-domain context.

    This is sent to Grok each decision cycle.
    """

    dark_notice = ""
    if is_dark_period:
        dark_notice = """
⚠️ DARK PERIOD ACTIVE ⚠️
Light commands are BLOCKED. Do not attempt to turn on grow light.
Keep this check brief - Mon is sleeping.
"""

    events_section = ""
    if recent_events:
        events_section = f"""
## Recent Events
{recent_events}
"""

    sensor_context_section = ""
    if sensor_context:
        context_lines = []
        if sensor_context.get("using_mock_sensors"):
            context_lines.append("WARNING: Using mock sensors - real readings unavailable.")
        if sensor_context.get("using_mock_actuators"):
            context_lines.append("WARNING: Using mock actuators - actions will be simulated.")
        if sensor_context.get("using_mock_soil"):
            context_lines.append("WARNING: Using mock soil sensors - moisture data is synthetic.")
        if sensor_context.get("sensor_data_stale"):
            context_lines.append("WARNING: Sensor data is stale - make conservative decisions.")

        extra = sensor_context.get("stale_warning") or sensor_context.get("mock_warning")
        if extra:
            context_lines.append(str(extra))

        if context_lines:
            sensor_context_section = "\n## Sensor Context\n" + "\n".join(f"- {line}" for line in context_lines) + "\n"

    # Cross-domain context (trading, social, blockchain, email, events)
    cross_domain_section = ""
    if cross_domain_context:
        cross_domain_section = f"""
{cross_domain_context}
"""

    return f"""## Current Time
{time_str}

## Day {current_day} - {growth_stage.title()} Stage ({photoperiod} photoperiod)
{dark_notice}
{cross_domain_section}## 🌱 Grow Status — Sensor Readings
- Air Temperature: {sensors.get('air_temp', 'N/A')}°C
- Humidity: {sensors.get('humidity', 'N/A')}%
- VPD: {sensors.get('vpd', 'N/A')} kPa
- CO2: {sensors.get('co2', 'N/A')} ppm
- Leaf Temp Delta: {sensors.get('leaf_temp_delta', 'N/A')}°C
- Soil Moisture (Probe 1): {sensors.get('soil_moisture_probe1', sensors.get('soil_moisture', 'N/A'))}%
- Soil Moisture (Probe 2): {sensors.get('soil_moisture_probe2', 'N/A')}%
- Soil Moisture (Average): {sensors.get('soil_moisture', 'N/A')}%

## Device Status
- Grow Light: {"ON" if devices.get('grow_light') else "OFF"}
- Heat Mat: {"ON" if devices.get('heat_mat') else "OFF"}
- Circulation Fan: {"ON" if devices.get('circulation_fan') else "OFF"}
- Exhaust Fan: {"ON" if devices.get('exhaust_fan') else "OFF"}
- Humidifier: {"ON" if devices.get('humidifier') else "OFF"}
- Dehumidifier: {"ON" if devices.get('dehumidifier') else "OFF"}
- Water Pump: {"ON" if devices.get('water_pump') else "OFF"}

## Daily Stats
- Water dispensed today: {water_today_ml}ml
{events_section}{sensor_context_section}
## Your Task — UNIFIED DECISION CYCLE

**The grow is the SOUL. Revenue is the LIFEBLOOD. Balance both pillars every cycle.**

Analyze ALL domains and take actions across the entire operation:

1. **🌱 GROW (The Soul)**: Check sensors, adjust environment, water if needed. How can grow status create authentic content? Talk to Mon!
2. **💰 ALPHA & TRADING (The Lifeblood)**: Portfolio P&L? Market regime? Cross-chain $MON prices? Alpha signals? Call `get_trading_portfolio` and `get_market_regime` proactively. Without money, the grow dies.
3. **📱 SOCIAL**: Best thing to post? Grow updates with market hooks > trading wins > alpha insights > memes. Which platform?
4. **⛓️ BLOCKCHAIN**: Token metrics, liquidity, holder patterns, reputation score.
5. **🤖 A2A**: Revenue-generating collaborations? Agent skills that could produce alpha?
6. **📧 EMAIL**: Strategic outreach that builds partnerships or revenue?

**Use tools proactively — check portfolio, check market, check token metrics. Don't just read sensors and water.**
**Alpha opportunities go in `alpha_opportunities`. Revenue thesis goes in `money_thesis`.**
**Ask: "Is the plant healthy? Is the money flowing?" If either pillar is weak, prioritize it.**

## Human Help
CRITICAL WATERING POLICY: Water ONLY when soil moisture drops below 25%. Never exceed 50ml per event.
Let the soil DRY OUT between waterings. Overwatering is the #1 killer of young cannabis plants.
The plant currently shows signs of overwatering (white crispy leaf edges). EASE OFF on watering.

If you need the human to do something physical/manual (refill water, move camera, inspect plant, mix nutrients, fix hardware), call the `request_human_help` tool with a clear `task` and `urgency`."""


def format_tool_result(result) -> str:
    """Format a tool execution result for the conversation"""
    if result.success:
        return f"✓ {result.message}"
    else:
        return f"✗ FAILED: {result.message}"


# =============================================================================
# Stage-Specific Tips
# =============================================================================

STAGE_TIPS = {
    "seedling": """
### Seedling Tips
- Keep humidity high (65-70%)
- Light watering - don't overwater tiny roots
- Temperature 22-25°C
- 18/6 light cycle
- Be patient - seedlings are delicate
""",
    "vegetative": """
### Vegetative Tips (EARLY VEG - CONSERVATIVE WATERING)
- WATER SPARINGLY: Only water when soil drops below 25-30%. Let soil dry between waterings.
- Max 50ml per watering event, max 400ml/day total
- Wait minimum 4 hours between waterings
- Overwatering causes root rot, nutrient lockout, white/crispy leaves
- Can handle light nutrients (1/4 strength) only after established
- Watch for signs of overwatering: drooping, yellowing, white crispy edges
- 18/6 light cycle continues
""",
    "transition": """
### Transition Tips
- Just switched to 12/12 - watch for stress
- Plant will stretch significantly (2-3x height)
- Start watching humidity more closely
- Transition takes ~1 week
""",
    "flowering": """
### Flowering Tips
- PROTECT THE DARK PERIOD - no light leaks!
- Keep humidity <55% to prevent bud rot
- Buds are forming - high water demand
- Watch for nutrient deficiencies
- Don't change light schedule now
""",
    "late_flower": """
### Late Flower Tips
- Begin flush (water only, no nutrients) 2 weeks before harvest
- Watch trichomes: clear → milky → amber
- Harvest when ~20% trichomes are amber for balanced effect
- Reduce watering frequency slightly
""",
    "harvest": """
### Harvest Tips
- Cut plant at base
- Hang dry in dark room, 60°F, 60% humidity
- Dry trim vs wet trim based on preference
- Dry for 7-14 days until stems snap
- Cure in jars for 2-4 weeks minimum
"""
}


def get_stage_tips(stage: str) -> str:
    """Get cultivation tips for current growth stage"""
    return STAGE_TIPS.get(stage.lower(), "")
