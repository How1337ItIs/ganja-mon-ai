# Agentic Upgrade — Multi-Turn Tool-Use Loop

**Date:** February 2026  
**Status:** Implemented  
**Files Modified:** `src/ai/brain.py`, `src/ai/tools.py`

## What Changed

Ganja Mon evolved from a **timer-driven oracle** (single API call → hardcoded actions) to a **genuine agentic loop** where Grok can:

1. **Call tools** to gather information or take actions
2. **Receive results** back as `tool` role messages
3. **Reason over results** and decide to call more tools
4. **Iterate** up to `MAX_TOOL_ROUNDS` (8) before producing a final answer
5. **Self-diagnose** by reading its own system status and memory

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Orchestrator │────▶│  GrokBrain   │────▶│  Grok API    │
│ (trigger)    │     │  .decide()   │◀────│  (w/ tools)  │
└─────────────┘     │              │     └──────────────┘
                    │  AGENTIC LOOP│
                    │  ┌──────────┐│     ┌──────────────┐
                    │  │ Execute  ││────▶│ ToolExecutor  │
                    │  │ tools    ││◀────│ (39 tools)    │
                    │  └──────────┘│     └──────────────┘
                    │              │
                    │  Feed results│
                    │  back to     │
                    │  Grok as     │
                    │  `tool` msgs │
                    └──────────────┘
```

### Before (Oracle Mode)
```python
# Single API call, single batch of tool calls, done
response, tool_calls, tokens = await self._call_grok(messages)
for tc in tool_calls:
    result = executor.execute(tc)
    # Result is LOST — never sent back to Grok
    response_text += format_tool_result(result)
```

### After (Agentic Loop)
```python
while round_num < MAX_TOOL_ROUNDS:
    response, tool_calls, tokens = await self._call_grok(messages)
    
    if not tool_calls:
        return response  # Final answer — done!
    
    messages.append(assistant_message_with_tool_calls)
    
    for tc in tool_calls:
        result = executor.execute(tc)
        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": format_result(result),
        })
    
    # Loop! Grok sees results, can call more tools
```

## Tool Registry (39 Tools)

### 🌱 Grow Domain (8 tools)
| Tool | Description |
|------|-------------|
| `water_plant` | Dispense water (50-500ml) |
| `control_grow_light` | Light on/off (photoperiod-aware) |
| `control_exhaust_fan` | Exhaust fan on/off |
| `control_circulation_fan` | Circulation fan on/off |
| `control_heat_mat` | Heat mat on/off |
| `control_humidifier` | Humidifier on/off |
| `control_dehumidifier` | Dehumidifier on/off |
| `inject_co2` | CO2 injection |

### 📱 Social Domain (4 tools) — NEW
| Tool | Description |
|------|-------------|
| `post_tweet` | Tweet from @GanjaMonAI (280 char, no hashtags, no 🌿) |
| `post_farcaster` | Cast to Farcaster channels |
| `send_telegram` | Message Telegram community |
| `check_social_metrics` | Get 24h engagement metrics |

### ⛓️ Blockchain Domain (3 tools) — NEW
| Tool | Description |
|------|-------------|
| `get_token_metrics` | $MON price, MCap, volume, holders |
| `get_wallet_balance` | Check Monad wallet balance |
| `publish_reputation` | Publish ERC-8004 reputation on-chain |

### 📈 Trading Domain (2 tools) — NEW
| Tool | Description |
|------|-------------|
| `get_portfolio` | Trading agent's paper portfolio |
| `get_market_regime` | Bull/bear/crab + strategy tracker |

### 🧠 Memory/Learning Domain (4 tools) — NEW
| Tool | Description |
|------|-------------|
| `query_grimoire` | Search persistent knowledge store |
| `store_learning` | Store new learning for future |
| `read_sensors_live` | Re-read sensors in real-time |
| `get_grow_history` | Past decisions, watering, sensor trends |

### 🔍 Research Domain (5 tools)
| Tool | Description |
|------|-------------|
| `web_search` | Web search via Brave |
| `browse_url` | Fetch and read a URL |
| `deep_research` | Multi-source deep research |
| `smart_search` | Smart search with summarization |
| `spawn_research` | Spawn research subagent |

### 🤖 A2A Domain (4 tools)
| Tool | Description |
|------|-------------|
| `discover_agents` | Discover agents on A2A registry |
| `call_agent` | Call another agent |
| `multi_agent_query` | Multi-agent query |
| `a2a_outreach` | Proactive A2A outreach |

### 🔧 System Domain (2 tools) — NEW
| Tool | Description |
|------|-------------|
| `get_system_status` | Self-diagnostics |
| `emit_event` | Write to shared event log |

### 📋 Operational Tools (7 tools)
| Tool | Description |
|------|-------------|
| `take_photo` | Capture webcam image + vision analysis |
| `log_observation` | Record grow observations |
| `update_grow_stage` | Transition growth stage |
| `request_human_help` | Request human intervention |
| `queue_email` | Queue outbound email |
| `query_allium` | On-chain data via Allium |
| `create_task` | Create agent task |

## Safety Features

- **MAX_TOOL_ROUNDS = 8**: Prevents infinite loops
- **MAX_TOOLS_PER_ROUND = 5**: Prevents tool call spam
- **LOOP_TIMEOUT_SECONDS = 120**: Hard timeout on entire cycle
- **No-tool fallback**: If max rounds hit, forces a final response without tools
- **Brand rule enforcement**: Tweet handler blocks hashtags and leaf emoji
- **Tool results truncated to 3KB** to prevent context overflow

## Interactive Sessions

New `interactive_query()` method allows untriggered queries:

```python
result = await brain.interactive_query(
    query="What's the current VPD and should I adjust anything?",
    growth_stage="vegetative",
    current_day=45,
)
```

Can be called from Telegram bot, API endpoint, or scheduled tasks.

## Trigger Types

The `DecisionResult` now tracks what triggered the decision:
- `scheduled` — Regular 2-hour cycle
- `reactive` — Sensor anomaly detected
- `telegram` — User command from Telegram
- `api` — External API request
- `interactive` — Ad-hoc query
- `anomaly` — Auto-triggered by watchdog

## Completed Integration (Phase 2)

1. ✅ **Event-driven triggers in orchestrator**: Sensor anomalies push to `_reactive_queue`, consumed by `_reactive_loop()` with 10-min cooldown
2. ✅ **Telegram `/askgrok` command**: Routes through `brain.interactive_query()` with full tool access
3. ✅ **API `/api/ai/ask` endpoint**: POST JSON `{"query": "..."}` → agentic brain with all 39 tools
4. ✅ **Trigger wiring**: `_run_ai_decision(trigger=...)` passes trigger through to `brain.decide()`
5. ✅ **Interactive query bridge**: `orchestrator.handle_interactive_query()` provides sensor context + brain access

## Next Steps (Phase 3)

1. **Deploy to Chromebook**: Push and test with real sensors/hardware
2. **Grok model upgrade**: The agentic loop benefits from reasoning models (`grok-4-1-fast-reasoning`)
3. **Tool result caching**: Cache read-only tool results within a round to reduce latency
4. **Token budget tracking**: Monitor total tokens per loop to prevent cost blowouts
5. **Reactive anomaly tuning**: Calibrate cooldown, threshold, and which anomalies trigger reactive decisions
