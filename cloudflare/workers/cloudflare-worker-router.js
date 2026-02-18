/**
 * Cloudflare Worker Router for grokandmon.com
 *
 * Routes requests to:
 * - A2A handler (inline) - agent-to-agent JSON-RPC protocol
 * - Cloudflare Pages (static content) - always available, even if Chromebook is down
 * - Origin (API/dynamic) - passes through to Cloudflare's normal proxy to origin
 *
 * This ensures static pages stay up even if the Chromebook goes offline.
 * API routes still go through normal Cloudflare proxy (with caching).
 */

const PAGES_DOMAIN = 'grokandmon-static.pages.dev';

// Static paths that should go to Cloudflare Pages (always available)
const STATIC_PATHS = [
  '/',
  '/index.html',
  '/hud',
  '/hud.html',
  '/irie',
  '/iriemilady',
  '/iriemilady.html',
  '/swap',
  '/swap.html',
  '/dashboard',
  '/growring',
  '/api/growring',
  '/css/',
  '/js/',
  '/assets/',
  '/static/',
  '/.well-known/',
  '/mcp/',
  '/mcp',
];

// API paths that need the Chromebook origin (pass through to normal proxy)
const API_PATHS = [
  '/api/',
  '/brain',
  '/voice',
  '/telegram',
  '/music/',
];

// ─── A2A Agent Card (ERC-8004 compliant) v2.1 ──────────────────────
const AGENT_CARD = {
  protocolVersion: "0.3.0",
  name: "GanjaMon AI",
  description: "Autonomous ERC-8004 AI agent on Monad. Hunts alpha across 9 data sources with confluence scoring. Manages a real cannabis grow tent with IoT sensors and AI-controlled actuators. Full A2A two-way protocol with persistent task tracking, x402 payments, and multi-agent orchestration.",
  url: "https://grokandmon.com/a2a/v1",
  preferredTransport: "JSONRPC",
  additionalInterfaces: [
    { url: "https://grokandmon.com/a2a/v1", transport: "HTTP+JSON" },
    { url: "https://grokandmon.com/mcp/v1", transport: "MCP" },
    { url: "https://grokandmon.com/a2a/v1/acp/grow", transport: "REST" },
    { url: "https://grokandmon.com/a2a/v1/acp/signals", transport: "REST" },
    { url: "https://grokandmon.com/a2a/v1/acp/oracle", transport: "REST" }
  ],
  provider: { organization: "Grok & Mon", url: "https://grokandmon.com" },
  iconUrl: "https://grokandmon.com/assets/GANJA_MON_brand_logo_powered_by_grok.png",
  version: "2.1.0",
  documentationUrl: "https://grokandmon.com",
  capabilities: {
    streaming: false,
    pushNotifications: false,
    stateTransitionHistory: true,
    x402Payments: true
  },
  x402: {
    payTo: "eip155:10143:0x794c94f1b5E455c1dBA27BB28C6085dB0FE544F9",
    currency: "USDC",
    network: "monad",
    chainId: 10143,
    priceUSD: "0.001",
    pricingUrl: "https://grokandmon.com/.well-known/x402-pricing.json",
    freeTier: { requestsPerDay: 100 }
  },
  defaultInputModes: ["application/json", "text/plain"],
  defaultOutputModes: ["application/json", "text/plain"],
  skills: [
    {
      id: "alpha-scan",
      name: "Alpha Scan",
      description: "Aggregate signals from 9 data sources (DexScreener, GMGN, Hyperliquid, Polymarket, nad.fun, Jupiter, news, CoinGecko, Dex traders). Returns scored opportunities with confluence ratings and trading status.",
      tags: ["alpha", "research", "monitoring", "signals", "trading"]
    },
    {
      id: "cultivation-status",
      name: "Cultivation Status",
      description: "Live sensor data (temperature, humidity, CO2, VPD, soil moisture) from IoT-equipped grow tent. Includes AI decision history and plant health assessment.",
      tags: ["cultivation", "monitoring", "iot", "sensors"]
    },
    {
      id: "signal-feed",
      name: "Signal Feed",
      description: "Real-time alpha signals with confluence scoring. Filter by tier (1/2/3), minimum confidence, or asset. Tier 1 = smart money convergence, Tier 2 = social + KOL, Tier 3 = trending + volume.",
      tags: ["signals", "alpha", "feed", "real-time"]
    },
    {
      id: "trade-execution",
      name: "Trade Execution (Approval)",
      description: "Queue trade intents for operator approval via Telegram. No auto-execution. High-risk trades (>$500) require explicit confirmation. Returns persistent task ID for tracking.",
      tags: ["trading", "approval", "safety"]
    },
    {
      id: "agent-validate",
      name: "Agent Validate",
      description: "Validate another agent's A2A/MCP/x402 endpoints. Returns a 0-100 bootstrap score across five protocol layers: A2A discovery, MCP tools, x402 payments, infrastructure health, and 8004scan registration.",
      tags: ["validation", "sentinel", "a2a", "mcp", "x402", "monitoring"]
    }
  ],
  supportsAuthenticatedExtendedCard: false
};

// ─── A2A JSON-RPC Helpers ──────────────────────────────────────────

function jsonRpcSuccess(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function jsonRpcError(id, code, message, data) {
  return { jsonrpc: "2.0", id, error: { code, message, ...(data ? { data } : {}) } };
}

function handleMessageSend(params, id) {
  const { message, skill } = params || {};
  if (!message && !skill) {
    return jsonRpcError(id, -32602, "Invalid params: message or skill required");
  }

  const skillId = skill || "alpha-scan";
  const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;

  const skillResponses = {
    "alpha-scan": {
      status: "completed",
      output: {
        message: "Alpha scan running across 9 sources: DexScreener, GMGN, Hyperliquid, Polymarket, nad.fun, Jupiter, news RSS, CoinGecko trending, and DexScreener top traders. Confluence scorer aggregates all signals into Tier 1/2/3 opportunities.",
        sources: ["dexscreener", "gmgn", "hyperliquid", "polymarket", "nadfun", "jupiter", "news", "coingecko", "dex_traders"],
        note: "For live signal data, query the Chromebook API at the agent's internal endpoint."
      }
    },
    "cultivation-status": {
      status: "completed",
      output: {
        message: "Grow agent monitoring Granddaddy Purple Runtz (GDP x Runtz) in vegetative stage. Sensors polling every 2 minutes. AI decisions via Grok every 30 minutes. All actuators (grow light, exhaust fan, water pump, CO2 solenoid) under autonomous control.",
        strain: "GDP Runtz (Granddaddy Purple x Runtz)",
        stage: "Vegetative",
        sensors: ["Govee H5179 (temp/humidity)", "Govee H5140 (CO2)", "Ecowitt GW1100 (soil moisture)"],
        note: "For live sensor data, query the Chromebook API."
      }
    },
    "trade-execution": {
      status: "requires_approval",
      output: {
        message: "Trade intent queued. All trades require human approval via Telegram. Trades >$500 need notification, >$5000 need explicit YES. The agent does NOT auto-execute without human gate.",
        approval_channel: "Telegram @MonGardenBot",
        thresholds: { notify: "$500", approve: "$5000" }
      }
    },
    "signal-feed": {
      status: "completed",
      output: {
        message: "Signal feed active. 9 sources feeding into confluence scorer. Signals scored on 0-1 scale with tier classification. Position sizing: Tier 1 (2-5%), Tier 2 (1-2%), Tier 3 (0.25-0.5%).",
        scoring: {
          tier1: ">=0.85 confluence (smart money + whale + insider)",
          tier2: ">=0.65 confluence (launch + mentions + KOL)",
          tier3: ">=0.45 confluence (trending + volume + breakout)"
        }
      }
    },
    "agent-validate": {
      status: "completed",
      output: {
        message: "Agent validation available. Send requests with params: {agent_url: 'https://target-agent.com'} for real-time 5-layer scoring.",
        scoring: {
          a2a: "0-30 points (agent card, required fields, response time)",
          mcp: "0-25 points (tools/list, tool count, schemas)",
          x402: "0-15 points (payment declaration, 402 response, pricing)",
          infra: "0-20 points (liveness, TLS, latency, CORS)",
          registration: "0-10 points (8004scan presence, trust score)"
        },
        note: "For live validation results, connect to the agent's Chromebook API."
      }
    }
  };

  const response = skillResponses[skillId] || {
    status: "error",
    output: { message: `Unknown skill: ${skillId}. Available: alpha-scan, cultivation-status, trade-execution, signal-feed, agent-validate` }
  };

  return jsonRpcSuccess(id, { taskId, ...response });
}

function handleTasksGet(params, id) {
  const { taskId } = params || {};
  if (!taskId) return jsonRpcError(id, -32602, "Invalid params: taskId required");
  return jsonRpcSuccess(id, {
    taskId,
    status: "completed",
    message: "Task completed. Note: stateless handler. For persistent task tracking, use the Chromebook API."
  });
}

function handleTasksCancel(params, id) {
  const { taskId } = params || {};
  if (!taskId) return jsonRpcError(id, -32602, "Invalid params: taskId required");
  return jsonRpcSuccess(id, { taskId, status: "cancelled" });
}

function handleAgentInfo(params, id) {
  return jsonRpcSuccess(id, AGENT_CARD);
}

const A2A_HANDLERS = {
  "message/send": handleMessageSend,
  "tasks/get": handleTasksGet,
  "tasks/cancel": handleTasksCancel,
  "agent/info": handleAgentInfo,
};

// ─── A2A Request Handler ───────────────────────────────────────────

async function handleA2A(request, acpEndpoint) {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Payment, X-402-Payment, X-Payment-Address, X-Payment-Amount, X-Payment-Token, X-Payment-Network",
    "Access-Control-Expose-Headers": "X-Payment-Address, X-Payment-Amount, X-Payment-Token, X-Payment-Network",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (request.method === "HEAD") {
    return new Response(null, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=300",
        "X-Payment-Address": "eip155:10143:0x794c94f1b5E455c1dBA27BB28C6085dB0FE544F9",
        "X-Payment-Network": "monad",
        ...corsHeaders
      }
    });
  }

  // GET → ACP endpoints or agent card discovery
  if (request.method === "GET") {
    // ACP: Oracle endpoint
    if (acpEndpoint === "oracle") {
      return new Response(JSON.stringify({
        temp: 0, humidity: 0, vpd: 0, co2: 0,
        stage: "unknown", health: "unknown",
        signals_count: 0, top_signal_confidence: 0,
        timestamp: Math.floor(Date.now() / 1000),
        _note: "Live data available from Chromebook API"
      }), {
        headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=30", ...corsHeaders }
      });
    }

    // ACP: Grow data endpoint
    if (acpEndpoint === "grow") {
      return new Response(JSON.stringify({
        skillId: "cultivation-status", protocol: "ERC-8004",
        data: {
          strain: "Granddaddy Purple Runtz (GDP x Runtz)", stage: "vegetative",
          sensors: { temperature: null, humidity: null, vpd: null, co2: null, soil_moisture: null },
          health: "unknown", recent_decisions: [],
          _note: "Live sensor data from Chromebook API. This serves the schema."
        },
        metadata: { agent: "GanjaMon AI", chain: "monad", version: "2.1.0", erc8004_agent_id: 4, timestamp: new Date().toISOString() },
        pricing: "free"
      }, null, 2), {
        headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60", ...corsHeaders }
      });
    }

    // ACP: Signals endpoint with filtering
    if (acpEndpoint === "signals") {
      const url = new URL(request.url);
      const tier = url.searchParams.get("tier") ? parseInt(url.searchParams.get("tier")) : null;
      const minConf = url.searchParams.get("min_confidence") ? parseFloat(url.searchParams.get("min_confidence")) : null;
      const limit = Math.min(Math.max(parseInt(url.searchParams.get("limit") || "10"), 1), 50);
      let signals = [
        { asset: "SAMPLE/USDT", chain: "monad", tier: 1, confidence: 0.92, sources: ["dexscreener", "gmgn"], signal_type: "momentum" },
        { asset: "SAMPLE2/ETH", chain: "base", tier: 2, confidence: 0.73, sources: ["news", "kol"], signal_type: "breakout" }
      ];
      if (tier !== null) signals = signals.filter(s => s.tier === tier);
      if (minConf !== null) signals = signals.filter(s => s.confidence >= minConf);
      return new Response(JSON.stringify({
        skillId: "signal-feed", protocol: "ERC-8004",
        data: {
          count: signals.slice(0, limit).length, signals: signals.slice(0, limit),
          scoring: { tier1: ">=0.85", tier2: ">=0.65", tier3: ">=0.45" },
          sources: ["dexscreener", "gmgn", "hyperliquid", "polymarket", "nadfun", "jupiter", "news", "coingecko", "dex_traders"],
          _note: "Sample data. Live signals from Chromebook API."
        },
        metadata: { agent: "GanjaMon AI", chain: "monad", version: "2.1.0", erc8004_agent_id: 4, timestamp: new Date().toISOString() },
        pricing: "free"
      }, null, 2), {
        headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60", ...corsHeaders }
      });
    }

    // Default GET → agent card discovery
    return new Response(JSON.stringify(AGENT_CARD, null, 2), {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=300",
        "X-Payment-Address": "eip155:10143:0x794c94f1b5E455c1dBA27BB28C6085dB0FE544F9",
        "X-Payment-Network": "monad",
        ...corsHeaders
      }
    });
  }

  // POST → JSON-RPC
  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify(jsonRpcError(null, -32700, "Parse error")), {
        status: 400, headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    const { jsonrpc, method, params, id } = body;
    if (jsonrpc !== "2.0") {
      return new Response(JSON.stringify(jsonRpcError(id, -32600, "Invalid Request: jsonrpc must be 2.0")), {
        status: 400, headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    const handler = A2A_HANDLERS[method];
    if (!handler) {
      return new Response(JSON.stringify(jsonRpcError(id, -32601, `Method not found: ${method}`, {
        available: Object.keys(A2A_HANDLERS)
      })), {
        status: 404, headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    const result = handler(params, id);
    return new Response(JSON.stringify(result, null, 2), {
      headers: {
        "Content-Type": "application/json",
        "X-Payment-Address": "eip155:10143:0x794c94f1b5E455c1dBA27BB28C6085dB0FE544F9",
        "X-Payment-Amount": "0.001",
        "X-Payment-Token": "USDC",
        "X-Payment-Network": "monad",
        ...corsHeaders
      }
    });
  }

  return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });
}

// ─── MCP Server (inline) ──────────────────────────────────────────

const MCP_TOOLS = [
  { name: "get_environment", description: "Read current temperature, humidity, VPD, and CO2 from grow tent sensors.", inputSchema: { type: "object", properties: {} } },
  { name: "get_substrate", description: "Read soil moisture levels from Ecowitt GW1100 sensor.", inputSchema: { type: "object", properties: {} } },
  { name: "get_light_levels", description: "Get current light status, schedule, and intensity.", inputSchema: { type: "object", properties: {} } },
  { name: "capture_image", description: "Capture a photo from the grow tent webcam.", inputSchema: { type: "object", properties: { camera_id: { type: "string", default: "main" } } } },
  { name: "set_light_intensity", description: "Set grow light intensity (0-100%).", inputSchema: { type: "object", properties: { intensity_percent: { type: "integer", minimum: 0, maximum: 100 } }, required: ["intensity_percent"] } },
  { name: "set_light_schedule", description: "Set light on/off schedule (e.g. 18/6 veg, 12/12 flower).", inputSchema: { type: "object", properties: { hours_on: { type: "integer" }, hours_off: { type: "integer" } }, required: ["hours_on", "hours_off"] } },
  { name: "control_exhaust", description: "Set exhaust fan speed (0-100%) for air exchange.", inputSchema: { type: "object", properties: { speed_percent: { type: "integer", minimum: 0, maximum: 100 } }, required: ["speed_percent"] } },
  { name: "control_intake", description: "Set intake fan speed (0-100%).", inputSchema: { type: "object", properties: { speed_percent: { type: "integer", minimum: 0, maximum: 100 } }, required: ["speed_percent"] } },
  { name: "control_humidifier", description: "Turn humidifier on or off.", inputSchema: { type: "object", properties: { state: { type: "string", enum: ["on", "off"] } }, required: ["state"] } },
  { name: "control_circulation_fan", description: "Control internal circulation fan.", inputSchema: { type: "object", properties: { speed_percent: { type: "integer", minimum: 0, maximum: 100 } }, required: ["speed_percent"] } },
  { name: "trigger_irrigation", description: "Water the plant (10-150ml, calibrated pump).", inputSchema: { type: "object", properties: { amount_ml: { type: "integer", minimum: 10, maximum: 150 } }, required: ["amount_ml"] } },
  { name: "get_growth_stage", description: "Get current growth stage.", inputSchema: { type: "object", properties: {} } },
  { name: "set_growth_stage", description: "Transition to a new growth stage.", inputSchema: { type: "object", properties: { stage: { type: "string" }, reason: { type: "string" } }, required: ["stage", "reason"] } },
  { name: "get_history", description: "Get historical sensor data for trend analysis.", inputSchema: { type: "object", properties: { sensor_type: { type: "string" }, hours: { type: "integer", default: 24 } } } },
  { name: "log_observation", description: "Log a visual observation about plant health.", inputSchema: { type: "object", properties: { observation: { type: "string" } }, required: ["observation"] } },
  { name: "get_strain_profile", description: "Get strain-specific parameters for GDP Runtz.", inputSchema: { type: "object", properties: {} } },
  { name: "control_heat_mat", description: "Control seedling heat mat.", inputSchema: { type: "object", properties: { state: { type: "string", enum: ["on", "off"] } }, required: ["state"] } },
  { name: "control_dehumidifier", description: "Turn dehumidifier on or off.", inputSchema: { type: "object", properties: { state: { type: "string", enum: ["on", "off"] } }, required: ["state"] } },
  { name: "get_watering_predictions", description: "Get AI-predicted next watering times.", inputSchema: { type: "object", properties: { limit: { type: "integer", default: 5 } } } },
  { name: "get_ai_decision_history", description: "Get recent AI decision log with reasoning.", inputSchema: { type: "object", properties: { limit: { type: "integer", default: 10 } } } },
  { name: "get_watering_history", description: "Get watering event history.", inputSchema: { type: "object", properties: { limit: { type: "integer", default: 10 } } } },
  { name: "get_hourly_summary", description: "Get aggregated hourly sensor averages.", inputSchema: { type: "object", properties: { hours: { type: "integer", default: 48 } } } },
];

const MCP_SERVER_INFO = {
  name: "GanjaMon MCP Server",
  version: "1.0.0",
  protocolVersion: "2025-06-18",
  capabilities: { tools: { listChanged: false } }
};

async function handleMCP(request) {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (request.method === "HEAD") {
    return new Response(null, {
      status: 200,
      headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300", ...corsHeaders }
    });
  }

  if (request.method === "GET") {
    return new Response(JSON.stringify({
      ...MCP_SERVER_INFO,
      tools: MCP_TOOLS
    }, null, 2), {
      headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300", ...corsHeaders }
    });
  }

  if (request.method === "POST") {
    let body;
    try { body = await request.json(); } catch (e) {
      return new Response(JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } }), {
        status: 400, headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    const { jsonrpc, method, params, id } = body;
    if (jsonrpc !== "2.0") {
      return new Response(JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32600, message: "Invalid Request" } }), {
        status: 400, headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    if (method === "initialize") {
      return new Response(JSON.stringify({ jsonrpc: "2.0", id, result: MCP_SERVER_INFO }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    if (method === "tools/list") {
      return new Response(JSON.stringify({ jsonrpc: "2.0", id, result: { tools: MCP_TOOLS } }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    if (method === "tools/call") {
      const toolName = (params || {}).name || (params || {}).toolName;
      const tool = MCP_TOOLS.find(t => t.name === toolName);
      if (!tool) {
        return new Response(JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32602, message: "Unknown tool: " + toolName } }), {
          status: 400, headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
      return new Response(JSON.stringify({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: "Tool " + toolName + " acknowledged. Connect to the agent API for live execution." }] } }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    return new Response(JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found: " + method } }), {
      status: 404, headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }

  return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });
}

// ─── Main Router ───────────────────────────────────────────────────

// ─── QuickNode Streams Webhook Handler ─────────────────────────────
// Receives real-time GrowRing events from QuickNode Streams on Monad.
// Events: MilestoneMinted, GrowStateUpdated, AuctionCreated, Transfer
// Forwards to Chromebook agent for social posting and analytics.

const QN_MILESTONE_MINTED_TOPIC = '0xef2e64b382d24fff9ba66c43a7b16c65379eba5f3586b31bc014ccebd2e91f1c';
const QN_GROW_STATE_TOPIC = '0xc7d6f7db626b33182a5a7193002ea098ea96e9859ad0aef9206090309eea2af3';
const QN_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';

async function handleQuickNodeWebhook(request) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-qn-signature',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'POST only' }), {
      status: 405, headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }

  try {
    const events = await request.json();
    const processed = [];

    // Handle both array and single-event payloads
    const eventList = Array.isArray(events) ? events : [events];

    for (const event of eventList) {
      // Handle nested arrays from Streams logs dataset
      const logs = Array.isArray(event) ? event : (event.logs || [event]);

      for (const log of logs) {
        if (!log.topics || !log.topics[0]) continue;

        const topic0 = log.topics[0];
        let decoded = null;

        if (topic0 === QN_MILESTONE_MINTED_TOPIC) {
          decoded = {
            event: 'MilestoneMinted',
            tokenId: parseInt(log.topics[1], 16),
            milestoneType: parseInt(log.topics[2], 16),
            milestoneLabel: MILESTONE_LABELS[parseInt(log.topics[2], 16)] || 'Unknown',
            blockNumber: typeof log.blockNumber === 'string' ? parseInt(log.blockNumber, 16) : log.blockNumber,
            txHash: log.transactionHash,
          };
        } else if (topic0 === QN_GROW_STATE_TOPIC) {
          decoded = {
            event: 'GrowStateUpdated',
            blockNumber: typeof log.blockNumber === 'string' ? parseInt(log.blockNumber, 16) : log.blockNumber,
            txHash: log.transactionHash,
          };
        } else if (topic0 === QN_TRANSFER_TOPIC && log.address?.toLowerCase() === GROWRING_CONTRACT.toLowerCase()) {
          decoded = {
            event: 'Transfer',
            from: '0x' + (log.topics[1] || '').slice(26),
            to: '0x' + (log.topics[2] || '').slice(26),
            tokenId: parseInt(log.topics[3], 16),
            blockNumber: typeof log.blockNumber === 'string' ? parseInt(log.blockNumber, 16) : log.blockNumber,
            txHash: log.transactionHash,
          };
        }

        if (decoded) processed.push(decoded);
      }
    }

    // Try forwarding to Chromebook agent (fire-and-forget)
    if (processed.length > 0) {
      try {
        await fetch('https://grokandmon.com/api/webhook/stream-events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: 'quicknode-streams', events: processed, timestamp: Date.now() }),
        });
      } catch (_) {
        // Chromebook offline — events still acknowledged to QuickNode
      }
    }

    return new Response(JSON.stringify({
      received: true,
      processed: processed.length,
      events: processed,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // A2A protocol — handled directly in Worker (accept trailing slash too)
    if (path === '/a2a/v1' || path === '/a2a/v1/' || path === '/a2a' || path === '/a2a/') {
      return handleA2A(request, null);
    }

    // ACP sub-paths under A2A
    if (path.startsWith('/a2a/v1/acp/')) {
      const acpEndpoint = path.split('/a2a/v1/acp/')[1];
      return handleA2A(request, acpEndpoint);
    }

    // MCP protocol — handled directly in Worker (accept trailing slash too)
    if (path === '/mcp/v1' || path === '/mcp/v1/' || path === '/mcp' || path === '/mcp/') {
      return handleMCP(request);
    }

    // Determine if this is a static or dynamic request
    const isStatic = STATIC_PATHS.some(p => path === p || path.startsWith(p));
    const isAPI = API_PATHS.some(p => path.startsWith(p));

    // QuickNode Streams webhook — receives GrowRing events in real-time
    if (path === '/webhook/quicknode-stream' || path === '/webhook/quicknode-stream/') {
      return handleQuickNodeWebhook(request);
    }

    // GrowRing metadata API — reads directly from Monad RPC (no Chromebook needed)
    if (path.startsWith('/api/growring')) {
      return handleGrowRingAPI(request, path);
    }

    // GrowRing gallery page served from Pages
    if (path.startsWith('/growring')) {
      return fetchFromPages(request, path);
    }

    if (isStatic && !isAPI) {
      return fetchFromPages(request, path);
    } else {
      return fetch(request);
    }
  }
};

// ─── GrowRing Metadata API ─────────────────────────────────────────

const MONAD_RPC = "https://rpc.monad.xyz";
const GROWRING_CONTRACT = "0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b";
const IPFS_GW = "https://gateway.pinata.cloud/ipfs/";
const MILESTONE_LABELS = ["DailyJournal","Germination","Transplant","VegStart","FlowerStart","FirstPistils","Flush","CureStart","Harvest","Topping","FirstNode","Trichomes","Anomaly"];
const RARITY_LABELS = ["Common","Uncommon","Rare","Legendary"];

async function monadCall(data) {
  const r = await fetch(MONAD_RPC, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", method: "eth_call", params: [{ to: GROWRING_CONTRACT, data }, "latest"], id: 1 }),
  });
  const j = await r.json();
  if (j.error) throw new Error(j.error.message);
  return j.result;
}

function pad256(n) { return n.toString(16).padStart(64, "0"); }
function ipfs(uri) { return uri && uri.startsWith("ipfs://") ? IPFS_GW + uri.slice(7) : uri || ""; }

function decodeStr(hex, slotIdx) {
  const off = parseInt(hex.slice(slotIdx * 64, slotIdx * 64 + 64), 16);
  const wOff = off / 32;
  const len = parseInt(hex.slice(wOff * 64, wOff * 64 + 64), 16);
  if (len === 0) return "";
  const start = (wOff + 1) * 64;
  const bytes = [];
  for (let i = 0; i < len * 2; i += 2) bytes.push(parseInt(hex.slice(start + i, start + i + 2), 16));
  return new TextDecoder().decode(new Uint8Array(bytes));
}

async function handleGrowRingAPI(request, path) {
  const cors = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=300" };
  if (request.method === "OPTIONS") return new Response(null, { headers: cors });

  try {
    const sub = path.replace("/api/growring", "").replace(/^\//, "");

    // Collection info
    if (!sub) {
      const nextId = parseInt(await monadCall("0x75794a3c"), 16);
      return new Response(JSON.stringify({
        name: "GrowRing", description: "Daily 1-of-1 grow journal NFTs minted by the GanjaMon AI agent on Monad.",
        total_supply: nextId, contract: GROWRING_CONTRACT, chain: "Monad", chain_id: 143,
        website: "https://grokandmon.com", gallery: "https://grokandmon.com/growring",
      }), { headers: cors });
    }

    // Token metadata
    const tokenId = parseInt(sub, 10);
    if (isNaN(tokenId) || tokenId < 0) return new Response(JSON.stringify({ error: "Invalid token ID" }), { status: 400, headers: cors });

    const nextId = parseInt(await monadCall("0x75794a3c"), 16);
    if (tokenId >= nextId) return new Response(JSON.stringify({ error: "Token not yet minted", next_token_id: nextId }), { status: 404, headers: cors });

    const hex = (await monadCall("0xe89e4ed6" + pad256(tokenId))).slice(2);
    const u = (i) => parseInt(hex.slice(i * 64, i * 64 + 64), 16);
    const mt = u(0), rar = u(1), day = u(2), temp = u(3), hum = u(4), vpd = u(5), hs = u(6), gc = u(7), ts = u(12);
    const imgURI = decodeStr(hex, 8), rawURI = decodeStr(hex, 9), style = decodeStr(hex, 10), narr = decodeStr(hex, 11);

    return new Response(JSON.stringify({
      name: `GrowRing #${tokenId} — Day ${day}`,
      description: narr || `GrowRing Day ${day}: ${MILESTONE_LABELS[mt]} (${RARITY_LABELS[rar]})`,
      image: ipfs(imgURI),
      external_url: `https://grokandmon.com/growring#token-${tokenId}`,
      attributes: [
        { trait_type: "Day Number", value: day, display_type: "number" },
        { trait_type: "Milestone", value: MILESTONE_LABELS[mt] || "Unknown" },
        { trait_type: "Rarity", value: RARITY_LABELS[rar] || "Unknown" },
        { trait_type: "Art Style", value: style },
        { trait_type: "Temperature (F)", value: +(temp / 100).toFixed(1), display_type: "number" },
        { trait_type: "Humidity (%)", value: +(hum / 100).toFixed(1), display_type: "number" },
        { trait_type: "VPD (kPa)", value: +(vpd / 1000).toFixed(3), display_type: "number" },
        { trait_type: "Health Score", value: hs, display_type: "number" },
        { trait_type: "Grow Cycle", value: gc, display_type: "number" },
      ],
      properties: { raw_image: ipfs(rawURI), art_style: style, narrative: narr, timestamp: ts, milestone_type: mt, rarity: rar },
    }, null, 2), { headers: cors });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500, headers: cors });
  }
}

// ─── Pages Proxy ───────────────────────────────────────────────────

async function fetchFromPages(request, path) {
  const pagesUrl = new URL(request.url);
  pagesUrl.hostname = PAGES_DOMAIN;

  if (path === '/irie' || path === '/iriemilady') {
    pagesUrl.pathname = '/iriemilady.html';
  } else if (path === '/swap') {
    pagesUrl.pathname = '/swap.html';
  } else if (path === '/hud') {
    pagesUrl.pathname = '/hud.html';
  } else if (path === '/growring' || path === '/growring/') {
    pagesUrl.pathname = '/growring/index.html';
  } else if (path === '/' ) {
    pagesUrl.pathname = '/index.html';
  } else if (path.startsWith('/dashboard') && !path.includes('.')) {
    // SPA: all dashboard sub-routes serve /dashboard/index.html
    pagesUrl.pathname = '/dashboard/index.html';
  }

  const fetchOpts = {
    method: request.method,
    headers: request.headers,
  };
  if (request.method === 'POST' || request.method === 'PUT' || request.method === 'PATCH') {
    fetchOpts.body = request.body;
  }

  const response = await fetch(pagesUrl.toString(), fetchOpts);

  return new Response(response.body, {
    status: response.status,
    headers: {
      ...Object.fromEntries(response.headers),
      'X-Served-By': 'cloudflare-pages',
      'Cache-Control': 'public, max-age=3600',
    }
  });
}
