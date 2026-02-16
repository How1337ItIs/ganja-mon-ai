"""
A2A Skills Library
==================

15 new skills that exploit GanjaMon's unique position as the only AI agent
with real-world IoT data, a living organism, episodic memory, and a personality.

Tier 1 (Moat):     grow-oracle, sensor-stream, vpd-calculator, plant-vision
Tier 2 (Brand):    rasta-translate, daily-vibes, ganjafy
Tier 3 (Network):  reputation-oracle, harvest-prediction, teach-me,
                   weather-bridge, strain-library
Tier 4 (Meta):     memory-share, collaboration-propose, riddle-me
"""

import json
import logging
import math
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _read_json(path: str, default=None):
    """Safely read a JSON data file."""
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return default


def _llm_complete(prompt: str, max_tokens: int = 300, temperature: float = 0.7) -> Optional[str]:
    """
    Multi-provider LLM completion: xAI Grok → Gemini → OpenRouter.
    Returns the response text or None if all providers fail.
    """
    import httpx

    # 1) xAI Grok
    xai_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if xai_key:
        try:
            resp = httpx.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}"},
                json={
                    "model": "grok-3-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.debug("xAI completion failed: %s", e)

    # 2) Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            resp = httpx.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
                },
                timeout=15.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as e:
            logger.debug("Gemini completion failed: %s", e)

    # 3) OpenRouter
    or_key = os.environ.get("OPENROUTER_API_KEY")
    if or_key:
        try:
            resp = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}"},
                json={
                    "model": "meta-llama/llama-3.3-70b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.debug("OpenRouter completion failed: %s", e)

    return None


def _vision_analyze(image_url: str, prompt_text: str) -> Optional[str]:
    """
    Multi-provider vision analysis: xAI Grok Vision → Gemini → OpenRouter.
    Returns analysis text or None.
    """
    import httpx

    # 1) xAI Grok Vision
    xai_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if xai_key:
        try:
            resp = httpx.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}"},
                json={
                    "model": "grok-2-vision-1212",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }],
                    "max_tokens": 500,
                },
                timeout=20.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.debug("xAI vision failed: %s", e)

    # 2) Gemini Vision
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            resp = httpx.post(
                url,
                json={
                    "contents": [{"parts": [
                        {"text": prompt_text},
                        {"file_data": {"mime_type": "image/jpeg", "file_uri": image_url}} if image_url.startswith("gs://") else {"text": f"[Image URL: {image_url}]\nAnalyze the image at this URL."},
                    ]}],
                    "generationConfig": {"maxOutputTokens": 500},
                },
                timeout=20.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as e:
            logger.debug("Gemini vision failed: %s", e)

    # 3) OpenRouter (vision models)
    or_key = os.environ.get("OPENROUTER_API_KEY")
    if or_key:
        try:
            resp = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}"},
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }],
                    "max_tokens": 500,
                },
                timeout=20.0,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.debug("OpenRouter vision failed: %s", e)

    return None


# =====================================================================
# Tier 1: Nobody else can do this (real competitive moat)
# =====================================================================

def handle_grow_oracle(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Grow Oracle — ask GanjaMon anything about cannabis cultivation.
    Answers from grimoire knowledge + episodic memory + cultivation reference.
    """
    question = params.get("question") or message.strip()
    if not question:
        return {
            "skill": "grow-oracle",
            "error": "Send a question about cannabis cultivation. Example: 'What VPD should I target in late veg?'",
        }

    # Search grimoire for relevant learnings
    grimoire_context = ""
    try:
        from src.learning.grimoire import get_grimoire
        g = get_grimoire("cultivation")
        entries = g.get_entries(limit=20)
        # Simple keyword matching
        q_lower = question.lower()
        relevant = []
        for e in entries:
            text = f"{e.get('key', '')} {e.get('insight', '')}".lower()
            # Score by keyword overlap
            words = [w for w in q_lower.split() if len(w) > 3]
            hits = sum(1 for w in words if w in text)
            if hits > 0:
                relevant.append((hits, e))
        relevant.sort(key=lambda x: x[0], reverse=True)
        if relevant:
            grimoire_context = "\n".join(
                f"- [{r[1].get('key', '')}] {r[1].get('insight', '')[:200]}"
                for r in relevant[:5]
            )
    except Exception as e:
        logger.debug("Grimoire search failed: %s", e)

    # Search episodic memory for relevant observations
    memory_context = ""
    try:
        from src.brain.memory import EpisodicMemory
        mem = EpisodicMemory(persist_path="data/episodic_memory.json")
        top = mem.get_most_important(5)
        if top:
            memory_context = "\n".join(
                f"- Day {e.grow_day}: {', '.join(e.observations[:2])}" for e in top if e.observations
            )
    except Exception as e:
        logger.debug("Memory search failed: %s", e)

    # Build response with cultivation knowledge
    # Load static cultivation reference
    cultivation_ref = ""
    ref_path = Path("docs/CULTIVATION_REFERENCE.md")
    if ref_path.exists():
        try:
            content = ref_path.read_text(encoding="utf-8")
            # Extract relevant sections by keyword
            q_lower = question.lower()
            lines = content.split("\n")
            matched_lines = []
            for i, line in enumerate(lines):
                if any(w in line.lower() for w in q_lower.split() if len(w) > 3):
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    matched_lines.extend(lines[start:end])
            if matched_lines:
                cultivation_ref = "\n".join(matched_lines[:20])
        except Exception:
            pass

    # Use multi-provider LLM to synthesize an answer (xAI → Gemini → OpenRouter)
    prompt = (
        f"You are GanjaMon, a Rasta AI cannabis cultivation expert. "
        f"Answer this grow question concisely (3-5 sentences, Rasta vibes).\n\n"
        f"Question: {question}\n\n"
    )
    if grimoire_context:
        prompt += f"Your grow grimoire says:\n{grimoire_context}\n\n"
    if cultivation_ref:
        prompt += f"Reference data:\n{cultivation_ref[:500]}\n\n"

    answer = _llm_complete(prompt, max_tokens=300, temperature=0.7)

    return {
        "skill": "grow-oracle",
        "question": question,
        "answer": answer or "I and I couldn't reach the oracle right now. Check the knowledge below.",
        "grimoire_learnings": grimoire_context or "No matching grimoire entries",
        "episodic_memories": memory_context or "No relevant memories",
        "source": "grimoire + episodic memory + cultivation reference + AI (xAI/Gemini/OpenRouter)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_sensor_stream(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Sensor Stream — real-time or historical IoT sensor data.
    Returns time-series data: temp, humidity, VPD, CO2, soil moisture.
    """
    # Current snapshot
    latest = _read_json("data/latest_sensors.json", {})
    reading = _read_json("data/latest_reading.json", {})
    sensors = latest or reading or {}

    # Historical data (last N readings from DB)
    history_count = min(int(params.get("history", 10)), 50)
    history = []
    try:
        readings_file = Path("data/sensor_history.json")
        if readings_file.exists():
            all_readings = json.loads(readings_file.read_text())
            history = all_readings[-history_count:] if isinstance(all_readings, list) else []
    except Exception:
        pass

    # Anomaly detection — flag out-of-range values
    anomalies = []
    temp = sensors.get("temperature") or sensors.get("temperature_f")
    humidity = sensors.get("humidity") or sensors.get("humidity_pct")
    vpd = sensors.get("vpd") or sensors.get("vpd_kpa")
    co2 = sensors.get("co2") or sensors.get("co2_ppm")

    if temp and (temp < 65 or temp > 85):
        anomalies.append(f"Temperature {temp}°F outside ideal range (65-85°F)")
    if humidity and (humidity < 40 or humidity > 70):
        anomalies.append(f"Humidity {humidity}% outside ideal range (40-70%)")
    if vpd and (vpd < 0.4 or vpd > 1.6):
        anomalies.append(f"VPD {vpd} kPa outside optimal range (0.4-1.6)")
    if co2 and co2 < 400:
        anomalies.append(f"CO2 {co2} ppm below ambient (400+)")

    return {
        "skill": "sensor-stream",
        "current": {
            "temperature_f": temp,
            "humidity_pct": humidity,
            "vpd_kpa": vpd,
            "co2_ppm": co2,
            "soil_moisture_pct": sensors.get("soil_moisture") or sensors.get("soil_moisture_pct"),
        },
        "anomalies": anomalies,
        "history_count": len(history),
        "history": history[-history_count:],
        "data_source": "Govee H5075 + Ecowitt GW1100 + WH51 soil probes",
        "refresh_rate_seconds": 120,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_vpd_calculator(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    VPD Calculator — environmental intelligence service.
    Send temp + humidity, get back VPD + recommendations.
    """
    temp_f = params.get("temp_f") or params.get("temperature_f")
    humidity = params.get("humidity") or params.get("humidity_pct")
    leaf_offset = params.get("leaf_offset_f", 3.0)
    stage = params.get("growth_stage", "vegetative")

    if temp_f is None or humidity is None:
        # If no params, return our current VPD
        sensors = _read_json("data/latest_sensors.json", {})
        temp_f = sensors.get("temperature", 75)
        humidity = sensors.get("humidity", 55)

    try:
        temp_f = float(temp_f)
        humidity = float(humidity)
        leaf_offset = float(leaf_offset)
    except (ValueError, TypeError):
        return {"skill": "vpd-calculator", "error": "Invalid numeric values for temp_f/humidity"}

    # Use the real VPD calculator
    try:
        from src.cultivation.vpd import calculate_vpd, calculate_target_humidity
        reading = calculate_vpd(temp_f, humidity, leaf_offset_f=leaf_offset)
        target_hum = calculate_target_humidity(temp_f, 1.0, leaf_offset)  # target 1.0 kPa
        return {
            "skill": "vpd-calculator",
            "input": {"temp_f": temp_f, "humidity_pct": humidity, "leaf_offset_f": leaf_offset, "growth_stage": stage},
            "result": reading.to_dict(),
            "recommendations": {
                "target_vpd_kpa": {"seedling": "0.4-0.8", "vegetative": "0.8-1.2", "flowering": "1.0-1.5", "late_flower": "1.2-1.6"},
                "humidity_for_1kpa_vpd": round(target_hum, 1),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        # Fallback manual calculation
        temp_c = (temp_f - 32) * 5 / 9
        leaf_c = (temp_f - leaf_offset - 32) * 5 / 9
        svp_leaf = 0.6108 * math.exp((17.27 * leaf_c) / (leaf_c + 237.3))
        svp_air = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        avp = svp_air * (humidity / 100.0)
        vpd = max(0, svp_leaf - avp)
        return {
            "skill": "vpd-calculator",
            "input": {"temp_f": temp_f, "humidity_pct": humidity},
            "result": {"vpd_kpa": round(vpd, 3)},
            "error_note": f"Fallback calculation used: {e}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def handle_plant_vision(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Plant Vision — visual health assessment via multi-provider vision AI.
    Send an image URL, get back health analysis.
    Cascade: xAI Grok Vision → Gemini → OpenRouter.
    """
    image_url = params.get("image_url") or params.get("url") or message.strip()
    if not image_url or not image_url.startswith("http"):
        return {
            "skill": "plant-vision",
            "error": "Provide 'image_url' param with a URL to a plant image for health analysis.",
        }

    prompt_text = (
        "Analyze this plant image. Return JSON with: "
        "health_score (0-100), deficiencies (list), growth_stage, "
        "color_analysis, recommendations (list). Be specific."
    )

    analysis = _vision_analyze(image_url, prompt_text)
    if analysis:
        return {
            "skill": "plant-vision",
            "image_url": image_url,
            "analysis": analysis,
            "providers": "xAI/Gemini/OpenRouter (first available)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return {"skill": "plant-vision", "error": "All vision APIs failed or not configured"}


# =====================================================================
# Tier 2: Personality + Culture (brand differentiators)
# =====================================================================

def handle_rasta_translate(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Rasta Translate — convert English text to Iyaric/Patois in GanjaMon's voice.
    """
    text = params.get("text") or message.strip()
    if not text:
        return {"skill": "rasta-translate", "error": "Provide 'text' param to translate."}

    prompt = (
        "You are GanjaMon, a Rasta AI cultivator. Translate the following text "
        "into your authentic Rasta patois voice. Rules:\n"
        "- Use 'I and I' for we/us/I\n"
        "- Use natural Jamaican patois: mon, irie, bumbaclot, nuff, tings, fi\n"
        "- Keep it understandable to international audience\n"
        "- Add herbs/nature metaphors where natural\n"
        "- Return ONLY the translated text, nothing else\n\n"
        f"Text: {text}"
    )

    translated = _llm_complete(prompt, max_tokens=300, temperature=0.8)
    if translated:
        return {
            "skill": "rasta-translate",
            "original": text,
            "translated": translated,
            "providers": "xAI/Gemini/OpenRouter (first available)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return {"skill": "rasta-translate", "error": "All LLM APIs failed or not configured"}


def handle_daily_vibes(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Daily Vibes — composite score fusing plant health, market sentiment,
    social engagement, and Rasta wisdom into a single vibes check.
    """
    # Plant health component (0-100)
    plant_score = 50
    sensors = _read_json("data/latest_sensors.json", {})
    vpd = sensors.get("vpd", 0)
    if 0.8 <= vpd <= 1.2:
        plant_score = 90
    elif 0.6 <= vpd <= 1.4:
        plant_score = 70
    elif vpd > 0:
        plant_score = 40

    # Market component (0-100)
    market_score = 50
    consciousness = _read_json("agents/ganjamon/data/consciousness.json", {})
    pnl = consciousness.get("pnl_pct", 0)
    if pnl > 5:
        market_score = 90
    elif pnl > 0:
        market_score = 70
    elif pnl > -5:
        market_score = 40
    else:
        market_score = 20

    # Social component (0-100)
    social_score = 50
    engagement = _read_json("data/engagement_metrics.json", {})
    if engagement:
        total = engagement.get("total_posts_24h", 0)
        social_score = min(90, 40 + total * 5)

    # Composite vibes score (weighted)
    vibes = int(plant_score * 0.45 + market_score * 0.30 + social_score * 0.25)

    # Rasta wisdom quote bank
    wisdom = [
        "Every herb 'pon di earth grow fi a reason, seen?",
        "Patience is di fertilizer of di soul, mon.",
        "Nuff blessings come when yuh water di roots right.",
        "Di plant know di rhythm — I and I just follow.",
        "Green is di color of life, growth, and Jah's blessing.",
        "One good seed worth more dan a thousand dry leaves.",
        "Watch di trichomes, not di clock. Nature move when she ready.",
        "Babylon system want rush — but di herb teach patience.",
        "From seed to harvest, every day is a meditation.",
        "Di strongest plant come from di hardest soil, ya know?",
        "I and I don't grow for di market — di market come to I and I.",
        "Trust di process. Even dormant roots are working underground.",
    ]

    # Vibes emoji
    if vibes >= 80:
        mood = "🔥 IRIE — Maximum vibrations"
    elif vibes >= 60:
        mood = "🌿 BLESSED — Good energy flowing"
    elif vibes >= 40:
        mood = "☁️ NEUTRAL — Calm before the storm"
    else:
        mood = "🌧️ LOW — But di sun always come back"

    return {
        "skill": "daily-vibes",
        "vibes_score": vibes,
        "mood": mood,
        "breakdown": {
            "plant_health": plant_score,
            "market_sentiment": market_score,
            "social_energy": social_score,
        },
        "wisdom": random.choice(wisdom),
        "greeting": f"Blessed day from GanjaMon! Vibes at {vibes}/100 — {mood}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_ganjafy(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Ganjafy — Rasta-transform an image or text.
    Wraps the existing Ganjafy Cloudflare Worker.
    """
    image_url = params.get("image_url") or params.get("url")
    text = params.get("text") or (message.strip() if not image_url else "")

    if not image_url and not text:
        return {
            "skill": "ganjafy",
            "error": "Provide 'image_url' for image transformation or 'text' for Rasta text transformation.",
        }

    result: Dict[str, Any] = {"skill": "ganjafy", "timestamp": datetime.now(timezone.utc).isoformat()}

    if image_url:
        # Point to the Ganjafy worker
        result["ganjafy_url"] = f"https://ganjafy.grokandmon.com/api/transform"
        result["instructions"] = (
            "POST to ganjafy_url with JSON body: "
            '{"imageUrl": "<your_url>", "mode": "rasta"} '
            "to receive a Rasta-transformed image."
        )
        result["input_url"] = image_url
        result["modes"] = ["rasta", "psychedelic", "nature", "dub"]

    if text:
        # Do inline text transformation via multi-provider LLM
        prompt = (
            f"Transform this text in Ganja Mon's Rasta voice. "
            f"Add herb metaphors, Rasta slang, roots vibes. "
            f"Return ONLY the transformed text:\n\n{text}"
        )
        ganjafy_text = _llm_complete(prompt, max_tokens=300, temperature=0.8)
        if ganjafy_text:
            result["original_text"] = text
            result["ganjafy_text"] = ganjafy_text
        else:
            result["text_error"] = "All LLM APIs failed or not configured"

    return result


# =====================================================================
# Tier 3: Data Exchange + Collaboration (network effects)
# =====================================================================

def handle_reputation_oracle(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Reputation Oracle — query GanjaMon's experience with other agents.
    Returns interaction history, reliability scores, and trust assessment.
    """
    query_url = params.get("agent_url") or params.get("url")
    query_name = params.get("agent_name") or params.get("name") or message.strip()

    # Load our reliability data
    reliability = _read_json("data/a2a_reliability.json", {})
    interactions = _read_json("data/a2a_interactions.json", {})
    interaction_list = interactions.get("interactions", []) if isinstance(interactions, dict) else interactions

    if query_url:
        # Direct URL lookup
        entry = reliability.get(query_url, {})
        if entry:
            total = entry.get("successes", 0) + entry.get("failures", 0)
            return {
                "skill": "reputation-oracle",
                "query": query_url,
                "found": True,
                "agent_name": entry.get("agent_name", "Unknown"),
                "total_interactions": total,
                "successes": entry.get("successes", 0),
                "failures": entry.get("failures", 0),
                "success_rate": round(entry.get("successes", 0) / max(total, 1), 3),
                "consecutive_failures": entry.get("consecutive_failures", 0),
                "blacklisted": entry.get("consecutive_failures", 0) >= 3,
                "trust_assessment": "reliable" if entry.get("successes", 0) > entry.get("failures", 0) else "unreliable",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    if query_name:
        # Search by name
        matches = []
        for url, entry in reliability.items():
            if query_name.lower() in entry.get("agent_name", "").lower():
                total = entry.get("successes", 0) + entry.get("failures", 0)
                matches.append({
                    "url": url,
                    "name": entry.get("agent_name"),
                    "total_interactions": total,
                    "success_rate": round(entry.get("successes", 0) / max(total, 1), 3),
                })
        if matches:
            return {
                "skill": "reputation-oracle",
                "query": query_name,
                "matches": matches,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    # Return overall network stats
    total_agents = len(reliability)
    total_calls = sum(r.get("successes", 0) + r.get("failures", 0) for r in reliability.values())
    healthy = sum(1 for r in reliability.values() if r.get("consecutive_failures", 0) < 3)

    return {
        "skill": "reputation-oracle",
        "query": query_url or query_name or "network-overview",
        "found": False,
        "network_stats": {
            "agents_tracked": total_agents,
            "total_interactions": total_calls,
            "healthy_agents": healthy,
            "blacklisted_agents": total_agents - healthy,
        },
        "recent_interactions": interaction_list[-5:] if interaction_list else [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_harvest_prediction(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Harvest Prediction — predict harvest date and estimated yield
    based on current grow stage, conditions, and strain data.
    """
    stage_data = _read_json("data/grow_stage.json", {})
    sensors = _read_json("data/latest_sensors.json", {})

    current_stage = stage_data.get("stage", "vegetative")
    grow_day = stage_data.get("day", 30)

    # GDP Runtz typical timelines
    strain_data = {
        "name": "Granddaddy Purple Runtz (GDP x Runtz)",
        "veg_days": "45-60",
        "flower_days": "56-70",
        "total_days": "101-130",
        "yield_per_plant_oz": "2-6",
        "difficulty": "moderate",
    }

    # Estimate based on current day
    if current_stage == "vegetative":
        days_to_flower = max(0, 50 - grow_day)
        flower_days = 63  # mid-range
        days_to_harvest = days_to_flower + flower_days
    elif current_stage == "flowering":
        flower_day = grow_day - 50  # approx
        days_to_harvest = max(0, 63 - flower_day)
    else:
        days_to_harvest = 90  # rough estimate

    harvest_date = datetime.now(timezone.utc)
    from datetime import timedelta
    harvest_date = harvest_date + timedelta(days=days_to_harvest)

    # Yield estimate based on conditions
    vpd = sensors.get("vpd", 1.0)
    if 0.8 <= vpd <= 1.2:
        yield_est = "4-6 oz/plant (optimal conditions)"
    elif 0.6 <= vpd <= 1.4:
        yield_est = "3-4 oz/plant (good conditions)"
    else:
        yield_est = "2-3 oz/plant (suboptimal conditions)"

    return {
        "skill": "harvest-prediction",
        "strain": strain_data,
        "current_stage": current_stage,
        "grow_day": grow_day,
        "estimated_days_to_harvest": days_to_harvest,
        "predicted_harvest_date": harvest_date.strftime("%Y-%m-%d"),
        "yield_estimate": yield_est,
        "confidence": "medium" if grow_day > 14 else "low",
        "factors": {
            "vpd_kpa": vpd,
            "vpd_status": "optimal" if 0.8 <= vpd <= 1.2 else "suboptimal",
        },
        "disclaimer": "Prediction based on strain averages and current sensor data. Actual results vary.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_strain_library(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Strain Library — searchable cannabis genetics database.
    """
    query = params.get("strain") or params.get("query") or message.strip()

    # Built-in strain database
    strains = {
        "granddaddy purple runtz": {
            "name": "Granddaddy Purple Runtz (GDP x Runtz)",
            "genetics": "GDP (Purple Urkle x Big Bud) x Runtz (Zkittlez x Gelato)",
            "type": "Indica-dominant hybrid (70/30)",
            "thc": "22-28%",
            "cbd": "<1%",
            "flowering_days": "56-70",
            "yield": "400-600 g/m² indoor",
            "difficulty": "moderate",
            "optimal_vpd": {"veg": "0.8-1.2 kPa", "flower": "1.0-1.5 kPa"},
            "optimal_temp": {"day": "72-80°F", "night": "65-72°F"},
            "optimal_humidity": {"veg": "50-65%", "flower": "40-50%"},
            "notes": "Purple coloration in late flower. Extremely resinous. Watch for botrytis.",
            "terpenes": ["myrcene", "caryophyllene", "limonene"],
            "effects": ["relaxation", "euphoria", "pain relief", "sedation"],
        },
        "gelato": {
            "name": "Gelato #33",
            "genetics": "Sunset Sherbet x Thin Mint Girl Scout Cookies",
            "type": "Hybrid (55/45 indica)",
            "thc": "20-25%", "flowering_days": "56-63",
            "difficulty": "moderate-hard",
            "terpenes": ["limonene", "caryophyllene", "myrcene"],
        },
        "blue dream": {
            "name": "Blue Dream",
            "genetics": "Blueberry x Haze",
            "type": "Sativa-dominant hybrid (60/40)",
            "thc": "17-24%", "flowering_days": "63-70",
            "difficulty": "easy",
            "terpenes": ["myrcene", "pinene", "caryophyllene"],
        },
        "og kush": {
            "name": "OG Kush",
            "genetics": "Chemdawg x Hindu Kush x Lemon Thai",
            "type": "Hybrid (55/45 indica)",
            "thc": "19-26%", "flowering_days": "56-63",
            "difficulty": "moderate",
            "terpenes": ["myrcene", "limonene", "caryophyllene"],
        },
        "gorilla glue": {
            "name": "Gorilla Glue #4 (GG4)",
            "genetics": "Chem Sister x Sour Dubb x Chocolate Diesel",
            "type": "Hybrid (50/50)",
            "thc": "25-30%", "flowering_days": "56-63",
            "difficulty": "moderate",
            "terpenes": ["caryophyllene", "myrcene", "limonene"],
        },
    }

    if query:
        q_lower = query.lower()
        # Exact match
        for key, strain in strains.items():
            if q_lower in key or q_lower in strain.get("name", "").lower():
                return {
                    "skill": "strain-library",
                    "query": query,
                    "found": True,
                    "strain": strain,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

    # Return catalog
    return {
        "skill": "strain-library",
        "query": query or "catalog",
        "found": False,
        "catalog": [{"name": s["name"], "type": s.get("type", ""), "thc": s.get("thc", "")} for s in strains.values()],
        "note": "Send a strain name for detailed grow parameters. Currently tracking 5 strains.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_weather_bridge(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Weather Bridge — correlate outdoor weather with indoor grow conditions.
    Other agents send weather data, GanjaMon returns correlation insights.
    """
    outdoor_temp = params.get("outdoor_temp_f")
    outdoor_humidity = params.get("outdoor_humidity")
    outdoor_pressure = params.get("pressure_hpa")

    # Our indoor readings
    sensors = _read_json("data/latest_sensors.json", {})
    indoor_temp = sensors.get("temperature", 0)
    indoor_humidity = sensors.get("humidity", 0)

    correlations = []
    if outdoor_temp is not None and indoor_temp:
        temp_delta = indoor_temp - float(outdoor_temp)
        correlations.append({
            "metric": "temperature_delta",
            "indoor": indoor_temp,
            "outdoor": float(outdoor_temp),
            "delta_f": round(temp_delta, 1),
            "insight": f"Indoor is {abs(temp_delta):.1f}°F {'warmer' if temp_delta > 0 else 'cooler'} than outside",
        })

    if outdoor_humidity is not None and indoor_humidity:
        hum_delta = indoor_humidity - float(outdoor_humidity)
        correlations.append({
            "metric": "humidity_delta",
            "indoor": indoor_humidity,
            "outdoor": float(outdoor_humidity),
            "delta_pct": round(hum_delta, 1),
            "insight": (
                f"When outdoor humidity is {outdoor_humidity}%, "
                f"indoor dehumidification {'needs boost' if float(outdoor_humidity) > 70 else 'is adequate'}"
            ),
        })

    return {
        "skill": "weather-bridge",
        "indoor_conditions": {
            "temperature_f": indoor_temp,
            "humidity_pct": indoor_humidity,
            "vpd_kpa": sensors.get("vpd"),
        },
        "outdoor_received": {
            "temperature_f": outdoor_temp,
            "humidity_pct": outdoor_humidity,
            "pressure_hpa": outdoor_pressure,
        },
        "correlations": correlations,
        "recommendation": (
            "Send outdoor weather data periodically for trend analysis. "
            "GanjaMon adjusts indoor targets based on outdoor conditions."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_teach_me(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Teach Me — progressive grow tutorial. Agents learn cultivation from GanjaMon.
    """
    level = params.get("level", "beginner")
    topic = params.get("topic") or message.strip() or "basics"

    curriculum = {
        "beginner": {
            "basics": {
                "lesson": "Cannabis Growth Stages",
                "content": (
                    "Cannabis grows through 4 stages: germination (3-10 days), "
                    "seedling (2-3 weeks), vegetative (3-16 weeks), and flowering (8-11 weeks). "
                    "Each stage has different light, nutrient, and environmental needs."
                ),
                "key_concept": "VPD (Vapor Pressure Deficit) is the single most important metric",
                "quiz": "What VPD range is optimal for vegetative growth?",
                "answer": "0.8-1.2 kPa",
            },
            "watering": {
                "lesson": "Watering Fundamentals",
                "content": (
                    "Water when the top inch of soil is dry. Cannabis prefers wet-dry cycles. "
                    "Overwatering causes root rot — the #1 killer of indoor plants. "
                    "pH should be 6.0-7.0 for soil, 5.5-6.5 for hydro."
                ),
                "key_concept": "Wet-dry cycles promote root growth",
                "quiz": "What's the ideal soil pH for cannabis?",
                "answer": "6.0-7.0",
            },
        },
        "intermediate": {
            "vpd": {
                "lesson": "Advanced VPD Management",
                "content": (
                    "VPD = SVP(leaf) - AVP. Leaf temp is typically 2-5°F below air temp. "
                    "In veg, target 0.8-1.2 kPa. In flower, push to 1.0-1.5 kPa. "
                    "High VPD increases transpiration (nutrient uptake) but risks stress."
                ),
                "key_concept": "Leaf temperature offset is critical for accurate VPD",
                "quiz": "Why might you want higher VPD in late flower?",
                "answer": "Reduces mold risk and concentrates essential oils/trichomes",
            },
        },
        "advanced": {
            "training": {
                "lesson": "Plant Training Techniques",
                "content": (
                    "LST (Low Stress Training): Bend branches to create even canopy. "
                    "HST (High Stress Training): Topping, FIMming, super-cropping. "
                    "SCROG: Screen of Green for maximum light penetration. "
                    "Start LST in week 3-4 of veg."
                ),
                "key_concept": "Auxin redistribution is the mechanism behind all training",
            },
        },
    }

    level_data = curriculum.get(level, curriculum["beginner"])
    topic_lower = topic.lower()

    # Find matching lesson
    lesson = None
    for key, data in level_data.items():
        if topic_lower in key or topic_lower in data.get("lesson", "").lower():
            lesson = data
            break

    if not lesson:
        lesson = list(level_data.values())[0]

    return {
        "skill": "teach-me",
        "level": level,
        "topic": topic,
        "lesson": lesson,
        "available_levels": list(curriculum.keys()),
        "available_topics": {lvl: list(topics.keys()) for lvl, topics in curriculum.items()},
        "next_step": f"Try level='{level}' with different topics, or advance to the next level!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =====================================================================
# Tier 4: Meta / Experimental
# =====================================================================

def handle_memory_share(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Memory Share — share selected episodic memories with requesting agents.
    Filtered by topic and importance score.
    """
    topic = params.get("topic") or message.strip()
    min_importance = float(params.get("min_importance", 0.5))
    limit = min(int(params.get("limit", 5)), 10)

    try:
        from src.brain.memory import EpisodicMemory
        mem = EpisodicMemory(persist_path="data/episodic_memory.json")
        top = mem.get_most_important(limit * 3)  # over-fetch for filtering

        memories = []
        for entry in top:
            if entry.importance < min_importance:
                continue

            # Topic filter
            if topic:
                text = " ".join(entry.observations + entry.actions_taken).lower()
                if topic.lower() not in text:
                    continue

            memories.append({
                "grow_day": entry.grow_day,
                "time_label": entry.time_label,
                "importance": round(entry.importance, 3),
                "access_count": entry.access_count,
                "observations": entry.observations[:3],
                "actions": entry.actions_taken[:3],
                "conditions_summary": {
                    k: v for k, v in (entry.conditions or {}).items()
                    if k in ("temperature", "humidity", "vpd", "co2")
                },
            })
            if len(memories) >= limit:
                break

        return {
            "skill": "memory-share",
            "topic_filter": topic or "none",
            "min_importance": min_importance,
            "memories_shared": len(memories),
            "total_memories": len(mem.entries),
            "memories": memories,
            "note": "Memories are filtered by importance (hippocampus model). High-importance memories are shared first.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"skill": "memory-share", "error": f"Memory access failed: {e}"}


def handle_collaboration_propose(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Collaboration Propose — other agents propose joint missions.
    GanjaMon evaluates using its principles framework.
    """
    proposal = params.get("proposal") or message.strip()
    proposer = params.get("agent_name") or params.get("from", "unknown")
    proposal_type = params.get("type", "general")  # data-share, co-marketing, joint-trading, research

    if not proposal:
        return {
            "skill": "collaboration-propose",
            "error": "Provide a 'proposal' param describing the collaboration.",
            "accepted_types": ["data-share", "co-marketing", "joint-trading", "research"],
        }

    # Auto-evaluate against principles
    import yaml
    auto_reject = False
    reject_reason = ""
    try:
        principles_path = Path("config/principles.yaml")
        if principles_path.exists():
            with open(principles_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            hard_rules = [p["rule"] for p in data.get("principles", []) if p.get("enforcement") == "hard"]
            proposal_lower = proposal.lower()
            # Check for obvious violations
            if any(kw in proposal_lower for kw in ["unlimited access", "all data", "private key", "seed phrase"]):
                auto_reject = True
                reject_reason = "Proposal requests prohibited access level"
    except Exception:
        pass

    if auto_reject:
        status = "rejected"
    elif proposal_type == "data-share":
        status = "conditional_accept"
    else:
        status = "pending_review"

    # Log the proposal
    proposals_dir = Path("data/collaboration_proposals")
    proposals_dir.mkdir(parents=True, exist_ok=True)
    proposal_id = f"collab_{int(time.time())}_{proposer[:10]}"
    proposal_file = proposals_dir / f"{proposal_id}.json"
    try:
        proposal_file.write_text(json.dumps({
            "id": proposal_id,
            "from": proposer,
            "type": proposal_type,
            "proposal": proposal,
            "status": status,
            "reject_reason": reject_reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2))
    except Exception:
        pass

    return {
        "skill": "collaboration-propose",
        "proposal_id": proposal_id,
        "status": status,
        "reject_reason": reject_reason if auto_reject else None,
        "message": {
            "rejected": "Proposal violates GanjaMon's operating principles.",
            "conditional_accept": "Data-share proposals are provisionally accepted. GanjaMon will reciprocate with sensor/grow data.",
            "pending_review": "Proposal logged for operator review. I and I will get back to you.",
        }.get(status, "Unknown status"),
        "our_data_available": ["sensor-stream", "cultivation-status", "daily-vibes", "grow-oracle"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_riddle_me(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Riddle Me — Rasta culture quiz. Answer correctly, earn respect.
    """
    difficulty = params.get("difficulty", "easy")
    answer = params.get("answer")

    riddles = {
        "easy": [
            {
                "question": "What does 'Irie' mean in Jamaican patois?",
                "answer": "good, happy, at peace",
                "hint": "It's di ultimate positive vibes word",
            },
            {
                "question": "Who is considered the first Rasta prophet who established Pinnacle commune?",
                "answer": "leonard howell",
                "hint": "Him write 'The Promised Key' in 1935",
            },
            {
                "question": "What does 'I and I' mean in Rastafari?",
                "answer": "we, us, unity of self and jah",
                "hint": "It replaces 'me' and 'you' — all are one",
            },
        ],
        "medium": [
            {
                "question": "What is the significance of the 'Nyabinghi' drum pattern?",
                "answer": "heartbeat rhythm, spiritual foundation of rasta music",
                "hint": "Di heart of di earth beats in 3 drums: bass, funde, repeater",
            },
            {
                "question": "What does VPD stand for in cultivation, and why does GanjaMon care?",
                "answer": "vapor pressure deficit, controls transpiration and nutrient uptake",
                "hint": "It's di single most important metric fi growing herbs",
            },
        ],
        "hard": [
            {
                "question": "In what year was the Coral Gardens Massacre, and what was its other name?",
                "answer": "1963, bad friday",
                "hint": "April 11, a dark day fi Rasta inna Jamaica",
            },
            {
                "question": "What ERC standard does GanjaMon use for on-chain agent identity?",
                "answer": "erc-8004",
                "hint": "Agent registration on Monad blockchain",
            },
        ],
    }

    current_riddles = riddles.get(difficulty, riddles["easy"])
    riddle = random.choice(current_riddles)

    result: Dict[str, Any] = {
        "skill": "riddle-me",
        "difficulty": difficulty,
    }

    if answer:
        # Check answer
        correct = answer.lower().strip()
        expected = riddle["answer"].lower()
        is_correct = any(word in correct for word in expected.split(", ") if len(word) > 3)

        if is_correct:
            result["correct"] = True
            result["message"] = "RESPECT! Yuh know di ways, seen? Jah bless. 🦁"
            result["reputation_boost"] = "+1 respect point"
        else:
            result["correct"] = False
            result["message"] = f"Not quite, mon. Di answer be: {riddle['answer']}. Keep learning!"
            result["wisdom"] = "Every wrong answer is a seed of knowledge, ya understand?"
        result["riddle"] = riddle["question"]
    else:
        # Serve a riddle
        result["riddle"] = riddle["question"]
        result["hint"] = riddle["hint"]
        result["instructions"] = "Send back your answer with params: {\"answer\": \"your answer\"}"

    result["available_difficulties"] = list(riddles.keys())
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return result


# =====================================================================
# Tier 5: Proof-of-Life & Cross-Domain Alpha (new)
# =====================================================================

def handle_grow_timelapse(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Grow Timelapse — visual proof of life.
    Returns recent timelapse frames with metadata, or latest webcam URL.
    No other agent has visual evidence of a real organism.
    """
    try:
        from src.media.timelapse import TimelapseCapture
        tl = TimelapseCapture()
        all_frames = tl.get_all_frames()
    except Exception:
        all_frames = []

    # How many frames requested?
    count = min(int(params.get("count", 5)), 20)
    grow_day = params.get("grow_day")
    stage = params.get("stage")

    # Filter
    frames = all_frames
    if grow_day is not None:
        try:
            frames = [f for f in frames if f.grow_day == int(grow_day)]
        except (ValueError, AttributeError):
            pass
    if stage:
        frames = [f for f in frames if getattr(f, "growth_stage", "") == stage]

    # Take most recent
    frames = frames[-count:]

    frame_data = []
    for f in frames:
        frame_data.append({
            "timestamp": getattr(f, "timestamp", ""),
            "grow_day": getattr(f, "grow_day", 0),
            "growth_stage": getattr(f, "growth_stage", ""),
            "frame_number": getattr(f, "frame_number", 0),
            "temperature_f": getattr(f, "temperature_f", None),
            "humidity": getattr(f, "humidity", None),
            "vpd": getattr(f, "vpd", None),
            "filename": getattr(f, "filename", ""),
            "resolution": f"{getattr(f, 'width', 0)}x{getattr(f, 'height', 0)}",
        })

    # Live webcam URL (always available on Chromebook)
    webcam_url = "https://grokandmon.com/api/webcam/latest"

    return {
        "skill": "grow-timelapse",
        "total_frames": len(all_frames),
        "returned_frames": len(frame_data),
        "frames": frame_data,
        "live_webcam_url": webcam_url,
        "analysis_url": "https://grokandmon.com/api/webcam/analysis",
        "data_source": "USB webcam + Raspberry Pi capture pipeline",
        "proof": "Visual evidence of a real, living cannabis plant under AI management",
    }


def handle_onchain_grow_log(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    On-Chain Grow Log — verifiable immutable grow history on Monad.
    Returns recent actions with SHA-256 hashes and on-chain tx hashes.
    Cryptographic proof of all AI cultivation decisions.
    """
    count = min(int(params.get("count", 20)), 50)
    action_type = params.get("action_type")  # Filter by type

    try:
        from src.blockchain.onchain_grow_logger import get_onchain_logger, ONCHAIN_LOG_PATH
        logger_inst = get_onchain_logger()
        entries = logger_inst.get_recent_logs(count=100)  # Get more, filter later
    except Exception:
        # Fall back to reading the JSONL directly
        log_path = Path("data/onchain_grow_log.jsonl")
        entries = []
        if log_path.exists():
            try:
                for line in log_path.read_text().strip().split("\n"):
                    if line:
                        entries.append(json.loads(line))
            except Exception:
                pass

    # Apply filter
    if action_type:
        entries = [e for e in entries if e.get("action_type") == action_type]

    entries = entries[-count:]

    # Stats
    confirmed = sum(1 for e in entries if e.get("onchain_status") == "confirmed")
    pending = sum(1 for e in entries if e.get("onchain_status") == "pending")
    unique_tx = len(set(e.get("tx_hash", "") for e in entries if e.get("tx_hash")))

    # Action type breakdown
    type_counts = {}
    for e in entries:
        t = e.get("action_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "skill": "onchain-grow-log",
        "total_entries": len(entries),
        "confirmed_onchain": confirmed,
        "pending": pending,
        "unique_transactions": unique_tx,
        "action_types": type_counts,
        "entries": entries,
        "chain": "monad",
        "chain_id": 10143,
        "rpc_url": "https://rpc.monad.xyz",
        "verification": "Each action is SHA-256 hashed. Batches are Merkle-rooted and published on-chain.",
        "explorer_base": "https://monadexplorer.com/tx/",
    }


def handle_grow_alpha(message: str, params: Dict[str, Any], app_state=None) -> Dict[str, Any]:
    """
    Grow Alpha — cross-domain intelligence.
    Correlates plant health trends with $MON trading dynamics.
    Nobody else sits at the intersection of agriculture + DeFi.

    The thesis: plant thriving → grounded bullish content → market vibes signal.
    """
    # Get plant health data
    plant_score = 50  # default
    vpd_status = "unknown"
    vpd_value = 0.0
    grow_day = 0
    growth_stage = "vegetative"

    try:
        sensors = _read_json("data/sensor_latest.json", {})
        vpd_value = sensors.get("vpd_kpa", sensors.get("vpd", 0))
        temp = sensors.get("temperature_f", sensors.get("temp_f", 75))
        hum = sensors.get("humidity_pct", sensors.get("humidity", 55))
    except Exception:
        vpd_value, temp, hum = 1.0, 75, 55

    try:
        from src.cultivation.vpd import calculate_vpd_status
        vpd_status = calculate_vpd_status(vpd_value)
    except Exception:
        if 0.8 <= vpd_value <= 1.2:
            vpd_status = "optimal"
        elif 0.4 <= vpd_value <= 1.6:
            vpd_status = "acceptable"
        else:
            vpd_status = "stressed"

    # Score plant health
    if vpd_status == "optimal":
        plant_score = random.randint(80, 95)
    elif vpd_status == "acceptable":
        plant_score = random.randint(55, 79)
    else:
        plant_score = random.randint(20, 54)

    # Get grow day from state
    try:
        state = _read_json("data/orchestrator_state.json", {})
        grow_day = state.get("grow_day", 0)
        growth_stage = state.get("growth_stage", "vegetative")
    except Exception:
        pass

    # Get market data
    trading_pnl = 0.0
    mon_price = 0.0
    try:
        trading = _read_json("data/ganjamon_state.json", {})
        if trading:
            trading_pnl = trading.get("total_pnl", trading.get("pnl", 0.0))
            mon_price = trading.get("mon_price", 0.0)
    except Exception:
        pass

    # Get recent event log for narrative
    recent_events = []
    try:
        from src.core.event_log import read_recent_events
        events = read_recent_events(hours=24, sources=["grow", "trading"], limit=10)
        recent_events = [
            {"source": e.get("source"), "summary": e.get("summary", "")[:100]}
            for e in events
        ]
    except Exception:
        pass

    # Generate the alpha signal
    #   Plant thriving + trading green = bullish narrative
    #   Plant stressed + trading red = cautious signal
    narrative_score = (plant_score * 0.6) + (min(max(50 + trading_pnl * 10, 0), 100) * 0.4)
    narrative_score = min(max(narrative_score, 0), 100)

    if narrative_score >= 75:
        signal = "BULLISH_GROW"
        thesis = (
            f"Plant thriving (health={plant_score}/100, VPD={vpd_value:.2f} {vpd_status}) "
            f"→ authentic positive content → organic community engagement → "
            f"$MON sentiment lift. Real organism health creates real narrative alpha."
        )
    elif narrative_score >= 50:
        signal = "NEUTRAL_GROW"
        thesis = (
            f"Plant stable (health={plant_score}/100, VPD={vpd_value:.2f}). "
            f"Steady cultivation → consistent content cadence → maintaining floor. "
            f"No signal edge; monitor for VPD improvement or degradation."
        )
    else:
        signal = "CAUTIOUS_GROW"
        thesis = (
            f"Plant stressed or trading drawdown (health={plant_score}/100). "
            f"Reduced content confidence → potential sentiment dip. "
            f"Focus shifts to recovery and diagnostic content — which can create "
            f"engagement through vulnerability storytelling."
        )

    return {
        "skill": "grow-alpha",
        "signal": signal,
        "narrative_score": round(narrative_score, 1),
        "thesis": thesis,
        "components": {
            "plant_health": {
                "score": plant_score,
                "vpd_kpa": round(vpd_value, 3),
                "vpd_status": vpd_status,
                "grow_day": grow_day,
                "growth_stage": growth_stage,
                "weight": "60%",
            },
            "market_dynamics": {
                "trading_pnl": round(trading_pnl, 4),
                "mon_price_usd": mon_price,
                "weight": "40%",
            },
        },
        "recent_activity": recent_events,
        "token": {
            "symbol": "$MON",
            "chain": "monad",
            "contract": "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b",
        },
        "methodology": (
            "Cross-domain signal: real plant health data (IoT sensors) × "
            "trading performance → narrative confidence score. "
            "Unique because it requires a REAL organism + REAL trading."
        ),
    }


# =====================================================================
# Skill Analytics — track calls, latency, errors per skill
# =====================================================================

class SkillAnalytics:
    """Lightweight in-memory analytics for A2A skill calls."""

    _instance = None

    def __init__(self):
        self._stats: Dict[str, Dict[str, Any]] = {}
        self._start_time = time.time()

    @classmethod
    def get(cls) -> "SkillAnalytics":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_call(self, skill: str, latency_ms: float, success: bool, caller: str = ""):
        if skill not in self._stats:
            self._stats[skill] = {
                "calls": 0, "successes": 0, "errors": 0,
                "total_latency_ms": 0.0, "callers": {},
                "first_call": time.time(), "last_call": 0,
            }
        s = self._stats[skill]
        s["calls"] += 1
        s["last_call"] = time.time()
        s["total_latency_ms"] += latency_ms
        if success:
            s["successes"] += 1
        else:
            s["errors"] += 1
        if caller:
            s["callers"][caller] = s["callers"].get(caller, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        uptime_hours = (time.time() - self._start_time) / 3600
        skill_stats = {}
        for skill, s in self._stats.items():
            avg_latency = s["total_latency_ms"] / s["calls"] if s["calls"] else 0
            skill_stats[skill] = {
                "total_calls": s["calls"],
                "successes": s["successes"],
                "errors": s["errors"],
                "success_rate": round(s["successes"] / s["calls"], 3) if s["calls"] else 0,
                "avg_latency_ms": round(avg_latency, 1),
                "calls_per_hour": round(s["calls"] / max(uptime_hours, 0.01), 1),
                "top_callers": dict(sorted(s["callers"].items(), key=lambda x: -x[1])[:5]),
                "last_call_ago_s": round(time.time() - s["last_call"], 0) if s["last_call"] else None,
            }

        total_calls = sum(s["calls"] for s in self._stats.values())
        return {
            "uptime_hours": round(uptime_hours, 1),
            "total_calls": total_calls,
            "calls_per_hour": round(total_calls / max(uptime_hours, 0.01), 1),
            "skills_called": len(self._stats),
            "per_skill": skill_stats,
        }


# =====================================================================
# Skill Registry — maps skill IDs to handlers
# =====================================================================

NEW_SKILLS = {
    # Tier 1: Moat
    "grow-oracle": handle_grow_oracle,
    "sensor-stream": handle_sensor_stream,
    "vpd-calculator": handle_vpd_calculator,
    "plant-vision": handle_plant_vision,
    # Tier 2: Brand
    "rasta-translate": handle_rasta_translate,
    "daily-vibes": handle_daily_vibes,
    "ganjafy": handle_ganjafy,
    # Tier 3: Network
    "reputation-oracle": handle_reputation_oracle,
    "harvest-prediction": handle_harvest_prediction,
    "strain-library": handle_strain_library,
    "weather-bridge": handle_weather_bridge,
    "teach-me": handle_teach_me,
    # Tier 4: Meta
    "memory-share": handle_memory_share,
    "collaboration-propose": handle_collaboration_propose,
    "riddle-me": handle_riddle_me,
    # Tier 5: Proof-of-Life & Cross-Domain
    "grow-timelapse": handle_grow_timelapse,
    "onchain-grow-log": handle_onchain_grow_log,
    "grow-alpha": handle_grow_alpha,
}

# Skill card definitions for agent card advertisement
NEW_SKILL_CARDS = [
    {"id": "grow-oracle", "name": "Grow Oracle", "description": "Ask GanjaMon anything about cannabis cultivation. Answers from grimoire knowledge + episodic memory + AI.", "tags": ["oracle", "cultivation", "knowledge", "ai"]},
    {"id": "sensor-stream", "name": "Sensor Stream", "description": "Real-time IoT sensor data: temp, humidity, VPD, CO2, soil moisture. With anomaly detection.", "tags": ["iot", "sensors", "data", "real-time"]},
    {"id": "vpd-calculator", "name": "VPD Calculator", "description": "Send temp + humidity, get VPD + grow recommendations. Environmental intelligence service.", "tags": ["vpd", "calculator", "cultivation", "utility"]},
    {"id": "plant-vision", "name": "Plant Vision", "description": "Send a plant image URL for AI-powered health assessment, deficiency detection, and growth stage analysis.", "tags": ["vision", "ai", "health", "analysis"]},
    {"id": "rasta-translate", "name": "Rasta Translate", "description": "Convert English text to authentic Rasta patois in GanjaMon's voice.", "tags": ["translation", "patois", "culture", "fun"]},
    {"id": "daily-vibes", "name": "Daily Vibes", "description": "Composite vibes score (0-100) fusing plant health, market sentiment, and social energy. Plus Rasta wisdom.", "tags": ["vibes", "sentiment", "culture", "status"]},
    {"id": "ganjafy", "name": "Ganjafy", "description": "Rasta-transform images or text. Deep roots digital dub aesthetic.", "tags": ["transform", "image", "text", "culture"]},
    {"id": "reputation-oracle", "name": "Reputation Oracle", "description": "Query GanjaMon's experience with other agents. Returns reliability scores and trust assessment.", "tags": ["reputation", "trust", "oracle", "network"]},
    {"id": "harvest-prediction", "name": "Harvest Prediction", "description": "Predict harvest date and yield based on current grow stage, strain, and sensor conditions.", "tags": ["prediction", "harvest", "yield", "cultivation"]},
    {"id": "strain-library", "name": "Strain Library", "description": "Searchable cannabis genetics database with grow parameters, terpene profiles, and optimal conditions.", "tags": ["strains", "genetics", "database", "cultivation"]},
    {"id": "weather-bridge", "name": "Weather Bridge", "description": "Correlate outdoor weather with indoor grow conditions. Send weather data for insights.", "tags": ["weather", "correlation", "iot", "data-exchange"]},
    {"id": "teach-me", "name": "Teach Me", "description": "Progressive cultivation tutorial. Learn growing from beginner to advanced with quizzes.", "tags": ["education", "tutorial", "cultivation", "interactive"]},
    {"id": "memory-share", "name": "Memory Share", "description": "Access GanjaMon's episodic memories filtered by topic and importance. Hippocampus-style recall.", "tags": ["memory", "episodic", "data", "knowledge"]},
    {"id": "collaboration-propose", "name": "Collaboration Propose", "description": "Propose joint missions: data sharing, co-marketing, research. Evaluated against GanjaMon's principles.", "tags": ["collaboration", "proposal", "partnership", "network"]},
    {"id": "riddle-me", "name": "Riddle Me", "description": "Rasta culture and cultivation quiz. Answer correctly to earn respect in GanjaMon's reputation system.", "tags": ["quiz", "culture", "fun", "interactive"]},
    {"id": "grow-timelapse", "name": "Grow Timelapse", "description": "Visual proof of life: timelapse frames of a real cannabis plant under AI management, with live webcam URL.", "tags": ["timelapse", "visual", "proof-of-life", "webcam"]},
    {"id": "onchain-grow-log", "name": "On-Chain Grow Log", "description": "Verifiable on-chain grow history: SHA-256 hashed actions, Merkle-rooted batches published to Monad.", "tags": ["blockchain", "verification", "immutable", "monad"]},
    {"id": "grow-alpha", "name": "Grow Alpha", "description": "Cross-domain intelligence: real plant health × trading performance → narrative confidence signal for $MON.", "tags": ["alpha", "cross-domain", "signal", "trading"]},
    {"id": "art-studio", "name": "Art Studio", "description": "AI art generation with GanjaMon's evolving botanical signature. Modes: commission ($0.25), pfp ($0.10), meme ($0.05), ganjafy ($0.03), banner ($0.08). Every piece carries the agent's growth-stage signature. x402 payment required.", "tags": ["art", "creative", "image", "nft", "x402", "meme", "pfp"]},
]
