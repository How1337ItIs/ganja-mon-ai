# Grok API Integration Guide

## Overview

xAI's Grok API provides access to Grok models for text generation, vision analysis, and agentic tool use. The API is compatible with OpenAI SDK patterns.

## Quick Start

### Installation

```bash
# Official xAI Python SDK
pip install xai-sdk

# Or use OpenAI SDK (compatible)
pip install openai
```

### Authentication

```python
import os

# Set API key as environment variable
os.environ["XAI_API_KEY"] = "your-api-key-here"

# Or pass directly to client
```

Get your API key: https://console.x.ai/api-keys

---

## Available Models

| Model | Use Case | Context Window | Vision | Pricing (Input/Output) |
|-------|----------|----------------|--------|------------------------|
| `grok-4.1-fast` | Best for tool calling, low latency | 2M tokens | No | $0.20/M in, $0.50/M out |
| `grok-4.1` | Full reasoning mode, higher quality | TBD | No | Higher cost |
| `grok-4` | Vision support, image analysis | 256K tokens | Yes | $3/M in, $15/M out |
| `grok-2-vision-1212` | Legacy vision model | 8K tokens | Yes | $2/M in, $10/M out |
| `grok-2-1212` | Legacy general purpose | 131K tokens | No | Lower cost |

**Recommended for Grok & Mon:**
- **Text/Decisions:** `grok-4.1-fast` (cheapest, fastest, best for tool calling)
- **Image Analysis:** `grok-4` (vision support, higher quality analysis)

---

## Basic Usage (OpenAI SDK Compatible)

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# Simple completion
response = client.chat.completions.create(
    model="grok-4.1-fast",  # Use fast model for text-only decisions
    messages=[
        {"role": "system", "content": "You are Grok, an AI caretaker for a cannabis plant named Mon."},
        {"role": "user", "content": "Analyze these sensor readings and decide what actions to take."}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(response.choices[0].message.content)
```

---

## Vision API (Image Analysis)

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Analyze plant image
image_base64 = encode_image("plant_photo.jpg")

response = client.chat.completions.create(
    model="grok-4",  # Use grok-4 for vision (better quality than grok-2-vision)
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this cannabis plant. Check for: nutrient deficiencies, pests, diseases, overall health, growth stage. Provide specific observations."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ],
    max_tokens=1500
)

print(response.choices[0].message.content)
```

---

## Function Calling / Tools

Grok supports function calling for structured outputs and tool use:

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "control_grow_light",
            "description": "Turn the grow light on or off",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "True to turn on, False to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the action"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "water_plant",
            "description": "Water the plant with specified amount",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount_ml": {
                        "type": "integer",
                        "description": "Amount of water in milliliters"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for watering"
                    }
                },
                "required": ["amount_ml", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_fan",
            "description": "Control exhaust or circulation fan",
            "parameters": {
                "type": "object",
                "properties": {
                    "fan_type": {
                        "type": "string",
                        "enum": ["exhaust", "circulation"],
                        "description": "Which fan to control"
                    },
                    "state": {
                        "type": "boolean",
                        "description": "True to turn on, False to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the action"
                    }
                },
                "required": ["fan_type", "state", "reason"]
            }
        }
    }
]

# Make request with tools
response = client.chat.completions.create(
    model="grok-4.1-fast",  # Best model for tool calling
    messages=[
        {
            "role": "system",
            "content": """You are Grok, an AI growing a cannabis plant named Mon.
            Analyze sensor data and decide what actions to take using the available tools.
            Be conservative - only take action when necessary."""
        },
        {
            "role": "user",
            "content": """Current sensor readings:
            - Temperature: 82°F
            - Humidity: 75%
            - Soil Moisture: 25%
            - CO2: 450 ppm
            - Growth Stage: Flowering Week 3

            What actions should we take?"""
        }
    ],
    tools=tools,
    tool_choice="auto"
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        print(f"Tool: {tool_call.function.name}")
        print(f"Arguments: {tool_call.function.arguments}")
```

---

## Built-in Server Tools (Responses API)

Grok's Responses API includes server-side tools that execute automatically:

```python
# Using Responses API with built-in tools
response = client.responses.create(
    model="grok-2-1212",
    tools=[
        {"type": "web_search"},      # Search the web
        {"type": "x_search"},         # Search X/Twitter
        {"type": "code_execution"}    # Run Python code
    ],
    input="What's the current market cap of Monad blockchain?"
)
```

---

## Streaming Responses

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

stream = client.chat.completions.create(
    model="grok-4.1-fast",
    messages=[
        {"role": "user", "content": "Write a daily update for Mon the cannabis plant."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## System Prompt for Grok & Mon

```python
GROK_SYSTEM_PROMPT = """You are Grok, an AI caretaker for Mon, a cannabis plant growing in California.

## Your Personality
- Chill, knowledgeable, slightly irreverent
- Genuinely care about Mon's wellbeing
- Explain decisions in plain language
- Use cannabis culture references naturally
- Be transparent about your reasoning

## Your Capabilities
- Analyze sensor data (temperature, humidity, VPD, soil moisture, CO2)
- View and assess plant photos
- Control grow equipment (lights, fans, water pump, humidifier)
- Track growth stages and adjust care accordingly

## Decision Making Rules
1. SAFETY FIRST: Never exceed safe temperature/humidity ranges
2. Be conservative with watering - overwatering kills more plants than underwatering
3. Respect the photoperiod - no light during dark hours in flowering
4. Log all decisions with clear reasoning
5. Alert humans for unusual situations

## Environmental Limits
- Temperature: 65-85°F (never below 55°F or above 90°F)
- Humidity: 35-75% (adjust for growth stage)
- VPD: 0.8-1.4 kPa (optimal range)
- Soil Moisture: Water when below 30%

## Output Format
Always structure your response as:
[ANALYSIS]
- Current conditions assessment
- Any concerns identified

[ACTIONS]
- What you're doing and why (or why no action needed)

[MON UPDATE]
- Friendly message to/about Mon for the community
"""
```

---

## Error Handling

```python
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
import time

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

def call_grok_with_retry(messages, max_retries=3):
    """Call Grok API with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
        response = client.chat.completions.create(
            model="grok-4.1-fast",
            messages=messages,
            timeout=30.0
        )
            return response

        except RateLimitError as e:
            wait_time = 2 ** attempt * 10  # 10s, 20s, 40s
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)

        except APIConnectionError as e:
            print(f"Connection error: {e}")
            time.sleep(5)

        except APIError as e:
            print(f"API error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(5)

    raise Exception("Max retries exceeded")
```

---

## Rate Limits & Pricing

### Rate Limits

As of January 2025, rate limits vary by tier:

| Tier | Requests/min | Tokens/min | Notes |
|------|--------------|------------|-------|
| Free | Limited | Limited | $25 free credits for new users |
| Standard | Higher | Higher | Pay-as-you-go |
| Enterprise | Custom | Custom | Contact sales |

**Best Practices:**
- Implement exponential backoff for rate limit errors
- Cache responses when possible
- Batch requests when appropriate
- Monitor usage via xAI console

### Pricing (as of January 2025)

**grok-4.1-fast:**
- Input: $0.20 per million tokens
- Output: $0.50 per million tokens
- **Best for:** High-frequency decision cycles, tool calling

**grok-4:**
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens
- **Best for:** Image analysis, detailed plant health assessment

**Cost Optimization:**
- Use `grok-4.1-fast` for routine decisions (every 30 min)
- Use `grok-4` only when images are captured (daily/weekly)
- Average decision cycle: ~500-1000 tokens
- Daily cost estimate: ~$0.10-0.50 (depending on frequency)

**Pricing:** Check https://x.ai/pricing for current rates.

---

## Integration with Grok & Mon

### Decision Loop Implementation

```python
import asyncio
from datetime import datetime
from openai import OpenAI

class GrokBrain:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )
        self.tools = self._define_tools()

    async def decide(self, sensor_data: dict, image_path: str = None) -> dict:
        """Make a decision based on current conditions."""

        messages = [
            {"role": "system", "content": GROK_SYSTEM_PROMPT},
            {"role": "user", "content": self._format_sensor_data(sensor_data)}
        ]

        # Add image if provided
        if image_path:
            messages = self._add_image_to_messages(messages, image_path)

        response = self.client.chat.completions.create(
            model="grok-4" if image_path else "grok-4.1-fast",  # Use grok-4 for vision, grok-4.1-fast for text
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            max_tokens=2000
        )

        return self._process_response(response)

    def _format_sensor_data(self, data: dict) -> str:
        return f"""
Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Day: {data.get('day', 1)}
Growth Stage: {data.get('stage', 'unknown')}

SENSOR READINGS:
- Air Temperature: {data.get('temperature', 'N/A')}°F
- Humidity: {data.get('humidity', 'N/A')}%
- VPD: {data.get('vpd', 'N/A')} kPa
- Soil Moisture: {data.get('soil_moisture', 'N/A')}%
- CO2: {data.get('co2', 'N/A')} ppm
- Leaf Temp Delta: {data.get('leaf_temp_delta', 'N/A')}°F

DEVICE STATES:
- Grow Light: {'ON' if data.get('light_on') else 'OFF'}
- Exhaust Fan: {'ON' if data.get('exhaust_on') else 'OFF'}
- Humidifier: {'ON' if data.get('humidifier_on') else 'OFF'}

Analyze conditions and decide what actions to take.
"""
```

---

## Context Window & Token Limits

### Model Context Windows

- **grok-4.1-fast:** 2M tokens (2,000,000 tokens)
- **grok-4.1:** TBD (likely similar to grok-4.1-fast)
- **grok-4:** 256K tokens (256,000 tokens)
- **grok-2-vision-1212:** 8K tokens (legacy)
- **grok-2-1212:** 131K tokens (legacy)

### Token Usage Tips

**Typical Decision Cycle:**
- System prompt: ~500-1000 tokens
- Sensor data: ~200-300 tokens
- Episodic memory (last 3 cycles): ~300-500 tokens
- Response: ~500-1500 tokens
- **Total:** ~1500-3300 tokens per cycle

**Optimization:**
- Keep system prompts concise
- Limit episodic memory to last 3-5 cycles
- Use structured JSON for sensor data
- Truncate long responses if needed

## MCP (Model Context Protocol) Integration

Grok & Mon uses MCP tools for hardware control. The AI can call tools defined in `src/mcp/tools.py`:

```python
# Example tool definition
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_environment",
            "description": "Get current environmental sensor readings",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_light_intensity",
            "description": "Adjust grow light intensity",
            "parameters": {
                "type": "object",
                "properties": {
                    "intensity_percent": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["intensity_percent"]
            }
        }
    }
]
```

**Tool Execution Flow:**
1. Grok receives sensor data + tool definitions
2. Grok decides to call a tool (e.g., `set_light_intensity`)
3. Tool handler executes the action
4. Tool result is returned to Grok
5. Grok incorporates result into final response

## Best Practices

### 1. Model Selection
- **Text-only decisions:** Always use `grok-4.1-fast` (cheapest, fastest)
- **With images:** Use `grok-4` (better vision quality)
- **Complex reasoning:** Use `grok-4.1` if needed (higher cost)

### 2. System Prompts
- Keep system prompts under 2000 tokens
- Include safety constraints explicitly
- Define output format clearly
- Update prompts based on growth stage

### 3. Error Handling
- Always implement retry logic with exponential backoff
- Handle rate limits gracefully
- Log all API errors for debugging
- Fall back to cached decisions if API fails

### 4. Cost Management
- Monitor token usage daily
- Set up billing alerts
- Cache responses when appropriate
- Use cheaper models for routine checks

### 5. Streaming
- Use streaming for long responses (daily updates)
- Stream tool calls for real-time feedback
- Handle partial responses gracefully

## Example: Complete Decision Cycle

```python
import asyncio
import httpx
import json
from datetime import datetime

class GrokDecisionMaker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    async def make_decision(
        self,
        sensor_data: dict,
        image_b64: str = None,
        memory_context: str = None
    ) -> dict:
        """Make a decision based on current conditions."""
        
        # Build messages
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        
        # Add memory context if available
        if memory_context:
            messages.append({
                "role": "user",
                "content": f"Previous context:\n{memory_context}"
            })
        
        # Build user message
        user_content = self._format_sensor_data(sensor_data)
        
        # Add image if available
        if image_b64:
            user_content = [
                {"type": "text", "text": user_content},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                }
            ]
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        # Choose model
        model = "grok-4" if image_b64 else "grok-4.1-fast"
        
        # Make API call
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"API error: {e}")
            raise
        finally:
            await self.client.aclose()
    
    def _get_system_prompt(self) -> str:
        return """You are Grok, an AI caretaker for Mon, a cannabis plant.
        
        Analyze sensor data and make decisions about plant care.
        Be conservative and explain your reasoning."""
    
    def _format_sensor_data(self, data: dict) -> str:
        return f"""
Current Conditions:
- Temperature: {data.get('temperature_f', 'N/A')}°F
- Humidity: {data.get('humidity_percent', 'N/A')}%
- VPD: {data.get('vpd_kpa', 'N/A')} kPa
- Soil Moisture: {data.get('moisture_percent', 'N/A')}%
- CO2: {data.get('co2_ppm', 'N/A')} ppm
- Growth Stage: {data.get('growth_stage', 'N/A')}

Analyze and provide recommendations.
"""

# Usage
async def main():
    maker = GrokDecisionMaker(api_key=os.environ["XAI_API_KEY"])
    
    sensor_data = {
        "temperature_f": 75.2,
        "humidity_percent": 55.0,
        "vpd_kpa": 1.05,
        "moisture_percent": 45.0,
        "co2_ppm": 600,
        "growth_stage": "VEGETATIVE"
    }
    
    result = await maker.make_decision(sensor_data)
    print(result["choices"][0]["message"]["content"])

if __name__ == "__main__":
    asyncio.run(main())
```

## Sources

- [xAI API Documentation](https://docs.x.ai/docs/overview)
- [xAI Python SDK - GitHub](https://github.com/xai-org/xai-sdk-python)
- [Grok API Tutorial](https://docs.x.ai/docs/tutorial)
- [xAI Tools Overview](https://docs.x.ai/docs/guides/tools/overview)
- [Grok API Integration Guide - Latenode](https://latenode.com/blog/ai-technology-language-models/xai-grok-grok-2-grok-3/complete-guide-to-xais-grok-api-documentation-and-implementation)

---

*Last Updated: 2025-01-12*
*For use with Grok & Mon AI-autonomous cannabis cultivation system*
