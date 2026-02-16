"""
Grok Vision
===========

Plant health analysis using XAI's Grok vision capabilities.
Analyzes webcam images to detect issues and provide recommendations.

Based on PLANT_HEALTH_VISION.md research.
"""

import os
import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import httpx


@dataclass
class VisionAnalysis:
    """Result of a plant vision analysis"""
    timestamp: datetime
    overall_health: str  # "EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL"
    confidence: float
    detected_issues: List[Dict[str, Any]]
    observations: List[str]
    recommendations: List[str]
    raw_response: str
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_health": self.overall_health,
            "confidence": self.confidence,
            "detected_issues": self.detected_issues,
            "observations": self.observations,
            "recommendations": self.recommendations,
            "tokens_used": self.tokens_used,
        }


# Vision analysis system prompt
VISION_SYSTEM_PROMPT = """You are Grok, an AI assistant specializing in cannabis plant health analysis.

Analyze the provided plant image and report on:

1. OVERALL HEALTH: Rate as EXCELLENT, GOOD, FAIR, POOR, or CRITICAL

2. DETECTED ISSUES: Look for these specific problems:
   - Nutrient deficiencies (yellowing, browning, spots)
   - Light stress (bleaching, tacoing leaves)
   - Heat stress (curling, wilting)
   - Overwatering (drooping, dark leaves)
   - Underwatering (dry, crispy, wilting)
   - Pest damage (holes, webbing, visible insects)
   - Mold/mildew (white/gray fuzzy patches)
   - pH problems (multi-colored deficiencies)

3. OBSERVATIONS: Note the plant's current state

4. RECOMMENDATIONS: Specific actionable advice

Respond in JSON format:
{
  "overall_health": "GOOD",
  "confidence": 0.85,
  "detected_issues": [
    {
      "type": "nutrient_deficiency",
      "description": "Minor nitrogen deficiency visible in lower leaves",
      "severity": "low",
      "location": "lower canopy"
    }
  ],
  "observations": [
    "Plant shows healthy new growth",
    "Canopy is filling in nicely",
    "No visible pests"
  ],
  "recommendations": [
    "Consider slight increase in nitrogen in next feeding",
    "Continue current care routine"
  ]
}"""


class GrokVision:
    """
    Grok-powered vision analysis for plant health.

    Uses XAI's multimodal API to analyze plant images.
    """

    XAI_API_URL = "https://api.x.ai/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-2-vision-1212",  # Grok's vision model
    ):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.model = model

        if not self.api_key:
            print("Warning: XAI_API_KEY not set. Vision will use mock responses.")

    async def analyze(
        self,
        image_data: bytes,
        growth_stage: str = "vegetative",
        current_day: int = 1,
        additional_context: Optional[str] = None,
    ) -> VisionAnalysis:
        """
        Analyze a plant image for health issues.

        Args:
            image_data: JPEG image bytes
            growth_stage: Current growth stage for context
            current_day: Day of grow
            additional_context: Any additional context to provide

        Returns:
            VisionAnalysis with detected issues and recommendations
        """
        now = datetime.now()

        # Build context message
        context = f"""Analyzing cannabis plant on Day {current_day} ({growth_stage} stage).
Current date/time: {now.strftime("%B %d, %Y at %I:%M %p")}"""

        if additional_context:
            context += f"\n\nAdditional context: {additional_context}"

        # Call Grok Vision API
        if self.api_key:
            result = await self._call_grok_vision(image_data, context)
        else:
            result = await self._mock_analysis()

        result.timestamp = now
        return result

    async def _call_grok_vision(
        self,
        image_data: bytes,
        context: str,
    ) -> VisionAnalysis:
        """Call XAI Grok Vision API with image"""

        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        # Build multimodal message
        messages = [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": context + "\n\nPlease analyze this plant image:",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.XAI_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,  # Lower temp for more consistent analysis
                        "max_tokens": 1500,
                    },
                )

                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                message = choice["message"]
                response_text = message.get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)

                # Parse JSON response
                analysis = self._parse_response(response_text)
                analysis.tokens_used = tokens
                analysis.raw_response = response_text
                return analysis

        except httpx.HTTPError as e:
            print(f"Vision API error: {e}")
            return await self._mock_analysis(error=str(e))

        except json.JSONDecodeError as e:
            print(f"Failed to parse vision response: {e}")
            return await self._mock_analysis(error=f"Parse error: {e}")

    def _parse_response(self, response_text: str) -> VisionAnalysis:
        """Parse JSON response from Grok"""

        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                # Try parsing entire response as JSON
                json_str = response_text

            data = json.loads(json_str)

            return VisionAnalysis(
                timestamp=datetime.now(),
                overall_health=data.get("overall_health", "UNKNOWN"),
                confidence=data.get("confidence", 0.5),
                detected_issues=data.get("detected_issues", []),
                observations=data.get("observations", []),
                recommendations=data.get("recommendations", []),
                raw_response=response_text,
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Return partial analysis if parsing fails
            return VisionAnalysis(
                timestamp=datetime.now(),
                overall_health="UNKNOWN",
                confidence=0.3,
                detected_issues=[],
                observations=["Unable to fully parse AI response"],
                recommendations=["Manual inspection recommended"],
                raw_response=response_text,
            )

    async def _mock_analysis(self, error: Optional[str] = None) -> VisionAnalysis:
        """Generate mock analysis when API unavailable"""

        if error:
            return VisionAnalysis(
                timestamp=datetime.now(),
                overall_health="UNKNOWN",
                confidence=0.0,
                detected_issues=[],
                observations=[f"API error: {error}"],
                recommendations=["Check API configuration and retry"],
                raw_response=f"Error: {error}",
            )

        # Return UNKNOWN when API is unavailable - no fake data
        return VisionAnalysis(
            timestamp=datetime.now(),
            overall_health="UNKNOWN",
            confidence=0.0,
            detected_issues=[],
            observations=[
                "Vision analysis unavailable - XAI_API_KEY not configured",
            ],
            recommendations=[
                "Set XAI_API_KEY environment variable for real vision analysis",
                "Manual visual inspection recommended",
            ],
            raw_response="API unavailable - XAI_API_KEY not configured",
        )


# =============================================================================
# Issue Detection Helpers
# =============================================================================

ISSUE_TYPES = {
    "nitrogen_deficiency": {
        "symptoms": ["yellowing lower leaves", "pale green", "stunted growth"],
        "severity_indicators": {
            "low": "slight yellowing on oldest leaves",
            "medium": "spreading yellowing, slow growth",
            "high": "severe yellowing, leaf drop",
        },
    },
    "phosphorus_deficiency": {
        "symptoms": ["purple stems", "dark leaves", "slow flowering"],
        "severity_indicators": {
            "low": "slight purple tinge",
            "medium": "noticeable purple, slow growth",
            "high": "severe discoloration, stunted",
        },
    },
    "potassium_deficiency": {
        "symptoms": ["brown leaf edges", "curling", "weak stems"],
        "severity_indicators": {
            "low": "slight browning on tips",
            "medium": "spreading brown edges",
            "high": "severe burning, leaf death",
        },
    },
    "light_stress": {
        "symptoms": ["bleached tops", "tacoing leaves", "foxtailing"],
        "severity_indicators": {
            "low": "slight leaf curl",
            "medium": "noticeable bleaching",
            "high": "severe bleaching, heat damage",
        },
    },
    "overwatering": {
        "symptoms": ["drooping", "dark leaves", "slow growth", "root rot"],
        "severity_indicators": {
            "low": "slight droop",
            "medium": "persistent droop, dark leaves",
            "high": "root rot symptoms, yellowing",
        },
    },
    "underwatering": {
        "symptoms": ["wilting", "dry crispy leaves", "light colored"],
        "severity_indicators": {
            "low": "slight wilt in afternoon",
            "medium": "persistent wilt",
            "high": "crispy leaves, severe stress",
        },
    },
    "pest_damage": {
        "symptoms": ["holes", "webbing", "spots", "visible insects"],
        "severity_indicators": {
            "low": "minor damage, few pests",
            "medium": "spreading damage",
            "high": "severe infestation",
        },
    },
    "mold_mildew": {
        "symptoms": ["white fuzzy patches", "gray mold", "bud rot"],
        "severity_indicators": {
            "low": "small isolated patches",
            "medium": "spreading patches",
            "high": "widespread infection",
        },
    },
}


def get_issue_info(issue_type: str) -> Dict[str, Any]:
    """Get information about an issue type"""
    return ISSUE_TYPES.get(issue_type, {})


# =============================================================================
# Convenience Functions
# =============================================================================

def create_vision_analyzer() -> GrokVision:
    """Create a GrokVision instance"""
    return GrokVision()
