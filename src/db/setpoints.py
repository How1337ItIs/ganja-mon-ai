"""
Setpoints and Growth Stage Configuration
=========================================
Target environmental parameters for each growth stage.
Based on SmartGrow DataControl's setpoints pattern.

Setpoints define the "ideal" values that the AI aims to maintain.
When sensor readings deviate from setpoints, the AI takes corrective action.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# Import from models - handle circular import gracefully
try:
    from .models import GrowthStage, Photoperiod
except ImportError:
    # Define locally if models not available (for standalone use)
    class GrowthStage(str, Enum):
        SEEDLING = "seedling"
        VEGETATIVE = "vegetative"
        TRANSITION = "transition"
        FLOWERING = "flowering"
        LATE_FLOWER = "late_flower"
        HARVEST = "harvest"

    class Photoperiod(str, Enum):
        VEG_18_6 = "18/6"
        FLOWER_12_12 = "12/12"
        DARK_48 = "48/0"


@dataclass
class VPDRange:
    """Vapor Pressure Deficit targets in kPa"""
    min: float
    target: float
    max: float

    def in_range(self, value: float) -> bool:
        """Check if value is within acceptable range"""
        return self.min <= value <= self.max

    def deviation(self, value: float) -> float:
        """Calculate deviation from target (negative = too low, positive = too high)"""
        return value - self.target

    def deviation_percent(self, value: float) -> float:
        """Calculate percentage deviation from target"""
        if self.target == 0:
            return 0
        return ((value - self.target) / self.target) * 100


@dataclass
class TemperatureRange:
    """Temperature targets in both F and C"""
    min_f: float
    target_f: float
    max_f: float

    @property
    def min_c(self) -> float:
        return (self.min_f - 32) * 5 / 9

    @property
    def target_c(self) -> float:
        return (self.target_f - 32) * 5 / 9

    @property
    def max_c(self) -> float:
        return (self.max_f - 32) * 5 / 9

    def in_range_f(self, value: float) -> bool:
        return self.min_f <= value <= self.max_f

    def in_range_c(self, value: float) -> bool:
        return self.min_c <= value <= self.max_c


@dataclass
class HumidityRange:
    """Relative humidity targets in percent"""
    min: float
    target: float
    max: float

    def in_range(self, value: float) -> bool:
        return self.min <= value <= self.max


@dataclass
class LightSettings:
    """Light configuration for growth stage"""
    photoperiod: Photoperiod
    hours_on: int
    hours_off: int
    ppfd_target: int        # μmol/m²/s
    ppfd_min: int
    ppfd_max: int
    dli_target: float       # mol/m²/day (Daily Light Integral)

    @property
    def schedule_str(self) -> str:
        return f"{self.hours_on}/{self.hours_off}"


@dataclass
class SubstrateTargets:
    """Root zone/substrate targets"""
    moisture_min: float     # Percent
    moisture_target: float
    moisture_max: float
    ec_target: float        # mS/cm (electrical conductivity)
    ec_min: float
    ec_max: float
    ph_target: float
    ph_min: float
    ph_max: float


@dataclass
class CO2Targets:
    """CO2 supplementation targets"""
    ppm_target: int
    ppm_min: int
    ppm_max: int
    supplement_enabled: bool = False


@dataclass
class GrowthStageSetpoints:
    """
    Complete setpoint configuration for a growth stage.

    These values define the "ideal" conditions the AI should maintain.
    Based on research and best practices for cannabis cultivation.
    """
    stage: GrowthStage
    description: str

    # Duration hints
    typical_days: int
    min_days: int
    max_days: int

    # Environmental targets
    vpd: VPDRange
    temperature_day: TemperatureRange
    temperature_night: TemperatureRange
    humidity: HumidityRange
    light: LightSettings
    substrate: SubstrateTargets
    co2: CO2Targets

    # Stage-specific notes
    key_objectives: list[str] = field(default_factory=list)
    warning_signs: list[str] = field(default_factory=list)
    transition_triggers: list[str] = field(default_factory=list)


# =============================================================================
# Default Setpoints for Each Growth Stage
# Based on cannabis cultivation research and VPD charts
# =============================================================================

SEEDLING_SETPOINTS = GrowthStageSetpoints(
    stage=GrowthStage.SEEDLING,
    description="Early growth phase - focus on root development and gentle conditions",
    typical_days=14,
    min_days=7,
    max_days=21,

    vpd=VPDRange(min=0.4, target=0.6, max=0.8),

    temperature_day=TemperatureRange(min_f=70, target_f=77, max_f=82),
    temperature_night=TemperatureRange(min_f=65, target_f=72, max_f=77),

    humidity=HumidityRange(min=65, target=70, max=80),

    light=LightSettings(
        photoperiod=Photoperiod.VEG_18_6,
        hours_on=18,
        hours_off=6,
        ppfd_target=200,
        ppfd_min=100,
        ppfd_max=300,
        dli_target=12.96,  # 200 * 18 * 3600 / 1000000
    ),

    substrate=SubstrateTargets(
        moisture_min=50,
        moisture_target=65,
        moisture_max=80,
        ec_target=0.8,
        ec_min=0.4,
        ec_max=1.2,
        ph_target=6.2,
        ph_min=5.8,
        ph_max=6.5,
    ),

    co2=CO2Targets(
        ppm_target=400,
        ppm_min=350,
        ppm_max=500,
        supplement_enabled=False,
    ),

    key_objectives=[
        "Establish healthy root system",
        "Develop first true leaves",
        "Maintain high humidity for young plant",
    ],
    warning_signs=[
        "Damping off (stem rot at soil line)",
        "Stretching (light too far/weak)",
        "Yellowing cotyledons (normal if true leaves healthy)",
    ],
    transition_triggers=[
        "3-4 sets of true leaves developed",
        "Root system visible at container edges",
        "Stem thickening and strengthening",
    ],
)

VEGETATIVE_SETPOINTS = GrowthStageSetpoints(
    stage=GrowthStage.VEGETATIVE,
    description="Rapid growth phase - maximize vegetative development",
    typical_days=28,
    min_days=14,
    max_days=56,

    vpd=VPDRange(min=0.8, target=1.0, max=1.2),

    temperature_day=TemperatureRange(min_f=72, target_f=80, max_f=86),
    temperature_night=TemperatureRange(min_f=65, target_f=72, max_f=78),

    humidity=HumidityRange(min=50, target=60, max=70),

    light=LightSettings(
        photoperiod=Photoperiod.VEG_18_6,
        hours_on=18,
        hours_off=6,
        ppfd_target=500,
        ppfd_min=400,
        ppfd_max=700,
        dli_target=32.4,  # 500 * 18 * 3600 / 1000000
    ),

    substrate=SubstrateTargets(
        moisture_min=40,
        moisture_target=55,
        moisture_max=70,
        ec_target=1.4,
        ec_min=1.0,
        ec_max=1.8,
        ph_target=6.0,
        ph_min=5.8,
        ph_max=6.5,
    ),

    co2=CO2Targets(
        ppm_target=800,
        ppm_min=400,
        ppm_max=1200,
        supplement_enabled=True,
    ),

    key_objectives=[
        "Maximize leaf area for photosynthesis",
        "Develop strong branching structure",
        "Training and topping for canopy management",
        "Build nutrient reserves for flowering",
    ],
    warning_signs=[
        "Nitrogen deficiency (lower leaf yellowing)",
        "Light burn (bleaching on top leaves)",
        "Overwatering (droopy, dark green leaves)",
        "Underwatering (wilting, light green leaves)",
    ],
    transition_triggers=[
        "Desired plant size reached",
        "Showing pre-flowers (sex determination)",
        "Space constraints require flip",
        "Minimum 4-6 weeks in veg completed",
    ],
)

TRANSITION_SETPOINTS = GrowthStageSetpoints(
    stage=GrowthStage.TRANSITION,
    description="Stretch phase - plant adjusts to flowering light cycle",
    typical_days=14,
    min_days=7,
    max_days=21,

    vpd=VPDRange(min=0.9, target=1.1, max=1.3),

    temperature_day=TemperatureRange(min_f=72, target_f=78, max_f=84),
    temperature_night=TemperatureRange(min_f=64, target_f=70, max_f=75),

    humidity=HumidityRange(min=45, target=55, max=65),

    light=LightSettings(
        photoperiod=Photoperiod.FLOWER_12_12,
        hours_on=12,
        hours_off=12,
        ppfd_target=600,
        ppfd_min=500,
        ppfd_max=800,
        dli_target=25.92,  # 600 * 12 * 3600 / 1000000
    ),

    substrate=SubstrateTargets(
        moisture_min=40,
        moisture_target=50,
        moisture_max=65,
        ec_target=1.6,
        ec_min=1.2,
        ec_max=2.0,
        ph_target=6.2,
        ph_min=5.8,
        ph_max=6.5,
    ),

    co2=CO2Targets(
        ppm_target=1000,
        ppm_min=600,
        ppm_max=1400,
        supplement_enabled=True,
    ),

    key_objectives=[
        "Manage stretch (can double in height)",
        "Support branches for bud weight",
        "Begin bloom nutrient transition",
        "CRITICAL: Maintain uninterrupted dark period",
    ],
    warning_signs=[
        "Light leaks during dark period (can cause hermaphroditism)",
        "Excessive stretch (light too weak/far)",
        "Nutrient burn from veg nutrients",
    ],
    transition_triggers=[
        "Stretch has slowed/stopped",
        "First pistils (white hairs) visible",
        "2 weeks since light flip",
    ],
)

FLOWERING_SETPOINTS = GrowthStageSetpoints(
    stage=GrowthStage.FLOWERING,
    description="Bud development phase - maximize flower production",
    typical_days=42,
    min_days=35,
    max_days=56,

    vpd=VPDRange(min=1.0, target=1.2, max=1.5),

    temperature_day=TemperatureRange(min_f=68, target_f=76, max_f=82),
    temperature_night=TemperatureRange(min_f=62, target_f=68, max_f=74),

    humidity=HumidityRange(min=40, target=50, max=55),

    light=LightSettings(
        photoperiod=Photoperiod.FLOWER_12_12,
        hours_on=12,
        hours_off=12,
        ppfd_target=800,
        ppfd_min=600,
        ppfd_max=1000,
        dli_target=34.56,  # 800 * 12 * 3600 / 1000000
    ),

    substrate=SubstrateTargets(
        moisture_min=35,
        moisture_target=45,
        moisture_max=60,
        ec_target=1.8,
        ec_min=1.4,
        ec_max=2.2,
        ph_target=6.3,
        ph_min=6.0,
        ph_max=6.8,
    ),

    co2=CO2Targets(
        ppm_target=1200,
        ppm_min=800,
        ppm_max=1500,
        supplement_enabled=True,
    ),

    key_objectives=[
        "Maximize bud density and size",
        "Maintain optimal VPD for trichome production",
        "Support heavy branches",
        "CRITICAL: No light interruptions",
    ],
    warning_signs=[
        "Bud rot (gray mold in dense buds)",
        "Powdery mildew (white patches on leaves)",
        "Nutrient lockout (pH issues)",
        "Hermaphroditism (bananas/nanners)",
    ],
    transition_triggers=[
        "Trichomes turning milky/cloudy",
        "Most pistils darkened and curled",
        "Calyxes swelling",
        "8+ weeks since flip (strain dependent)",
    ],
)

LATE_FLOWER_SETPOINTS = GrowthStageSetpoints(
    stage=GrowthStage.LATE_FLOWER,
    description="Ripening/flush phase - final trichome development",
    typical_days=14,
    min_days=10,
    max_days=21,

    vpd=VPDRange(min=1.0, target=1.3, max=1.6),

    temperature_day=TemperatureRange(min_f=65, target_f=74, max_f=80),
    temperature_night=TemperatureRange(min_f=58, target_f=65, max_f=70),

    humidity=HumidityRange(min=35, target=45, max=50),

    light=LightSettings(
        photoperiod=Photoperiod.FLOWER_12_12,
        hours_on=12,
        hours_off=12,
        ppfd_target=700,
        ppfd_min=500,
        ppfd_max=900,
        dli_target=30.24,
    ),

    substrate=SubstrateTargets(
        moisture_min=30,
        moisture_target=40,
        moisture_max=55,
        ec_target=0.6,  # Flushing - reduced nutrients
        ec_min=0.2,
        ec_max=1.0,
        ph_target=6.0,
        ph_min=5.8,
        ph_max=6.5,
    ),

    co2=CO2Targets(
        ppm_target=600,
        ppm_min=400,
        ppm_max=800,
        supplement_enabled=False,  # Reduce for flush
    ),

    key_objectives=[
        "Flush excess nutrients for smooth smoke",
        "Monitor trichome development daily",
        "Lower temps for color expression",
        "Reduce humidity to prevent mold",
    ],
    warning_signs=[
        "Bud rot (inspect daily)",
        "Premature harvest (clear trichomes)",
        "Over-ripening (amber trichomes excessive)",
    ],
    transition_triggers=[
        "Trichomes 70-80% milky, 10-20% amber",
        "Fan leaves yellowing and falling",
        "No new pistil growth",
    ],
)

HARVEST_SETPOINTS = GrowthStageSetpoints(
    stage=GrowthStage.HARVEST,
    description="Harvest and initial dry - final preparations",
    typical_days=1,
    min_days=1,
    max_days=3,

    vpd=VPDRange(min=1.0, target=1.2, max=1.4),

    temperature_day=TemperatureRange(min_f=60, target_f=68, max_f=72),
    temperature_night=TemperatureRange(min_f=58, target_f=65, max_f=70),

    humidity=HumidityRange(min=50, target=55, max=60),  # For drying

    light=LightSettings(
        photoperiod=Photoperiod.FLOWER_12_12,
        hours_on=0,  # Optional 48h darkness pre-harvest
        hours_off=24,
        ppfd_target=0,
        ppfd_min=0,
        ppfd_max=0,
        dli_target=0,
    ),

    substrate=SubstrateTargets(
        moisture_min=0,
        moisture_target=0,
        moisture_max=0,
        ec_target=0,
        ec_min=0,
        ec_max=0,
        ph_target=0,
        ph_min=0,
        ph_max=0,
    ),

    co2=CO2Targets(
        ppm_target=400,
        ppm_min=350,
        ppm_max=500,
        supplement_enabled=False,
    ),

    key_objectives=[
        "Optional: 48 hour darkness period",
        "Harvest at optimal trichome ripeness",
        "Trim and hang for drying",
        "Document final yield",
    ],
    warning_signs=[
        "Mold development post-harvest",
        "Too-fast drying (brittle)",
        "Too-slow drying (mold risk)",
    ],
    transition_triggers=[
        "Plant harvested - grow cycle complete",
    ],
)


# =============================================================================
# Setpoints Registry
# =============================================================================

STAGE_SETPOINTS: dict[GrowthStage, GrowthStageSetpoints] = {
    GrowthStage.SEEDLING: SEEDLING_SETPOINTS,
    GrowthStage.VEGETATIVE: VEGETATIVE_SETPOINTS,
    GrowthStage.TRANSITION: TRANSITION_SETPOINTS,
    GrowthStage.FLOWERING: FLOWERING_SETPOINTS,
    GrowthStage.LATE_FLOWER: LATE_FLOWER_SETPOINTS,
    GrowthStage.HARVEST: HARVEST_SETPOINTS,
}


def get_setpoints(stage: GrowthStage) -> GrowthStageSetpoints:
    """Get setpoints for a growth stage"""
    return STAGE_SETPOINTS[stage]


def get_current_setpoints(stage: GrowthStage, is_day: bool = True) -> dict:
    """
    Get current target values as a flat dict for easy comparison.

    Args:
        stage: Current growth stage
        is_day: Whether it's currently the light period

    Returns:
        Dict with all target values
    """
    sp = get_setpoints(stage)
    temp_range = sp.temperature_day if is_day else sp.temperature_night

    return {
        "vpd_target": sp.vpd.target,
        "vpd_min": sp.vpd.min,
        "vpd_max": sp.vpd.max,
        "temp_target_f": temp_range.target_f,
        "temp_min_f": temp_range.min_f,
        "temp_max_f": temp_range.max_f,
        "humidity_target": sp.humidity.target,
        "humidity_min": sp.humidity.min,
        "humidity_max": sp.humidity.max,
        "ppfd_target": sp.light.ppfd_target,
        "ppfd_min": sp.light.ppfd_min,
        "ppfd_max": sp.light.ppfd_max,
        "moisture_target": sp.substrate.moisture_target,
        "moisture_min": sp.substrate.moisture_min,
        "moisture_max": sp.substrate.moisture_max,
        "ec_target": sp.substrate.ec_target,
        "ph_target": sp.substrate.ph_target,
        "co2_target": sp.co2.ppm_target,
        "photoperiod": sp.light.photoperiod.value,
    }
