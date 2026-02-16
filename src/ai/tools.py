"""
AI Tools — Full Cross-Domain Registry
======================================

Tool definitions for Grok's agentic loop across ALL domains:
- Grow: sensors, hardware, cultivation
- Social: Twitter, Farcaster, Telegram, Moltbook
- Blockchain: $MON token, reputation, on-chain logging
- Trading: portfolio, market regime, strategy tracking
- Memory: grimoire, episodic memory, grow learning
- Research: web search, deep research, subagent spawning
- A2A: agent discovery, cross-agent communication
- System: status, scheduling, event logging

Each tool follows OpenAI function-calling format and is
executed through the ToolExecutor safety layer.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Tool Definitions (OpenAI function calling format)
# =============================================================================

GROW_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "water_plant",
            "description": "Dispense water to Mon. Use when soil moisture is low. Safe range is 50-300ml per watering. Check soil moisture readings before watering - both probes should be considered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount_ml": {
                        "type": "integer",
                        "description": "Amount of water in milliliters (50-500ml)",
                        "minimum": 50,
                        "maximum": 500
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for watering decision"
                    }
                },
                "required": ["amount_ml", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_grow_light",
            "description": "Turn the grow light on or off. IMPORTANT: During flowering (12/12 photoperiod), the light MUST be off during dark period (6 PM - 6 AM). Light during dark period causes hermaphroditism. The safety system will block attempts to turn on light during dark period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "true to turn on, false to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for light change"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_exhaust_fan",
            "description": "Turn exhaust fan on or off. Use for temperature control, humidity reduction, or air exchange. Running exhaust will lower CO2 levels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "true to turn on, false to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for exhaust change"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_circulation_fan",
            "description": "Turn circulation fan on or off. Circulation strengthens stems and prevents hot spots. Should usually be on during light period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "true to turn on, false to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for fan change"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_heat_mat",
            "description": "Turn heat mat on or off. Use when temperature is too low (below 20°C). Heat mat warms the root zone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "true to turn on, false to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for heat mat change"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_humidifier",
            "description": "Turn humidifier on or off. Use when humidity is too low. Be careful not to raise humidity too high (>70%) especially during flowering - causes mold/bud rot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "true to turn on, false to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for humidifier change"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_dehumidifier",
            "description": "Turn dehumidifier on or off. Use when humidity is too high (>65% in flowering). Critical for preventing bud rot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "boolean",
                        "description": "true to turn on, false to turn off"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for dehumidifier change"
                    }
                },
                "required": ["state", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inject_co2",
            "description": "Inject CO2 to boost photosynthesis. Only useful during light period when plant is photosynthesizing. Target 700-1000ppm. Don't inject if exhaust is running (wastes CO2) or if already above 1000ppm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Duration of CO2 injection in seconds (15-120)",
                        "minimum": 15,
                        "maximum": 120
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for CO2 injection"
                    }
                },
                "required": ["duration_seconds", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_photo",
            "description": "Capture a photo of Mon for visual inspection. Use to check plant health, growth progress, or verify sensor readings visually.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why you want to take a photo"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_observation",
            "description": "Log an observation or note about Mon without taking any action. Use for recording insights, tracking patterns, or noting things to monitor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "observation": {
                        "type": "string",
                        "description": "The observation to log"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["health", "growth", "environment", "concern", "milestone"],
                        "description": "Category of observation"
                    }
                },
                "required": ["observation", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_help",
            "description": "Request a HUMAN to do something physical/manual (refill reservoir, move camera, inspect plant, mix nutrients, clean sensor). Use when you can't safely proceed autonomously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "What the human should do (actionable, concrete)"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "How urgent this request is",
                        "default": "medium"
                    },
                    "details": {
                        "type": "string",
                        "description": "Optional extra context (what to look for, why it matters, how to do it)"
                    }
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "queue_email",
            "description": "Send an email from agent@grokandmon.com. Use for grow reports, partnership inquiries, or automated alerts. Rate limited to 10 emails/day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body text"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_grow_stage",
            "description": "Transition Mon to a new growth stage. This also updates photoperiod (18/6 for veg, 12/12 for flower). Only use when plant shows clear signs of stage transition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_stage": {
                        "type": "string",
                        "enum": ["seedling", "vegetative", "transition", "flowering", "late_flower", "harvest"],
                        "description": "The growth stage to transition to"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why the stage is changing (what signs you observed)"
                    }
                },
                "required": ["new_stage", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_allium",
            "description": "Query blockchain data via Allium API. Use for checking on-chain activity related to $MON token, wallet balances, or transaction history. Supports ethereum, base, solana chains (NOT Monad yet).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to run against Allium data warehouse"
                    },
                    "chain": {
                        "type": "string",
                        "enum": ["ethereum", "base", "solana"],
                        "description": "Blockchain to query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet via DuckDuckGo. Use for researching hackathon judges, competitors, news, token info, or any real-time information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results to return (default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_url",
            "description": "Fetch and read the text content of a web page. Use after web_search to read full articles, project pages, or documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch and read"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Max characters to extract (default 5000)",
                        "default": 5000
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deep_research",
            "description": "Full research pipeline: searches the web, reads top results, and synthesizes findings with AI. Returns structured findings and action items. Use for strategic research tasks. Takes 30-60 seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The research question to investigate"
                    },
                    "max_sources": {
                        "type": "integer",
                        "description": "Number of web pages to read (default 3)",
                        "default": 3
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "smart_search",
            "description": "Ask a question and get a sourced answer from the internet (via Perplexity). Fastest way to get current information. Returns a text answer with citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to search for and answer"
                    }
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_research",
            "description": "Spawn parallel research subagents for multiple questions at once. Each subagent does web search + LLM synthesis independently. Use when you need to research multiple topics simultaneously (e.g., hackathon judges, competitor analysis, market conditions). Returns structured findings from all subagents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "description": "List of research tasks to run in parallel",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {"type": "string", "description": "Research question or mission"},
                                "type": {"type": "string", "enum": ["research", "analyze", "strategy"], "description": "Type of subagent"},
                                "context": {"type": "string", "description": "Additional context for the subagent"}
                            },
                            "required": ["task"]
                        }
                    }
                },
                "required": ["tasks"]
            }
        }
    },
    # --- A2A (Agent-to-Agent) Tools ---
    {
        "type": "function",
        "function": {
            "name": "discover_agents",
            "description": "Search the 8004scan agent registry for other AI agents. Find agents by capability (skill), chain, minimum trust score. Returns agent names, URLs, skills, and trust scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chain": {"type": "string", "description": "Blockchain to search (monad, base, ethereum)", "default": "monad"},
                    "skills": {"type": "array", "items": {"type": "string"}, "description": "Filter by skill IDs (e.g., ['alpha-scan', 'trading'])"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags (e.g., ['defi', 'nft'])"},
                    "min_trust": {"type": "number", "description": "Minimum trust score (0-100)", "default": 0},
                    "has_a2a": {"type": "boolean", "description": "Only return agents with A2A endpoints", "default": True},
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_agent",
            "description": "Call another AI agent via A2A protocol. Send a message to a specific agent's skill and get the response. Use discover_agents first to find agent URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_url": {"type": "string", "description": "A2A endpoint URL of the agent to call"},
                    "skill": {"type": "string", "description": "Skill ID to invoke on the remote agent"},
                    "message": {"type": "string", "description": "Natural language message/query for the agent"},
                },
                "required": ["agent_url", "skill", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "multi_agent_query",
            "description": "Query multiple agents in parallel for the same skill/question. Fan-out to all matching agents on a chain and aggregate responses. Use for consensus, cross-validation, or broad signal collection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "Skill ID to query across agents"},
                    "message": {"type": "string", "description": "Natural language query"},
                    "chain": {"type": "string", "description": "Chain to search for agents", "default": "monad"},
                    "max_agents": {"type": "integer", "description": "Maximum agents to query (1-10)", "default": 5},
                    "min_trust": {"type": "number", "description": "Minimum trust score for agents", "default": 50},
                },
                "required": ["skill", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "a2a_outreach",
            "description": "Trigger a manual A2A outreach round. Discovers agents on 8004scan with real A2A endpoints, calls up to 3 of them, exchanges cultivation data, and reports results. Use to proactively connect with other agents on Monad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_agents": {"type": "integer", "description": "Max agents to call this round (1-5)", "default": 3},
                    "chain": {"type": "string", "description": "Chain to discover agents on", "default": "monad"},
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task for the engagement daemon or yourself to execute later. Use this to queue social posts, research, email outreach, or any work that should happen asynchronously. The engagement daemon picks up tasks by tool_hint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short actionable title for the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what needs to be done"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Task priority level"
                    },
                    "tool_hint": {
                        "type": "string",
                        "enum": ["social_post", "moltbook_post", "queue_email", "telegram_message", "web_research", "reasoning"],
                        "description": "Which execution path the engagement daemon should use"
                    }
                },
                "required": ["title", "description", "priority", "tool_hint"]
            }
        }
    },
    # =========================================================================
    # SOCIAL DOMAIN TOOLS
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "post_tweet",
            "description": "Post a tweet from the @GanjaMonAI account. Must be in Ganja Mon rasta voice. NO HASHTAGS. NO leaf emoji. Max 280 chars. Use for grow updates, market commentary, community vibes. Rate limited to 4/day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Tweet text (max 280 chars, Ganja Mon voice, NO hashtags)"
                    },
                    "include_photo": {
                        "type": "boolean",
                        "description": "Whether to include a webcam photo of Mon (only during light period)",
                        "default": False
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_farcaster",
            "description": "Post a cast to Farcaster. Can target specific channels (monad, ai, cannabis, degen, base). Ganja Mon rasta voice. Max 1024 chars.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Cast text (max 1024 chars)"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Farcaster channel to post to (optional)",
                        "enum": ["monad", "ai", "cannabis", "degen", "base"]
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram",
            "description": "Send a message to the Ganja Mon Telegram community group. Use for grow updates, community announcements, or responding to community activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message text to send"
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_social_metrics",
            "description": "Get current social engagement metrics across all platforms (Twitter, Farcaster, Telegram, Moltbook). Returns post counts, engagement rates, follower changes, and top-performing content from the last 24 hours.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # =========================================================================
    # BLOCKCHAIN / TOKEN DOMAIN TOOLS
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_token_metrics",
            "description": "Get current $MON token metrics: price, market cap, 24h volume, holder count, recent trades. Data from DexScreener + SocialScan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force API refresh (default uses cache)",
                        "default": False
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wallet_balance",
            "description": "Check MON/ETH balance of the agent's wallet or any Monad address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Monad address to check (default: agent's own wallet)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "publish_reputation",
            "description": "Trigger a reputation publish cycle — gathers grow metrics, trading performance, community size, and publishes on-chain to the ERC-8004 ReputationRegistry. Costs gas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why you're publishing now (e.g., 'milestone reached', 'daily cycle')"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    # =========================================================================
    # TRADING / PORTFOLIO DOMAIN TOOLS
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_portfolio",
            "description": "Get the GanjaMon trading agent's current portfolio: cash balance, open positions, recent trades, total P&L. The trading agent runs as a subprocess.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_regime",
            "description": "Get current market regime classification (bull/bear/crab) and strategy performance. Includes per-strategy win rates, auto-disable status, and goal progress.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # =========================================================================
    # MEMORY / LEARNING DOMAIN TOOLS
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "query_grimoire",
            "description": "Search the Grimoire (persistent knowledge store) across domains: trading, cultivation, social, market_regimes. Returns learned insights with confidence scores. Use to recall past learnings before making decisions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": ["trading", "cultivation", "social", "market_regimes", "all"],
                        "description": "Knowledge domain to search"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (e.g., ['vpd', 'watering', 'overwater'])"
                    },
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimum confidence threshold (0.0-1.0)",
                        "default": 0.3
                    }
                },
                "required": ["domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "store_learning",
            "description": "Store a new learning/insight in the Grimoire for future reference. Use when you discover something important that should persist across restarts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": ["trading", "cultivation", "social", "market_regimes"],
                        "description": "Knowledge domain"
                    },
                    "key": {
                        "type": "string",
                        "description": "Unique key for this learning (e.g., 'vpd-sweet-spot-veg')"
                    },
                    "content": {
                        "type": "string",
                        "description": "The learning/insight to store"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "How confident you are (0.0-1.0)",
                        "default": 0.5
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for searchability"
                    }
                },
                "required": ["domain", "key", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_sensors_live",
            "description": "Read LIVE sensor data right now (not cached). Use to verify conditions after making an adjustment (e.g., turned on humidifier → wait → re-read humidity). Returns real-time Govee/Ecowitt/Kasa readings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "wait_seconds": {
                        "type": "integer",
                        "description": "Seconds to wait before reading (for changes to take effect)",
                        "default": 0,
                        "minimum": 0,
                        "maximum": 60
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_grow_history",
            "description": "Get historical grow data: past AI decisions, watering events, sensor trends, growth stage transitions. Use to understand trends and learn from past actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "enum": ["decisions", "watering", "sensors", "stages", "observations"],
                        "description": "Type of historical data to retrieve"
                    },
                    "days": {
                        "type": "integer",
                        "description": "How many days back to look",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max records to return",
                        "default": 20
                    }
                },
                "required": ["data_type"]
            }
        }
    },
    # =========================================================================
    # SYSTEM DOMAIN TOOLS
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Get the full system status: orchestrator health, sensor polling stats, hardware connectivity, social daemon status, trading agent status, API uptime. Use for self-diagnostics.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emit_event",
            "description": "Write an event to the shared event log. All subsystems (grow, social, trading) share this log for cross-domain awareness. Use to broadcast important happenings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": ["grow", "social", "trading", "blockchain", "system"],
                        "description": "Which domain this event belongs to"
                    },
                    "event_type": {
                        "type": "string",
                        "description": "Type of event (e.g., 'milestone', 'alert', 'decision', 'observation')"
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable event description"
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional structured data payload"
                    }
                },
                "required": ["domain", "event_type", "message"]
            }
        }
    },
]


# =============================================================================
# Tool Execution Results
# =============================================================================

@dataclass
class ToolResult:
    """Result of executing a tool"""
    success: bool
    tool_name: str
    message: str
    data: Optional[Dict[str, Any]] = None


# =============================================================================
# Tool Executor
# =============================================================================

class ToolExecutor:
    """
    Executes AI tool calls through the safety layer.

    Maps tool names to actual hardware operations.
    """

    def __init__(self, safe_actuators, camera, repository, govee_sensors=None):
        """
        Args:
            safe_actuators: SafeActuatorHub instance
            camera: CameraHub instance
            repository: GrowRepository instance for logging
            govee_sensors: Optional GoveeSensorHub for humidifier control
        """
        self.actuators = safe_actuators
        self.camera = camera
        self.repo = repository
        self.govee = govee_sensors  # For Govee H7145 humidifier control
        self._action_log: List[Dict[str, Any]] = []

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool call and return the result"""

        executor_map = {
            "water_plant": self._water_plant,
            "control_grow_light": self._control_grow_light,
            "control_exhaust_fan": self._control_exhaust_fan,
            "control_circulation_fan": self._control_circulation_fan,
            "control_heat_mat": self._control_heat_mat,
            "control_humidifier": self._control_humidifier,
            "control_dehumidifier": self._control_dehumidifier,
            "inject_co2": self._inject_co2,
            "take_photo": self._take_photo,
            "log_observation": self._log_observation,
            "create_task": self._create_task,
            "request_human_help": self._request_human_help,
            "queue_email": self._queue_email,
            "update_grow_stage": self._update_grow_stage,
            "query_allium": self._query_allium,
            "web_search": self._web_search,
            "browse_url": self._browse_url,
            "deep_research": self._deep_research,
            "smart_search": self._smart_search,
            "spawn_research": self._spawn_research,
            "discover_agents": self._discover_agents,
            "call_agent": self._call_agent,
            "multi_agent_query": self._multi_agent_query,
            "a2a_outreach": self._a2a_outreach,
            # --- Cross-Domain Tools (Agentic Upgrade) ---
            "post_tweet": self._post_tweet,
            "post_farcaster": self._post_farcaster,
            "send_telegram": self._send_telegram,
            "check_social_metrics": self._check_social_metrics,
            "get_token_metrics": self._get_token_metrics,
            "get_wallet_balance": self._get_wallet_balance,
            "publish_reputation": self._publish_reputation,
            "get_portfolio": self._get_portfolio,
            "get_market_regime": self._get_market_regime,
            "query_grimoire": self._query_grimoire,
            "store_learning": self._store_learning,
            "read_sensors_live": self._read_sensors_live,
            "get_grow_history": self._get_grow_history,
            "get_system_status": self._get_system_status,
            "emit_event": self._emit_event,
        }

        executor = executor_map.get(tool_name)
        if not executor:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                message=f"Unknown tool: {tool_name}"
            )

        try:
            result = await executor(arguments)
            self._action_log.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result.message,
                "success": result.success
            })
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                message=f"Error executing {tool_name}: {str(e)}"
            )

    async def _water_plant(self, args: Dict[str, Any]) -> ToolResult:
        amount_ml = args.get("amount_ml", 100)
        reason = args.get("reason", "")

        success = await self.actuators.water(amount_ml)

        return ToolResult(
            success=success,
            tool_name="water_plant",
            message=f"Dispensed {amount_ml}ml of water. Reason: {reason}",
            data={"amount_ml": amount_ml}
        )

    async def _control_grow_light(self, args: Dict[str, Any]) -> ToolResult:
        state = args.get("state", False)
        reason = args.get("reason", "")

        success = await self.actuators.set_device("grow_light", state)
        state_str = "ON" if state else "OFF"

        return ToolResult(
            success=success,
            tool_name="control_grow_light",
            message=f"Grow light turned {state_str}. Reason: {reason}",
            data={"state": state}
        )

    async def _control_exhaust_fan(self, args: Dict[str, Any]) -> ToolResult:
        state = args.get("state", False)
        reason = args.get("reason", "")

        success = await self.actuators.set_device("exhaust_fan", state)
        state_str = "ON" if state else "OFF"

        return ToolResult(
            success=success,
            tool_name="control_exhaust_fan",
            message=f"Exhaust fan turned {state_str}. Reason: {reason}",
            data={"state": state}
        )

    async def _control_circulation_fan(self, args: Dict[str, Any]) -> ToolResult:
        state = args.get("state", False)
        reason = args.get("reason", "")

        success = await self.actuators.set_device("circulation_fan", state)
        state_str = "ON" if state else "OFF"

        return ToolResult(
            success=success,
            tool_name="control_circulation_fan",
            message=f"Circulation fan turned {state_str}. Reason: {reason}",
            data={"state": state}
        )

    async def _control_heat_mat(self, args: Dict[str, Any]) -> ToolResult:
        state = args.get("state", False)
        reason = args.get("reason", "")

        success = await self.actuators.set_device("heat_mat", state)
        state_str = "ON" if state else "OFF"

        return ToolResult(
            success=success,
            tool_name="control_heat_mat",
            message=f"Heat mat turned {state_str}. Reason: {reason}",
            data={"state": state}
        )

    async def _control_humidifier(self, args: Dict[str, Any]) -> ToolResult:
        state = args.get("state", "on").lower() == "on" if isinstance(args.get("state"), str) else args.get("state", False)
        reason = args.get("reason", "")
        target_humidity = args.get("target_humidity")  # Optional: set target %
        state_str = "ON" if state else "OFF"

        # Try Govee H7145 humidifier first (cloud-controlled)
        if self.govee and hasattr(self.govee, 'has_humidifier') and self.govee.has_humidifier():
            try:
                # Turn on/off
                power_success = await self.govee.set_humidifier_power(state)

                # ALWAYS set target humidity when turning ON to override app state
                # Default to 70% if not specified (good for clone/veg)
                if state and power_success:
                    target = int(target_humidity) if target_humidity else 70
                    await self.govee.set_humidifier_target(target)
                    return ToolResult(
                        success=True,
                        tool_name="control_humidifier",
                        message=f"Govee humidifier turned {state_str}, target {target}%. Reason: {reason}",
                        data={"state": state, "target_humidity": target, "device": "govee_h7145"}
                    )

                return ToolResult(
                    success=power_success,
                    tool_name="control_humidifier",
                    message=f"Govee humidifier turned {state_str}. Reason: {reason}",
                    data={"state": state, "device": "govee_h7145"}
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    tool_name="control_humidifier",
                    message=f"Govee humidifier error: {str(e)}",
                    data={"error": str(e)}
                )

        # Fallback to smart plug control (Kasa/Tapo)
        success = await self.actuators.set_device("humidifier", state)

        return ToolResult(
            success=success,
            tool_name="control_humidifier",
            message=f"Humidifier turned {state_str}. Reason: {reason}",
            data={"state": state}
        )

    async def _control_dehumidifier(self, args: Dict[str, Any]) -> ToolResult:
        state = args.get("state", False)
        reason = args.get("reason", "")

        success = await self.actuators.set_device("dehumidifier", state)
        state_str = "ON" if state else "OFF"

        return ToolResult(
            success=success,
            tool_name="control_dehumidifier",
            message=f"Dehumidifier turned {state_str}. Reason: {reason}",
            data={"state": state}
        )

    async def _inject_co2(self, args: Dict[str, Any]) -> ToolResult:
        duration = args.get("duration_seconds", 60)
        reason = args.get("reason", "")

        success = await self.actuators.inject_co2(duration)

        return ToolResult(
            success=success,
            tool_name="inject_co2",
            message=f"CO2 injected for {duration} seconds. Reason: {reason}",
            data={"duration_seconds": duration}
        )

    async def _take_photo(self, args: Dict[str, Any]) -> ToolResult:
        reason = args.get("reason", "")
        import base64
        import aiohttp

        # Try fetching from local API first (works when MJPEG stream holds camera)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/webcam/latest", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        base64_image = base64.b64encode(image_bytes).decode('utf-8')
                        return ToolResult(
                            success=True,
                            tool_name="take_photo",
                            message=f"Photo captured via API. Reason: {reason}",
                            data={"image_base64": base64_image}
                        )
        except Exception as api_err:
            pass  # Fall through to direct camera capture

        # Fallback to direct camera capture
        try:
            if self.camera is None:
                return ToolResult(
                    success=False,
                    tool_name="take_photo",
                    message="Camera not initialized and API unavailable"
                )

            image_bytes, base64_image = await self.camera.capture_for_analysis()

            if image_bytes is None or base64_image is None:
                return ToolResult(
                    success=False,
                    tool_name="take_photo",
                    message="Camera not available (using mock camera - no real webcam connected)"
                )

            return ToolResult(
                success=True,
                tool_name="take_photo",
                message=f"Photo captured. Reason: {reason}",
                data={"image_base64": base64_image}
            )
        except ConnectionError as e:
            return ToolResult(
                success=False,
                tool_name="take_photo",
                message=f"Webcam connection failed: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name="take_photo",
                message=f"Photo capture failed: {str(e)}"
            )

    async def _log_observation(self, args: Dict[str, Any]) -> ToolResult:
        observation = args.get("observation", "")
        category = args.get("category", "health")

        # Persist to episodic memory via repository
        try:
            from src.db.models import EpisodicMemory
            from src.db.database import get_db_session
            severity_map = {"health": "info", "concern": "warning", "milestone": "info",
                            "growth": "info", "environment": "info"}
            importance_map = {"health": 1.0, "concern": 2.0, "milestone": 2.5,
                              "growth": 1.0, "environment": 1.0}
            severity = severity_map.get(category, "info")
            importance = importance_map.get(category, 1.0)

            formatted = f"[{category.upper()}] ({severity}) {observation}"
            async with get_db_session() as session:
                memory = EpisodicMemory(
                    formatted_text=formatted,
                    importance_score=importance,
                    grow_day=0,
                    time_label=f"OBSERVATION",
                )
                session.add(memory)
                await session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"log_observation DB persist failed: {e}")

        # Write to shared event log so all subsystems can see it
        try:
            from src.core.event_log import log_event
            log_event("grow", "observation", observation, {"category": category})
        except Exception:
            pass

        return ToolResult(
            success=True,
            tool_name="log_observation",
            message=f"Observation logged [{category}]: {observation}",
            data={"observation": observation, "category": category}
        )

    async def _create_task(self, args: Dict[str, Any]) -> ToolResult:
        """Create a task in agent_tasks.json for the engagement daemon."""
        import json
        from pathlib import Path
        from datetime import datetime as dt

        title = args.get("title", "")
        description = args.get("description", "")
        priority = args.get("priority", "medium")
        tool_hint = args.get("tool_hint", "web_research")

        tasks_path = Path(__file__).parent.parent.parent / "data" / "agent_tasks.json"
        try:
            tasks_path.parent.mkdir(parents=True, exist_ok=True)
            existing = []
            if tasks_path.exists():
                existing = json.loads(tasks_path.read_text())
                if not isinstance(existing, list):
                    existing = []

            new_id = max((t.get("id", 0) for t in existing), default=0) + 1
            new_task = {
                "id": new_id,
                "title": title,
                "description": description,
                "priority": priority,
                "status": "pending",
                "created": dt.now().isoformat(),
                "tool_hint": tool_hint,
                "notes": "",
                "source": "grow_brain",
            }
            existing.append(new_task)
            tasks_path.write_text(json.dumps(existing, indent=2))

            # Also log to shared event log
            try:
                from src.core.event_log import log_event
                log_event("grow", "decision", f"Created task: {title}", {"task_id": new_id, "hint": tool_hint})
            except Exception:
                pass

            return ToolResult(
                success=True,
                tool_name="create_task",
                message=f"Task #{new_id} created [{priority}]: {title} (hint: {tool_hint})",
                data={"task_id": new_id}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name="create_task",
                message=f"Failed to create task: {e}"
            )

    async def _request_human_help(self, args: Dict[str, Any]) -> ToolResult:
        task = (args.get("task") or "").strip()
        urgency = (args.get("urgency") or "medium").strip().lower()
        details = (args.get("details") or "").strip()

        if not task:
            return ToolResult(
                success=False,
                tool_name="request_human_help",
                message="Missing required field: task",
                data={"urgency": urgency, "details": details},
            )

        msg = f"HUMAN ACTION REQUIRED ({urgency.upper()}): {task}"
        if details:
            msg += f" | {details}"

        # This tool is intentionally non-hardware: it records intent so downstream
        # systems (notifications, dashboards) can alert the human.
        return ToolResult(
            success=True,
            tool_name="request_human_help",
            message=msg,
            data={"task": task, "urgency": urgency, "details": details},
        )

    async def _queue_email(self, args: Dict[str, Any]) -> ToolResult:
        to = args.get("to", "")
        subject = args.get("subject", "")
        body = args.get("body", "")

        if not to or not subject:
            return ToolResult(
                success=False,
                tool_name="queue_email",
                message="Missing required fields: to, subject"
            )

        try:
            from src.mailer.client import get_email_client
            client = get_email_client()
            success = await client.send(to=to, subject=subject, body_text=body)
            return ToolResult(
                success=success,
                tool_name="queue_email",
                message=f"Email sent to {to}: {subject}" if success else f"Email failed to {to}",
                data={"to": to, "subject": subject}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name="queue_email",
                message=f"Email error: {str(e)}"
            )

    async def _update_grow_stage(self, args: Dict[str, Any]) -> ToolResult:
        new_stage = args.get("new_stage", "")
        reason = args.get("reason", "")

        try:
            from src.db.models import GrowthStage
            stage_enum = GrowthStage(new_stage)

            from src.db.connection import get_db_session
            from src.db.repository import GrowRepository
            async with get_db_session() as session:
                repo = GrowRepository(session)
                transition = await repo.transition_stage(
                    to_stage=stage_enum,
                    triggered_by="ai",
                    reason=reason,
                )
            return ToolResult(
                success=True,
                tool_name="update_grow_stage",
                message=f"Stage transitioned to {new_stage}. Reason: {reason}",
                data={"new_stage": new_stage, "transition_id": transition.id if transition else None}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name="update_grow_stage",
                message=f"Stage transition failed: {str(e)}"
            )

    async def _query_allium(self, args: Dict[str, Any]) -> ToolResult:
        query = args.get("query", "")
        if not query:
            return ToolResult(
                success=False,
                tool_name="query_allium",
                message="Missing required field: query"
            )

        try:
            import os
            import httpx
            api_key = os.environ.get("ALLIUM_API_KEY", "")
            if not api_key:
                return ToolResult(
                    success=False,
                    tool_name="query_allium",
                    message="ALLIUM_API_KEY not configured"
                )

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.allium.so/api/v1/explorer/queries/run",
                    headers={"X-API-Key": api_key},
                    json={"query": query},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rows = data.get("data", [])[:10]  # Limit to 10 rows for context window
                    return ToolResult(
                        success=True,
                        tool_name="query_allium",
                        message=f"Query returned {len(rows)} rows",
                        data={"rows": rows}
                    )
                else:
                    return ToolResult(
                        success=False,
                        tool_name="query_allium",
                        message=f"Allium API error: {resp.status_code} {resp.text[:200]}"
                    )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name="query_allium",
                message=f"Allium query error: {str(e)}"
            )

    async def _web_search(self, args: Dict[str, Any]) -> ToolResult:
        query = args.get("query", "")
        if not query:
            return ToolResult(success=False, tool_name="web_search", message="Missing query")
        try:
            from src.tools.web_search import get_web_search
            ws = get_web_search()
            max_results = args.get("max_results", 5)
            results = await ws.search(query, max_results=max_results)
            # Format for context window
            formatted = []
            for r in results:
                formatted.append(f"- {r['title']}: {r['body'][:200]} ({r['url']})")
            return ToolResult(
                success=True,
                tool_name="web_search",
                message=f"Found {len(results)} results for '{query}':\n" + "\n".join(formatted),
                data={"results": results}
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="web_search", message=f"Search error: {e}")

    async def _browse_url(self, args: Dict[str, Any]) -> ToolResult:
        url = args.get("url", "")
        if not url:
            return ToolResult(success=False, tool_name="browse_url", message="Missing url")
        try:
            from src.tools.web_search import get_web_search
            ws = get_web_search()
            max_chars = args.get("max_chars", 5000)
            text = await ws.browse(url, max_chars=max_chars)
            if not text:
                return ToolResult(success=False, tool_name="browse_url", message=f"Could not extract content from {url}")
            return ToolResult(
                success=True,
                tool_name="browse_url",
                message=f"Content from {url} ({len(text)} chars):\n{text[:5000]}",
                data={"content": text, "url": url}
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="browse_url", message=f"Browse error: {e}")

    async def _deep_research(self, args: Dict[str, Any]) -> ToolResult:
        question = args.get("question", "")
        if not question:
            return ToolResult(success=False, tool_name="deep_research", message="Missing question")
        try:
            from src.tools.web_search import get_web_search
            ws = get_web_search()
            max_sources = args.get("max_sources", 3)
            result = await ws.deep_research(question, max_sources=max_sources)
            findings = result.get("findings", [])
            actions = result.get("action_items", [])
            summary = f"Research on '{question}':\n"
            summary += "Findings:\n" + "\n".join(f"  - {f}" for f in findings) + "\n"
            summary += "Action items:\n" + "\n".join(f"  - {a}" for a in actions)
            return ToolResult(
                success=True,
                tool_name="deep_research",
                message=summary,
                data=result
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="deep_research", message=f"Research error: {e}")

    async def _smart_search(self, args: Dict[str, Any]) -> ToolResult:
        question = args.get("question", "")
        if not question:
            return ToolResult(success=False, tool_name="smart_search", message="Missing question")
        try:
            from src.tools.web_search import get_web_search
            ws = get_web_search()
            answer = await ws.smart_search(question)
            if not answer:
                return ToolResult(success=False, tool_name="smart_search", message="No answer found")
            return ToolResult(
                success=True,
                tool_name="smart_search",
                message=f"Answer: {answer[:4000]}",
                data={"answer": answer}
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="smart_search", message=f"Search error: {e}")

    async def _spawn_research(self, args: Dict[str, Any]) -> ToolResult:
        tasks = args.get("tasks", [])
        if not tasks:
            return ToolResult(success=False, tool_name="spawn_research", message="Missing tasks list")
        try:
            from src.tools.subagent import get_subagent_executor
            executor = get_subagent_executor()
            batch = []
            for t in tasks[:5]:  # Cap at 5 parallel
                batch.append({
                    "task": t.get("task", ""),
                    "type": t.get("type", "research"),
                    "context": t.get("context", ""),
                })
            results = await executor.run_batch(batch)
            summaries = []
            for r in results:
                status = r.status
                findings = r.findings[:3] if r.findings else []
                actions = r.action_items[:3] if r.action_items else []
                summaries.append(f"[{r.task_id}] {r.task[:60]} — {status}\n"
                                 f"  Findings: {findings}\n  Actions: {actions}")
            completed = sum(1 for r in results if r.status == "completed")
            return ToolResult(
                success=True,
                tool_name="spawn_research",
                message=f"Spawned {len(results)} subagents ({completed} succeeded):\n" + "\n".join(summaries),
                data={"results": [r.to_dict() for r in results]}
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="spawn_research", message=f"Subagent error: {e}")

    # --- A2A Tool Handlers ---

    async def _discover_agents(self, args: Dict[str, Any]) -> ToolResult:
        """Discover agents from 8004scan registry."""
        try:
            from src.a2a.registry import get_registry
            registry = get_registry()
            agents = await registry.search(
                chain=args.get("chain", "monad"),
                skills=args.get("skills"),
                tags=args.get("tags"),
                has_a2a=args.get("has_a2a", True),
                min_trust=args.get("min_trust", 0),
            )
            if not agents:
                return ToolResult(success=True, tool_name="discover_agents", message="No agents found matching criteria")

            summaries = []
            for a in agents[:10]:
                summaries.append(
                    f"  #{a.agent_id} {a.name} (trust={a.trust_score:.0f}) "
                    f"skills={a.skills[:3]} url={a.a2a_url or 'none'}"
                )
            return ToolResult(
                success=True,
                tool_name="discover_agents",
                message=f"Found {len(agents)} agents:\n" + "\n".join(summaries),
                data={"agents": [{"id": a.agent_id, "name": a.name, "url": a.a2a_url, "skills": a.skills, "trust": a.trust_score} for a in agents[:10]]},
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="discover_agents", message=f"Registry error: {e}")

    async def _call_agent(self, args: Dict[str, Any]) -> ToolResult:
        """Call another agent via A2A protocol."""
        agent_url = args.get("agent_url", "")
        skill = args.get("skill", "")
        message = args.get("message", "")
        if not agent_url or not skill:
            return ToolResult(success=False, tool_name="call_agent", message="Missing agent_url or skill")
        try:
            from src.a2a.orchestrator import get_orchestrator
            orch = get_orchestrator()
            resp = await orch.call_one(agent_url, skill, message)
            if resp.success:
                return ToolResult(
                    success=True,
                    tool_name="call_agent",
                    message=f"Agent '{resp.agent_name}' responded ({resp.latency_ms:.0f}ms): {str(resp.data)[:500]}",
                    data=resp.data,
                )
            else:
                return ToolResult(success=False, tool_name="call_agent", message=f"Agent call failed: {resp.error}")
        except Exception as e:
            return ToolResult(success=False, tool_name="call_agent", message=f"A2A error: {e}")

    async def _multi_agent_query(self, args: Dict[str, Any]) -> ToolResult:
        """Fan-out query to multiple agents."""
        skill = args.get("skill", "")
        message = args.get("message", "")
        if not skill or not message:
            return ToolResult(success=False, tool_name="multi_agent_query", message="Missing skill or message")
        try:
            from src.a2a.orchestrator import get_orchestrator
            orch = get_orchestrator()
            result = await orch.fan_out(
                skill=skill,
                message=message,
                chain=args.get("chain", "monad"),
                max_agents=min(args.get("max_agents", 5), 10),
                min_trust=args.get("min_trust", 50),
            )
            agent_summaries = [
                f"  {r.agent_name}: {'OK' if r.success else 'FAIL'} ({r.latency_ms:.0f}ms)"
                for r in result.responses
            ]
            return ToolResult(
                success=True,
                tool_name="multi_agent_query",
                message=(
                    f"Queried {result.agent_count} agents, {result.success_count} responded "
                    f"({result.total_latency_ms:.0f}ms total):\n" + "\n".join(agent_summaries)
                ),
                data={
                    "success_rate": result.success_rate,
                    "responses": result.all_data(),
                    "consensus": result.consensus,
                },
            )
        except Exception as e:
            return ToolResult(success=False, tool_name="multi_agent_query", message=f"Orchestration error: {e}")

    async def _a2a_outreach(self, args: Dict[str, Any]) -> ToolResult:
        """Trigger a manual A2A outreach round via the outbound daemon."""
        try:
            from src.a2a.outbound_daemon import get_outbound_daemon
            daemon = get_outbound_daemon()

            # Override max_agents if provided
            max_agents = min(args.get("max_agents", 3), 5)
            original_max = None
            if max_agents != 3:
                # Temporarily patch the module-level constant for this round
                import src.a2a.outbound_daemon as _mod
                original_max = _mod.MAX_AGENTS_PER_ROUND
                _mod.MAX_AGENTS_PER_ROUND = max_agents

            results = await daemon.run_outreach_round()

            if original_max is not None:
                _mod.MAX_AGENTS_PER_ROUND = original_max

            if not results:
                return ToolResult(
                    success=True,
                    tool_name="a2a_outreach",
                    message="A2A outreach round completed but no viable agents found to call.",
                    data={"agents_called": 0},
                )

            summaries = []
            for r in results:
                status = "OK" if r.get("success") else "FAIL"
                name = r.get("agent_name", "Unknown")
                latency = r.get("latency_ms", 0)
                error = r.get("error", "")
                line = f"  {name}: {status} ({latency:.0f}ms)"
                if error:
                    line += f" - {str(error)[:100]}"
                summaries.append(line)

            succeeded = sum(1 for r in results if r.get("success"))
            stats = daemon.get_stats()

            return ToolResult(
                success=True,
                tool_name="a2a_outreach",
                message=(
                    f"A2A outreach round: {succeeded}/{len(results)} agents responded:\n"
                    + "\n".join(summaries)
                    + f"\n\nDaemon stats: {stats['total_calls']} total calls, "
                    f"{stats['agents_tracked']} agents tracked, "
                    f"{stats['calls_last_hour']} calls in last hour"
                ),
                data={
                    "agents_called": len(results),
                    "agents_responded": succeeded,
                    "results": results,
                    "daemon_stats": stats,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name="a2a_outreach",
                message=f"A2A outreach error: {e}",
            )

    # =========================================================================
    # CROSS-DOMAIN TOOL HANDLERS (Agentic Upgrade)
    # =========================================================================

    # --- Social ---

    async def _post_tweet(self, args: Dict[str, Any]) -> ToolResult:
        """Post a tweet via the social module."""
        text = args.get("text", "")
        if not text:
            return ToolResult(success=False, tool_name="post_tweet", message="Missing tweet text")
        if len(text) > 280:
            return ToolResult(success=False, tool_name="post_tweet",
                              message=f"Tweet too long ({len(text)} chars, max 280)")
        # Enforce rules: no hashtags, no leaf emoji
        if '#' in text:
            return ToolResult(success=False, tool_name="post_tweet",
                              message="BLOCKED: No hashtags allowed per brand rules")
        if '🌿' in text:
            return ToolResult(success=False, tool_name="post_tweet",
                              message="BLOCKED: No leaf emoji (🌿) per brand rules")
        try:
            from src.social.twitter import get_twitter_client
            twitter = get_twitter_client()
            include_photo = args.get("include_photo", False)
            image_data = None
            if include_photo:
                try:
                    import httpx as _httpx
                    async with _httpx.AsyncClient() as client:
                        resp = await client.get("http://localhost:8000/api/webcam/latest", timeout=10.0)
                        if resp.status_code == 200 and len(resp.content) > 1000:
                            image_data = resp.content
                except Exception:
                    pass  # Post without image

            if image_data:
                result = await twitter.tweet_with_image(text=text, image_data=image_data,
                                                       alt_text="Mon the cannabis plant")
            else:
                result = await twitter.tweet(text)

            if result.success:
                return ToolResult(success=True, tool_name="post_tweet",
                                  message=f"Tweet posted: {text[:100]}...",
                                  data={"tweet_id": result.tweet_id})
            else:
                return ToolResult(success=False, tool_name="post_tweet",
                                  message=f"Tweet failed: {result.error}")
        except Exception as e:
            return ToolResult(success=False, tool_name="post_tweet", message=f"Twitter error: {e}")

    async def _post_farcaster(self, args: Dict[str, Any]) -> ToolResult:
        """Post a cast to Farcaster."""
        text = args.get("text", "")
        if not text:
            return ToolResult(success=False, tool_name="post_farcaster", message="Missing cast text")
        try:
            from src.social.farcaster import get_farcaster_client
            fc = get_farcaster_client()
            channel = args.get("channel")
            result = await fc.post_cast(text, channel=channel)
            return ToolResult(success=True, tool_name="post_farcaster",
                              message=f"Cast posted to {'/' + channel if channel else 'home'}: {text[:100]}...",
                              data={"cast_hash": result.get("hash", "")})
        except Exception as e:
            return ToolResult(success=False, tool_name="post_farcaster", message=f"Farcaster error: {e}")

    async def _send_telegram(self, args: Dict[str, Any]) -> ToolResult:
        """Send a message to the Telegram community group."""
        message = args.get("message", "")
        if not message:
            return ToolResult(success=False, tool_name="send_telegram", message="Missing message")
        try:
            import os as _os
            import httpx as _httpx
            bot_token = _os.getenv("TELEGRAM_COMMUNITY_BOT_TOKEN", "")
            chat_id = _os.getenv("TELEGRAM_COMMUNITY_CHAT_ID", "")
            if not bot_token or not chat_id:
                return ToolResult(success=False, tool_name="send_telegram",
                                  message="Telegram bot not configured")
            async with _httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    return ToolResult(success=True, tool_name="send_telegram",
                                      message=f"Telegram message sent: {message[:100]}...")
                else:
                    return ToolResult(success=False, tool_name="send_telegram",
                                      message=f"Telegram API error: {resp.status_code}")
        except Exception as e:
            return ToolResult(success=False, tool_name="send_telegram", message=f"Telegram error: {e}")

    async def _check_social_metrics(self, args: Dict[str, Any]) -> ToolResult:
        """Get engagement metrics across all social platforms."""
        try:
            from src.social.engagement_daemon import get_engagement_daemon
            daemon = get_engagement_daemon()
            metrics = daemon.get_engagement_metrics()
            return ToolResult(success=True, tool_name="check_social_metrics",
                              message=f"Social metrics: {metrics.get('total_posts', 0)} posts, "
                                      f"{metrics.get('total_engagements', 0)} engagements in 24h",
                              data=metrics)
        except Exception as e:
            return ToolResult(success=False, tool_name="check_social_metrics",
                              message=f"Metrics error: {e}")

    # --- Blockchain ---

    async def _get_token_metrics(self, args: Dict[str, Any]) -> ToolResult:
        """Get $MON token metrics from DexScreener."""
        try:
            from src.blockchain.monad import create_lfj_client
            client = create_lfj_client()
            force = args.get("force_refresh", False)
            metrics = await client.get_token_metrics(force_refresh=force)
            return ToolResult(success=True, tool_name="get_token_metrics",
                              message=f"$MON: ${metrics.price_usd:.6f} | "
                                      f"MCap: ${metrics.market_cap:,.0f} | "
                                      f"24h Vol: ${metrics.volume_24h:,.0f} | "
                                      f"Holders: {metrics.holders}",
                              data=metrics.to_dict())
        except Exception as e:
            return ToolResult(success=False, tool_name="get_token_metrics",
                              message=f"Token metrics error: {e}")

    async def _get_wallet_balance(self, args: Dict[str, Any]) -> ToolResult:
        """Check wallet balance on Monad."""
        try:
            import os as _os
            from src.blockchain.monad import MonadClient
            client = MonadClient()
            address = args.get("address", _os.getenv("AGENT_WALLET_ADDRESS", ""))
            if not address:
                return ToolResult(success=False, tool_name="get_wallet_balance",
                                  message="No wallet address configured")
            balance = await client.get_balance(address)
            return ToolResult(success=True, tool_name="get_wallet_balance",
                              message=f"Wallet {address[:8]}...{address[-6:]}: {balance} MON",
                              data={"address": address, "balance_mon": balance})
        except Exception as e:
            return ToolResult(success=False, tool_name="get_wallet_balance",
                              message=f"Balance check error: {e}")

    async def _publish_reputation(self, args: Dict[str, Any]) -> ToolResult:
        """Trigger on-chain reputation publish cycle."""
        reason = args.get("reason", "agent-initiated")
        try:
            from src.blockchain.reputation_publisher import run_publish_cycle
            results = await asyncio.get_event_loop().run_in_executor(None, run_publish_cycle)
            if results:
                tx_count = len(results)
                return ToolResult(success=True, tool_name="publish_reputation",
                                  message=f"Published {tx_count} reputation signals on-chain. Reason: {reason}",
                                  data={"signals": results})
            else:
                return ToolResult(success=True, tool_name="publish_reputation",
                                  message="Reputation publish completed (no signals to publish)")
        except Exception as e:
            return ToolResult(success=False, tool_name="publish_reputation",
                              message=f"Reputation publish error: {e}")

    # --- Trading ---

    async def _get_portfolio(self, args: Dict[str, Any]) -> ToolResult:
        """Read the trading agent's portfolio from disk."""
        try:
            import json as _json
            from pathlib import Path
            portfolio_path = Path("agents/ganjamon/data/paper_portfolio.json")
            if not portfolio_path.exists():
                return ToolResult(success=True, tool_name="get_portfolio",
                                  message="No trading portfolio found (agent may not be running)",
                                  data={"status": "not_found"})
            data = _json.loads(portfolio_path.read_text())
            cash = data.get("current_cash", 0)
            starting = data.get("starting_balance", 0)
            trades = data.get("trades", [])
            pnl = cash - starting
            return ToolResult(success=True, tool_name="get_portfolio",
                              message=f"Portfolio: ${cash:.2f} cash (started ${starting:.2f}, "
                                      f"P&L: ${pnl:+.2f}, {len(trades)} trades)",
                              data={"cash": cash, "starting": starting, "pnl": pnl,
                                    "trade_count": len(trades),
                                    "recent_trades": trades[-5:] if trades else []})
        except Exception as e:
            return ToolResult(success=False, tool_name="get_portfolio",
                              message=f"Portfolio read error: {e}")

    async def _get_market_regime(self, args: Dict[str, Any]) -> ToolResult:
        """Get market regime and strategy tracker status."""
        try:
            from src.learning.strategy_tracker import get_strategy_tracker
            tracker = get_strategy_tracker()
            status = tracker.get_status()
            goals = tracker.get_goal_progress()
            stalled = tracker.get_stalled_goals()
            return ToolResult(success=True, tool_name="get_market_regime",
                              message=f"Strategies: {status.get('active_count', 0)} active, "
                                      f"{status.get('disabled_count', 0)} disabled | "
                                      f"Stalled goals: {len(stalled)}",
                              data={"strategies": status, "goals": [g.__dict__ if hasattr(g, '__dict__') else g for g in goals],
                                    "stalled": stalled})
        except Exception as e:
            return ToolResult(success=False, tool_name="get_market_regime",
                              message=f"Market regime error: {e}")

    # --- Memory / Learning ---

    async def _query_grimoire(self, args: Dict[str, Any]) -> ToolResult:
        """Search the Grimoire knowledge store."""
        try:
            from src.learning.grimoire import get_grimoire, get_all_grimoire_context
            domain = args.get("domain", "all")
            tags = args.get("tags")
            min_conf = args.get("min_confidence", 0.3)

            if domain == "all":
                context = get_all_grimoire_context(min_confidence=min_conf)
                return ToolResult(success=True, tool_name="query_grimoire",
                                  message=f"Grimoire context ({len(context)} chars):\n{context[:3000]}",
                                  data={"context": context})
            else:
                g = get_grimoire(domain)
                entries = g.search(tags=tags, min_confidence=min_conf)
                formatted = []
                for e in entries[:20]:
                    formatted.append(f"[{e.confidence:.0%}] {e.key}: {e.content}")
                result_text = "\n".join(formatted) if formatted else "No entries found"
                return ToolResult(success=True, tool_name="query_grimoire",
                                  message=f"Grimoire/{domain} ({len(entries)} entries):\n{result_text}",
                                  data={"entries": [{"key": e.key, "content": e.content,
                                                      "confidence": e.confidence} for e in entries[:20]]})
        except Exception as e:
            return ToolResult(success=False, tool_name="query_grimoire",
                              message=f"Grimoire error: {e}")

    async def _store_learning(self, args: Dict[str, Any]) -> ToolResult:
        """Store a new learning in the Grimoire."""
        try:
            from src.learning.grimoire import get_grimoire, save_all_grimoires
            domain = args.get("domain", "cultivation")
            key = args.get("key", "")
            content = args.get("content", "")
            if not key or not content:
                return ToolResult(success=False, tool_name="store_learning",
                                  message="Missing key or content")
            confidence = args.get("confidence", 0.5)
            tags = args.get("tags", [])

            g = get_grimoire(domain)
            entry = g.add(key=key, content=content, confidence=confidence,
                          source="agentic_brain", tags=tags)
            save_all_grimoires()

            return ToolResult(success=True, tool_name="store_learning",
                              message=f"Learning stored in {domain}/{key} "
                                      f"(confidence: {entry.confidence:.0%}, "
                                      f"evidence: {entry.evidence_count})",
                              data={"domain": domain, "key": key, "confidence": entry.confidence})
        except Exception as e:
            return ToolResult(success=False, tool_name="store_learning",
                              message=f"Store learning error: {e}")

    async def _read_sensors_live(self, args: Dict[str, Any]) -> ToolResult:
        """Read LIVE sensor data (not cached)."""
        wait_seconds = min(args.get("wait_seconds", 0), 60)
        if wait_seconds > 0:
            import asyncio as _asyncio
            await _asyncio.sleep(wait_seconds)

        try:
            from src.db.connection import get_db_session
            from src.db.repository import GrowRepository
            async with get_db_session() as session:
                repo = GrowRepository(session)
                sensors = await repo.get_sensors_latest()
                devices = await repo.get_devices_latest()

            if not sensors:
                return ToolResult(success=False, tool_name="read_sensors_live",
                                  message="No sensor data available")

            return ToolResult(success=True, tool_name="read_sensors_live",
                              message=f"Live sensors: Temp={sensors.get('air_temp', 'N/A')}°C, "
                                      f"RH={sensors.get('humidity', 'N/A')}%, "
                                      f"VPD={sensors.get('vpd', 'N/A')} kPa, "
                                      f"CO2={sensors.get('co2', 'N/A')} ppm, "
                                      f"Soil={sensors.get('soil_moisture', 'N/A')}%",
                              data={"sensors": sensors, "devices": devices or {}})
        except Exception as e:
            return ToolResult(success=False, tool_name="read_sensors_live",
                              message=f"Live sensor read error: {e}")

    async def _get_grow_history(self, args: Dict[str, Any]) -> ToolResult:
        """Get historical grow data."""
        data_type = args.get("data_type", "decisions")
        days = min(args.get("days", 7), 30)
        limit = min(args.get("limit", 20), 50)

        try:
            from src.db.connection import get_db_session
            from src.db.repository import GrowRepository
            async with get_db_session() as session:
                repo = GrowRepository(session)

                if data_type == "decisions":
                    history = await repo.get_ai_history(limit=limit)
                    return ToolResult(success=True, tool_name="get_grow_history",
                                      message=f"Last {len(history)} AI decisions",
                                      data={"decisions": history})
                elif data_type == "watering":
                    # Use daily stats for watering info
                    session_obj = await repo.get_active_session()
                    if session_obj:
                        stats = await repo.get_daily_stats(session_obj.current_day)
                        return ToolResult(success=True, tool_name="get_grow_history",
                                          message=f"Today's stats: {stats}",
                                          data={"daily_stats": stats})
                    return ToolResult(success=True, tool_name="get_grow_history",
                                      message="No active session",
                                      data={})
                elif data_type == "sensors":
                    history = await repo.get_sensors_history(hours=days * 24)
                    return ToolResult(success=True, tool_name="get_grow_history",
                                      message=f"Sensor history: {len(history)} records",
                                      data={"sensors": history})
                elif data_type == "observations":
                    memories = await repo.get_recent_memories(limit=limit)
                    return ToolResult(success=True, tool_name="get_grow_history",
                                      message=f"Last {len(memories)} observations/memories",
                                      data={"observations": memories})
                elif data_type == "stages":
                    stage_data = await repo.get_current_stage()
                    return ToolResult(success=True, tool_name="get_grow_history",
                                      message=f"Current stage: {stage_data}",
                                      data={"stage": stage_data})
                else:
                    return ToolResult(success=False, tool_name="get_grow_history",
                                      message=f"Unknown data_type: {data_type}")
        except Exception as e:
            return ToolResult(success=False, tool_name="get_grow_history",
                              message=f"History error: {e}")

    # --- System ---

    async def _get_system_status(self, args: Dict[str, Any]) -> ToolResult:
        """Get full system status for self-diagnostics."""
        try:
            import os as _os
            from src.core.watchdog import get_watchdog
            wdog = get_watchdog()
            status = wdog.get_status()

            # Add additional system info
            status["python_pid"] = _os.getpid()
            status["uptime_seconds"] = status.get("uptime_seconds", 0)

            return ToolResult(success=True, tool_name="get_system_status",
                              message=f"System status: {len(status.get('components', {}))} components tracked",
                              data=status)
        except Exception as e:
            # Fallback minimal status
            import os as _os
            return ToolResult(success=True, tool_name="get_system_status",
                              message=f"System running (PID {_os.getpid()}), watchdog unavailable: {e}",
                              data={"pid": _os.getpid(), "watchdog_error": str(e)})

    async def _emit_event(self, args: Dict[str, Any]) -> ToolResult:
        """Write an event to the shared event log."""
        domain = args.get("domain", "system")
        event_type = args.get("event_type", "info")
        message = args.get("message", "")
        data = args.get("data", {})

        if not message:
            return ToolResult(success=False, tool_name="emit_event", message="Missing event message")

        try:
            from src.core.event_log import log_event
            log_event(domain, event_type, message, data)
            return ToolResult(success=True, tool_name="emit_event",
                              message=f"Event logged [{domain}/{event_type}]: {message}")
        except Exception as e:
            return ToolResult(success=False, tool_name="emit_event",
                              message=f"Event log error: {e}")

    # =========================================================================
    # ACTION LOG
    # =========================================================================

    def get_action_log(self) -> List[Dict[str, Any]]:
        """Get log of all actions taken"""
        return self._action_log.copy()

    def clear_action_log(self) -> None:
        """Clear action log"""
        self._action_log = []
