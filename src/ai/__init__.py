"""
Grok AI Brain
=============

AI decision engine for cannabis cultivation.
Uses XAI's Grok API with tool calling for autonomous plant care.

Usage:
    from src.ai import GrokBrain, ToolExecutor, GROW_TOOLS

    executor = ToolExecutor(safe_actuators, camera, repo)
    brain = GrokBrain(tool_executor=executor)

    result = await brain.decide(
        sensors=sensor_data,
        devices=device_states,
        current_day=49,
        growth_stage="flowering",
        photoperiod="12/12",
        is_dark_period=False
    )

    print(result.output_text)  # Grok's response with [think] blocks
    print(result.actions_taken)  # List of tool calls executed
"""

from .brain import GrokBrain, DecisionResult, create_brain
from .tools import GROW_TOOLS, ToolExecutor, ToolResult
from .prompts import (
    get_system_prompt,
    get_decision_prompt,
    get_stage_tips,
    STAGE_TIPS
)
from .vision import GrokVision, VisionAnalysis, create_vision_analyzer

__all__ = [
    # Brain
    "GrokBrain",
    "DecisionResult",
    "create_brain",
    # Vision
    "GrokVision",
    "VisionAnalysis",
    "create_vision_analyzer",
    # Tools
    "GROW_TOOLS",
    "ToolExecutor",
    "ToolResult",
    # Prompts
    "get_system_prompt",
    "get_decision_prompt",
    "get_stage_tips",
    "STAGE_TIPS",
]
