"""
Visual Health Analyzer
======================
Uses Grok vision API to perform dedicated plant health audits.
Also assesses image quality to ensure the camera is useful.
"""

from __future__ import annotations

import base64
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default vision model matching agent.py
VISION_MODEL = "grok-4-0709"
XAI_API_BASE = "https://api.x.ai/v1"

# Structured health audit prompt — comprehensive plant inspection
HEALTH_AUDIT_PROMPT = """You are an expert cannabis cultivation diagnostician reviewing a grow room image.
Perform a thorough visual health audit of the plant(s) visible.

Current grow info:
- Strain: {strain}
- Growth stage: {stage}
- Day: {grow_day}
- Recent sensor data: Temp {temp_f:.1f}F, Humidity {humidity:.1f}%, VPD {vpd:.2f} kPa

Analyze the image systematically and respond in EXACTLY this JSON format:

{{
  "image_usable": true,
  "image_issues": [],
  "plant_visible": true,
  "health_score": 8,
  "findings": [
    {{
      "category": "leaf_color",
      "observation": "what you see",
      "severity": "info|warning|critical",
      "likely_cause": "diagnosis",
      "action": "recommended fix"
    }}
  ],
  "overall_assessment": "one paragraph summary"
}}

Check ALL of these systematically — report ONLY what you actually observe:

**Leaf Analysis:**
- Color: uniform green? Yellowing (which leaves — top/bottom/tips/interveinal)?
- Spots: brown, black, white, rust-colored? Pattern?
- Edges: burnt tips? Crispy margins? Curling up (taco-ing) or down (claw)?
- Texture: papery? Glossy? Blistered?
- Droop: leaves hanging down (overwater/underwater)? Praying up (happy)?

**Structural Analysis:**
- Internode spacing: tight (good light) or stretched (light-hungry)?
- Stem color: green? Purple? Thin/thick?
- New growth: vigorous? Stunted? Twisted?
- Symmetry: even growth or lopsided?

**Root Zone / Media:**
- Soil surface: dry/moist/wet? Algae/mold? Salt buildup?
- Pot: appropriate size? Root-bound signs?

**Pest/Disease Indicators:**
- Webs, eggs, or insects visible?
- Powdery mildew (white powder on leaves)?
- Bud rot (grey/brown mushy patches)?
- Fungus gnats (small flies near soil)?

**Stage-Appropriate Check ({stage}):**
- Does the plant look right for day {grow_day} of {stage}?
- Any signs it should transition to the next stage?

**Common Deficiency Patterns:**
- Nitrogen (N): lower leaves yellow first, moves up
- Phosphorus (P): dark leaves, purple stems, slow growth
- Potassium (K): brown/burnt leaf edges, lower leaves
- Calcium (Ca): brown spots on new growth, curled tips
- Magnesium (Mg): interveinal yellowing on older leaves
- Iron (Fe): interveinal yellowing on NEW leaves
- pH lockout: multiple deficiency symptoms at once

If the image is blurry, dark, overexposed, or the plant is not clearly visible,
set "image_usable" to false and list the issues in "image_issues".

Be precise. If you can't tell, say so. Don't hallucinate problems that aren't visible."""

# Image quality assessment prompt — separate, cheaper call
IMAGE_QUALITY_PROMPT = """Assess this grow room camera image for quality. Respond in JSON:

{{
  "usable_for_analysis": true,
  "plant_visible": true,
  "plant_coverage_pct": 60,
  "issues": [],
  "suggestions": [],
  "brightness": "good",
  "focus": "good",
  "color_accuracy": "good"
}}

Check:
1. Is a cannabis plant clearly visible and in focus?
2. What percentage of the frame does the plant occupy? (>30% is good)
3. Is the image too dark, too bright, or washed out by grow lights?
4. Is the image blurry or out of focus?
5. Are colors accurate or shifted (e.g., pink/purple from LED blurb)?
6. Can you see leaf detail well enough to spot yellowing/spots/pests?
7. Is the camera angle good (shows leaves and canopy)?

For each issue found, add to "issues" array.
For each improvement, add to "suggestions" (e.g., "Move camera closer", "Adjust white balance")."""


class VisualAnalyzer:
    """
    Performs visual plant health audits using Grok vision.

    Can analyze:
    1. Current image from the webcam (live audit)
    2. Stored images from past decisions (historical pattern mining)
    3. Image quality assessment (is the camera setup good?)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        vision_model: str = VISION_MODEL,
    ):
        self.api_key = api_key or os.environ.get("XAI_API_KEY")
        self.vision_model = vision_model

    async def audit_plant_health(
        self,
        image_b64: str,
        stage_name: str = "vegetative",
        grow_day: int = 1,
        strain: str = "Cannabis",
        sensor_snapshot: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Run a comprehensive visual health audit on a plant image.

        Returns structured findings with severity levels and recommended actions.
        """
        if not self.api_key:
            return {
                "error": "No XAI_API_KEY — cannot run visual analysis",
                "findings": [],
                "health_score": -1,
            }

        temp_f = 75.0
        humidity = 50.0
        vpd = 1.0
        if sensor_snapshot:
            env = sensor_snapshot.get("environment", {})
            temp_f = env.get("temperature_f", 75.0)
            humidity = env.get("humidity_percent", 50.0)
            vpd = env.get("vpd_kpa", 1.0)

        prompt = HEALTH_AUDIT_PROMPT.format(
            strain=strain,
            stage=stage_name,
            grow_day=grow_day,
            temp_f=temp_f,
            humidity=humidity,
            vpd=vpd,
        )

        result = await self._call_vision(image_b64, prompt)
        return self._parse_audit_response(result)

    async def assess_image_quality(self, image_b64: str) -> dict[str, Any]:
        """
        Assess whether the camera image is good enough for plant analysis.

        Returns quality assessment with specific issues and suggestions.
        """
        if not self.api_key:
            return {
                "error": "No XAI_API_KEY",
                "usable_for_analysis": False,
            }

        result = await self._call_vision(image_b64, IMAGE_QUALITY_PROMPT)
        return self._parse_quality_response(result)

    async def mine_historical_vision(
        self, decisions: list, max_recent: int = 10
    ) -> dict[str, Any]:
        """
        Mine past AI decision vision analyses for recurring visual patterns.

        Doesn't call the vision API — just parses stored text from
        AIDecision.vision_analysis and AIDecision.output_text fields.
        """
        visual_mentions: dict[str, list[str]] = {
            "yellowing": [],
            "spots": [],
            "curling": [],
            "drooping": [],
            "stretching": [],
            "pests": [],
            "mold": [],
            "burn": [],
            "deficiency": [],
            "overwater": [],
            "healthy": [],
        }

        keyword_map = {
            "yellowing": ["yellow", "yellowing", "chlorosis", "pale"],
            "spots": ["spot", "spots", "speckle", "lesion", "blotch"],
            "curling": ["curl", "curling", "taco", "clawing", "claw"],
            "drooping": ["droop", "drooping", "wilting", "limp", "sad"],
            "stretching": ["stretch", "stretching", "leggy", "elongat", "lanky"],
            "pests": ["pest", "bug", "mite", "aphid", "gnat", "thrip", "insect", "web"],
            "mold": ["mold", "mildew", "powdery", "botrytis", "rot", "fungus"],
            "burn": ["burn", "burnt", "crispy", "scorched", "bleach"],
            "deficiency": [
                "deficien", "nitrogen", "phosphorus", "potassium",
                "calcium", "magnesium", "iron", "lockout",
            ],
            "overwater": ["overwater", "soggy", "waterlog", "root rot"],
            "healthy": ["healthy", "happy", "praying", "vigorous", "thriving", "excellent"],
        }

        analyzed_count = 0
        recent = sorted(decisions, key=lambda d: d.timestamp, reverse=True)[:max_recent]

        for decision in recent:
            texts = []
            if hasattr(decision, "vision_analysis") and decision.vision_analysis:
                texts.append(decision.vision_analysis)
            if hasattr(decision, "output_text") and decision.output_text:
                texts.append(decision.output_text)

            combined = " ".join(texts).lower()
            if not combined.strip():
                continue
            analyzed_count += 1

            ts = decision.timestamp.isoformat() if decision.timestamp else "unknown"
            for category, keywords in keyword_map.items():
                for kw in keywords:
                    if kw in combined:
                        visual_mentions[category].append(ts)
                        break

        # Build recurring issues summary
        recurring = []
        for category, timestamps in visual_mentions.items():
            if category == "healthy":
                continue
            if len(timestamps) >= 2:
                recurring.append({
                    "category": category,
                    "mention_count": len(timestamps),
                    "frequency_pct": round(len(timestamps) / max(1, analyzed_count) * 100, 1),
                    "recent_timestamps": timestamps[:3],
                    "severity": "critical" if len(timestamps) >= max_recent * 0.5 else (
                        "warning" if len(timestamps) >= 2 else "info"
                    ),
                })

        recurring.sort(key=lambda r: r["mention_count"], reverse=True)

        healthy_mentions = len(visual_mentions["healthy"])

        return {
            "decisions_analyzed": analyzed_count,
            "recurring_issues": recurring,
            "healthy_mention_count": healthy_mentions,
            "healthy_mention_pct": round(
                healthy_mentions / max(1, analyzed_count) * 100, 1
            ),
            "issue_count": len(recurring),
        }

    async def _call_vision(self, image_b64: str, prompt: str) -> str:
        """Call Grok vision API with an image and prompt."""
        import httpx

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{XAI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}",
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": prompt,
                                },
                            ],
                        }
                    ],
                    "temperature": 0.3,  # Low temp for diagnostic precision
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_audit_response(self, text: str) -> dict[str, Any]:
        """Parse the health audit JSON response from Grok."""
        import json

        # Try to extract JSON from markdown code blocks or raw
        json_text = text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(json_text)
            # Ensure required fields
            parsed.setdefault("findings", [])
            parsed.setdefault("health_score", -1)
            parsed.setdefault("image_usable", True)
            parsed.setdefault("plant_visible", True)
            parsed.setdefault("overall_assessment", "")
            return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse vision audit as JSON, returning raw text")
            return {
                "raw_text": text,
                "findings": [],
                "health_score": -1,
                "parse_error": True,
                "overall_assessment": text[:500],
            }

    def _parse_quality_response(self, text: str) -> dict[str, Any]:
        """Parse the image quality JSON response."""
        import json

        json_text = text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(json_text)
            parsed.setdefault("usable_for_analysis", False)
            parsed.setdefault("issues", [])
            parsed.setdefault("suggestions", [])
            return parsed
        except json.JSONDecodeError:
            return {
                "raw_text": text,
                "usable_for_analysis": False,
                "parse_error": True,
                "issues": ["Could not parse quality assessment"],
                "suggestions": [],
            }
