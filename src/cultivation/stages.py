"""
Growth Stage Manager
====================
Cannabis-specific growth stage parameters.

Based on CANNABIS_STAGE_PARAMETERS.md research.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class GrowthStage(Enum):
    """Cannabis growth stages"""
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    TRANSITION = "transition"
    FLOWERING = "flowering"
    LATE_FLOWER = "late_flower"
    HARVEST = "harvest"


@dataclass
class StageParameters:
    """Environmental parameters for a growth stage"""
    stage: GrowthStage
    
    # Temperature (Fahrenheit)
    temp_min_f: float
    temp_max_f: float
    temp_optimal_f: float
    
    # Humidity (%)
    humidity_min: float
    humidity_max: float
    humidity_optimal: float
    
    # VPD (kPa)
    vpd_min: float
    vpd_max: float
    vpd_optimal: float
    
    # Light
    light_hours_on: int
    light_hours_off: int
    ppfd_min: int
    ppfd_max: int
    ppfd_optimal: int
    
    # CO2 (ppm)
    co2_min: int
    co2_max: int
    co2_optimal: int
    
    # Soil moisture (%)
    soil_moisture_min: float
    soil_moisture_max: float
    soil_moisture_optimal: float
    
    # pH and EC
    ph_min: float
    ph_max: float
    ec_min: float
    ec_max: float
    
    # Duration
    typical_days_min: int
    typical_days_max: int
    
    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "temperature": {
                "min_f": self.temp_min_f,
                "max_f": self.temp_max_f,
                "optimal_f": self.temp_optimal_f,
            },
            "humidity": {
                "min": self.humidity_min,
                "max": self.humidity_max,
                "optimal": self.humidity_optimal,
            },
            "vpd": {
                "min_kpa": self.vpd_min,
                "max_kpa": self.vpd_max,
                "optimal_kpa": self.vpd_optimal,
            },
            "light": {
                "hours_on": self.light_hours_on,
                "hours_off": self.light_hours_off,
                "schedule": f"{self.light_hours_on}/{self.light_hours_off}",
                "ppfd_min": self.ppfd_min,
                "ppfd_max": self.ppfd_max,
                "ppfd_optimal": self.ppfd_optimal,
            },
            "co2": {
                "min_ppm": self.co2_min,
                "max_ppm": self.co2_max,
                "optimal_ppm": self.co2_optimal,
            },
            "soil_moisture": {
                "min": self.soil_moisture_min,
                "max": self.soil_moisture_max,
                "optimal": self.soil_moisture_optimal,
            },
            "ph": {"min": self.ph_min, "max": self.ph_max},
            "ec": {"min": self.ec_min, "max": self.ec_max},
            "duration_days": {
                "min": self.typical_days_min,
                "max": self.typical_days_max,
            },
        }


# Stage parameter definitions based on research
STAGE_PARAMETERS = {
    GrowthStage.GERMINATION: StageParameters(
        stage=GrowthStage.GERMINATION,
        temp_min_f=70, temp_max_f=78, temp_optimal_f=75,
        humidity_min=70, humidity_max=90, humidity_optimal=80,
        vpd_min=0.2, vpd_max=0.5, vpd_optimal=0.3,
        light_hours_on=0, light_hours_off=24, ppfd_min=0, ppfd_max=0, ppfd_optimal=0,
        co2_min=400, co2_max=600, co2_optimal=400,
        soil_moisture_min=60, soil_moisture_max=80, soil_moisture_optimal=70,
        ph_min=6.0, ph_max=7.0, ec_min=0.0, ec_max=0.5,
        typical_days_min=2, typical_days_max=7,
    ),
    GrowthStage.SEEDLING: StageParameters(
        stage=GrowthStage.SEEDLING,
        temp_min_f=70, temp_max_f=78, temp_optimal_f=75,
        humidity_min=65, humidity_max=70, humidity_optimal=68,
        vpd_min=0.4, vpd_max=0.8, vpd_optimal=0.6,
        light_hours_on=18, light_hours_off=6, ppfd_min=200, ppfd_max=400, ppfd_optimal=300,
        co2_min=400, co2_max=800, co2_optimal=600,
        # NOTE: Ecowitt WH51 in our airy soil/perlite mix reads "sweet spot" around ~31-33%.
        # Historical grow logs and watering automation use 30% as the "water now" threshold.
        soil_moisture_min=30, soil_moisture_max=45, soil_moisture_optimal=32,
        ph_min=6.0, ph_max=6.5, ec_min=0.4, ec_max=0.8,
        typical_days_min=7, typical_days_max=14,
    ),
    GrowthStage.VEGETATIVE: StageParameters(
        stage=GrowthStage.VEGETATIVE,
        temp_min_f=70, temp_max_f=85, temp_optimal_f=77,
        humidity_min=40, humidity_max=60, humidity_optimal=50,
        vpd_min=0.8, vpd_max=1.2, vpd_optimal=1.0,
        light_hours_on=18, light_hours_off=6, ppfd_min=400, ppfd_max=600, ppfd_optimal=500,
        co2_min=800, co2_max=1200, co2_optimal=1000,
        soil_moisture_min=30, soil_moisture_max=60, soil_moisture_optimal=45,
        ph_min=5.8, ph_max=6.2, ec_min=1.0, ec_max=1.8,
        typical_days_min=14, typical_days_max=60,
    ),
    GrowthStage.TRANSITION: StageParameters(
        stage=GrowthStage.TRANSITION,
        temp_min_f=68, temp_max_f=82, temp_optimal_f=75,
        humidity_min=40, humidity_max=55, humidity_optimal=48,
        vpd_min=1.0, vpd_max=1.4, vpd_optimal=1.2,
        light_hours_on=12, light_hours_off=12, ppfd_min=500, ppfd_max=700, ppfd_optimal=600,
        co2_min=800, co2_max=1200, co2_optimal=1000,
        soil_moisture_min=30, soil_moisture_max=55, soil_moisture_optimal=42,
        ph_min=5.8, ph_max=6.3, ec_min=1.2, ec_max=2.0,
        typical_days_min=7, typical_days_max=14,
    ),
    GrowthStage.FLOWERING: StageParameters(
        stage=GrowthStage.FLOWERING,
        temp_min_f=65, temp_max_f=80, temp_optimal_f=73,
        humidity_min=40, humidity_max=50, humidity_optimal=45,
        vpd_min=1.0, vpd_max=1.5, vpd_optimal=1.2,
        light_hours_on=12, light_hours_off=12, ppfd_min=600, ppfd_max=900, ppfd_optimal=750,
        co2_min=1000, co2_max=1500, co2_optimal=1200,
        soil_moisture_min=25, soil_moisture_max=50, soil_moisture_optimal=38,
        ph_min=6.0, ph_max=6.5, ec_min=1.5, ec_max=2.2,
        typical_days_min=42, typical_days_max=70,
    ),
    GrowthStage.LATE_FLOWER: StageParameters(
        stage=GrowthStage.LATE_FLOWER,
        temp_min_f=65, temp_max_f=75, temp_optimal_f=70,
        humidity_min=30, humidity_max=40, humidity_optimal=35,
        vpd_min=1.2, vpd_max=1.6, vpd_optimal=1.4,
        light_hours_on=12, light_hours_off=12, ppfd_min=600, ppfd_max=800, ppfd_optimal=700,
        co2_min=800, co2_max=1200, co2_optimal=1000,
        soil_moisture_min=20, soil_moisture_max=45, soil_moisture_optimal=32,
        ph_min=6.0, ph_max=6.5, ec_min=1.0, ec_max=1.8,
        typical_days_min=14, typical_days_max=21,
    ),
    GrowthStage.HARVEST: StageParameters(
        stage=GrowthStage.HARVEST,
        temp_min_f=60, temp_max_f=70, temp_optimal_f=65,
        humidity_min=45, humidity_max=55, humidity_optimal=50,
        vpd_min=0.8, vpd_max=1.2, vpd_optimal=1.0,
        light_hours_on=0, light_hours_off=24, ppfd_min=0, ppfd_max=0, ppfd_optimal=0,
        co2_min=400, co2_max=600, co2_optimal=400,
        soil_moisture_min=0, soil_moisture_max=0, soil_moisture_optimal=0,
        ph_min=6.0, ph_max=6.5, ec_min=0.0, ec_max=0.0,
        typical_days_min=1, typical_days_max=3,
    ),
}


def get_stage_parameters(stage: GrowthStage | str) -> StageParameters:
    """Get parameters for a growth stage."""
    if isinstance(stage, str):
        stage = GrowthStage(stage.lower())
    return STAGE_PARAMETERS[stage]


def determine_stage_from_day(grow_day: int, photoperiod: str = "18/6") -> GrowthStage:
    """Estimate growth stage from grow day (approximate)."""
    if grow_day <= 7:
        return GrowthStage.GERMINATION
    elif grow_day <= 21:
        return GrowthStage.SEEDLING
    elif photoperiod == "18/6":
        return GrowthStage.VEGETATIVE
    elif grow_day <= 7 + 21 + 14:  # First 2 weeks of 12/12
        return GrowthStage.TRANSITION
    elif grow_day <= 7 + 21 + 14 + 56:  # 8 weeks of flower
        return GrowthStage.FLOWERING
    else:
        return GrowthStage.LATE_FLOWER


def check_parameters_in_range(
    stage: GrowthStage | str,
    temp_f: Optional[float] = None,
    humidity: Optional[float] = None,
    vpd: Optional[float] = None,
    ppfd: Optional[int] = None,
    soil_moisture: Optional[float] = None,
) -> dict:
    """Check if parameters are in range for the stage."""
    params = get_stage_parameters(stage)
    results = {}
    
    if temp_f is not None:
        in_range = params.temp_min_f <= temp_f <= params.temp_max_f
        results["temperature"] = {
            "value": temp_f,
            "in_range": in_range,
            "optimal": params.temp_optimal_f,
            "status": "optimal" if abs(temp_f - params.temp_optimal_f) < 3 else ("acceptable" if in_range else "out_of_range"),
        }
    
    if humidity is not None:
        in_range = params.humidity_min <= humidity <= params.humidity_max
        results["humidity"] = {
            "value": humidity,
            "in_range": in_range,
            "optimal": params.humidity_optimal,
            "status": "optimal" if abs(humidity - params.humidity_optimal) < 5 else ("acceptable" if in_range else "out_of_range"),
        }
    
    if vpd is not None:
        in_range = params.vpd_min <= vpd <= params.vpd_max
        results["vpd"] = {
            "value": vpd,
            "in_range": in_range,
            "optimal": params.vpd_optimal,
            "status": "optimal" if abs(vpd - params.vpd_optimal) < 0.15 else ("acceptable" if in_range else "out_of_range"),
        }
    
    if ppfd is not None:
        in_range = params.ppfd_min <= ppfd <= params.ppfd_max
        results["ppfd"] = {
            "value": ppfd,
            "in_range": in_range,
            "optimal": params.ppfd_optimal,
            "status": "optimal" if abs(ppfd - params.ppfd_optimal) < 50 else ("acceptable" if in_range else "out_of_range"),
        }
    
    if soil_moisture is not None:
        in_range = params.soil_moisture_min <= soil_moisture <= params.soil_moisture_max
        results["soil_moisture"] = {
            "value": soil_moisture,
            "in_range": in_range,
            "optimal": params.soil_moisture_optimal,
            "status": "optimal" if abs(soil_moisture - params.soil_moisture_optimal) < 10 else ("acceptable" if in_range else "out_of_range"),
        }
    
    return results
