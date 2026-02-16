"""
VPD (Vapor Pressure Deficit) Calculator
========================================
The KEY metric for cannabis cultivation.

VPD measures the "drying power" of the air:
- Too low: Risk of mold, poor transpiration
- Optimal: Happy plants, efficient nutrient uptake
- Too high: Stress, stomata close, slow growth

Based on CANNABIS_STAGE_PARAMETERS.md research.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class VPDStatus(Enum):
    """VPD status classification"""
    CRITICAL_LOW = "critical_low"
    LOW = "low"
    OPTIMAL_LOW = "optimal_low"
    OPTIMAL = "optimal"
    OPTIMAL_HIGH = "optimal_high"
    HIGH = "high"
    CRITICAL_HIGH = "critical_high"


@dataclass
class VPDReading:
    """VPD calculation result"""
    vpd_kpa: float
    status: VPDStatus
    recommendation: str
    air_temp_f: float
    humidity_percent: float
    leaf_temp_f: Optional[float] = None
    saturation_vapor_pressure_air: float = 0.0
    saturation_vapor_pressure_leaf: float = 0.0
    actual_vapor_pressure: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "vpd_kpa": round(self.vpd_kpa, 3),
            "status": self.status.value,
            "recommendation": self.recommendation,
            "air_temp_f": self.air_temp_f,
            "humidity_percent": self.humidity_percent,
            "leaf_temp_f": self.leaf_temp_f,
        }


def fahrenheit_to_celsius(f: float) -> float:
    """Convert Fahrenheit to Celsius"""
    return (f - 32) * 5/9


def saturation_vapor_pressure(temp_c: float) -> float:
    """Calculate saturation vapor pressure (SVP) using Tetens equation."""
    return 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))


def calculate_vpd(
    air_temp_f: float,
    humidity_percent: float,
    leaf_temp_f: Optional[float] = None,
    leaf_offset_f: float = 3.0,
) -> VPDReading:
    """
    Calculate VPD (Vapor Pressure Deficit).
    
    Args:
        air_temp_f: Air temperature in Fahrenheit
        humidity_percent: Relative humidity (0-100)
        leaf_temp_f: Leaf temperature in Fahrenheit (optional)
        leaf_offset_f: If leaf_temp not provided, assume leaf is this many F cooler
        
    Returns:
        VPDReading with calculated VPD and status
    """
    air_temp_c = fahrenheit_to_celsius(air_temp_f)
    
    if leaf_temp_f is None:
        leaf_temp_f = air_temp_f - leaf_offset_f
    leaf_temp_c = fahrenheit_to_celsius(leaf_temp_f)
    
    svp_air = saturation_vapor_pressure(air_temp_c)
    svp_leaf = saturation_vapor_pressure(leaf_temp_c)
    avp = svp_air * (humidity_percent / 100.0)
    vpd = max(0, svp_leaf - avp)
    
    status, recommendation = vpd_status(vpd)
    
    return VPDReading(
        vpd_kpa=round(vpd, 3),
        status=status,
        recommendation=recommendation,
        air_temp_f=air_temp_f,
        humidity_percent=humidity_percent,
        leaf_temp_f=leaf_temp_f,
        saturation_vapor_pressure_air=round(svp_air, 4),
        saturation_vapor_pressure_leaf=round(svp_leaf, 4),
        actual_vapor_pressure=round(avp, 4),
    )


def vpd_status(vpd_kpa: float, growth_stage: str = "vegetative") -> Tuple[VPDStatus, str]:
    """Determine VPD status and recommendation."""
    stage_lower = growth_stage.lower()
    
    if stage_lower in ("seedling", "clone", "propagation"):
        optimal_low, optimal_high = 0.4, 0.8
    elif stage_lower in ("vegetative", "veg"):
        optimal_low, optimal_high = 0.8, 1.2
    elif stage_lower in ("flowering", "flower", "bloom"):
        optimal_low, optimal_high = 1.0, 1.5
    elif stage_lower in ("late_flower", "late_flowering", "ripening"):
        optimal_low, optimal_high = 1.2, 1.6
    else:
        optimal_low, optimal_high = 0.8, 1.2
    
    if vpd_kpa < 0.4:
        return (VPDStatus.CRITICAL_LOW, "CRITICAL: VPD too low! Risk of mold. Reduce humidity or increase temperature.")
    elif vpd_kpa < 0.7:
        return (VPDStatus.LOW, "VPD low. Consider reducing humidity for better transpiration.")
    elif vpd_kpa < optimal_low:
        return (VPDStatus.OPTIMAL_LOW, "VPD acceptable for seedlings/clones.")
    elif vpd_kpa <= optimal_high:
        return (VPDStatus.OPTIMAL, f"VPD optimal for {growth_stage}. Plants are happy!")
    elif vpd_kpa <= 1.5:
        return (VPDStatus.OPTIMAL_HIGH, "VPD in upper optimal range. Good for flowering.")
    elif vpd_kpa <= 1.8:
        return (VPDStatus.HIGH, "VPD slightly high. Monitor for leaf curl. Consider increasing humidity.")
    else:
        return (VPDStatus.CRITICAL_HIGH, "CRITICAL: VPD too high! Plants may stop growing. Increase humidity.")


def calculate_target_humidity(air_temp_f: float, target_vpd_kpa: float, leaf_offset_f: float = 3.0) -> float:
    """Calculate humidity needed to achieve target VPD."""
    air_temp_c = fahrenheit_to_celsius(air_temp_f)
    leaf_temp_c = fahrenheit_to_celsius(air_temp_f - leaf_offset_f)
    
    svp_air = saturation_vapor_pressure(air_temp_c)
    svp_leaf = saturation_vapor_pressure(leaf_temp_c)
    
    target_humidity = ((svp_leaf - target_vpd_kpa) / svp_air) * 100
    return max(0, min(100, target_humidity))
