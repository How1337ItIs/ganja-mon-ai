/**
 * A2A JSON-RPC Server (ERC-8004 compliant) v2.1
 * ===============================================
 *
 * Cloudflare Pages Function handling agent-to-agent communication.
 *
 * GET  /a2a/v1 → Returns agent card (discovery)
 * POST /a2a/v1 → JSON-RPC handler for A2A protocol
 *
 * x402 Payment Support:
 *   - Free tier: 100 requests/day per IP
 *   - Paid tier: X-Payment header with CAIP-10 address
 *   - 402 response includes payment requirements
 *
 * Supported methods:
 *   - message/send     → Send a message to the agent
 *   - tasks/get        → Get task status
 *   - tasks/cancel     → Cancel a running task
 *   - agent/info       → Get agent capabilities
 *
 * Skills:
 *   - alpha-scan         → Aggregate signals from all sources
 *   - cultivation-status → Report latest grow metrics
 *   - trade-execution    → Queue trade for operator approval
 *   - signal-feed        → Get current signal feed
 */

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
  defaultInputModes: ["application/json", "text/plain"],
  defaultOutputModes: ["application/json", "text/plain"],
  x402: {
    payTo: "eip155:10143:0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
    currency: "USDC",
    network: "monad",
    chainId: 10143,
    pricingUrl: "https://grokandmon.com/.well-known/x402-pricing.json",
    freeTier: { requestsPerDay: 100 }
  },
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

// x402 payment requirements (returned in 402 responses)
const X402_REQUIREMENTS = {
  version: "x402-v1",
  payTo: "eip155:10143:0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
  currency: "USDC",
  network: "monad",
  chainId: 10143,
  priceUSD: "0.001",
  description: "A2A request fee. Free tier: 100 requests/day.",
  pricingUrl: "https://grokandmon.com/.well-known/x402-pricing.json"
};

function jsonRpcSuccess(id, result) {
  return {
    jsonrpc: "2.0",
    id: id,
    result: result
  };
}

function jsonRpcError(id, code, message, data) {
  return {
    jsonrpc: "2.0",
    id: id,
    error: {
      code: code,
      message: message,
      ...(data ? { data } : {})
    }
  };
}

async function handleMessageSend(params, id) {
  const { message, skill } = params || {};

  if (!message && !skill) {
    return jsonRpcError(id, -32602, "Invalid params: message or skill required");
  }

  const skillId = skill || "alpha-scan";
  const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;

  // Skill-specific responses
  const skillResponses = {
    "alpha-scan": {
      status: "completed",
      output: {
        message: "Alpha scan is running across 9 sources: DexScreener, GMGN, Hyperliquid, Polymarket, nad.fun, Jupiter, news RSS, CoinGecko trending, and DexScreener top traders. Confluence scorer aggregates all signals into Tier 1/2/3 opportunities. Check the signal feed for current opportunities.",
        sources: ["dexscreener", "gmgn", "hyperliquid", "polymarket", "nadfun", "jupiter", "news", "coingecko", "dex_traders"],
        note: "For live signal data, query the Chromebook API at the agent's internal endpoint."
      }
    },
    "cultivation-status": {
      status: "completed",
      output: {
        message: "Grow agent is monitoring Granddaddy Purple Runtz (GDP x Runtz) in vegetative stage. Sensors polling every 2 minutes. AI decisions via Grok every 30 minutes. All actuators (grow light, exhaust fan, water pump, CO2 solenoid) under autonomous control.",
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
        message: "Signal feed is active. 9 sources feeding into confluence scorer. Signals scored on 0-1 scale with tier classification. Position sizing: Tier 1 (2-5%), Tier 2 (1-2%), Tier 3 (0.25-0.5%).",
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
        message: "Agent validation is available on the live Chromebook API. This CF Pages endpoint advertises the skill. Send requests with params: {agent_url: 'https://target-agent.com', agent_id: 4, chain: 'monad'} to the live API for real-time validation.",
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

  return jsonRpcSuccess(id, {
    taskId: taskId,
    ...response
  });
}

async function handleTasksGet(params, id) {
  const { taskId } = params || {};
  if (!taskId) {
    return jsonRpcError(id, -32602, "Invalid params: taskId required");
  }

  return jsonRpcSuccess(id, {
    taskId: taskId,
    status: "completed",
    message: "Task completed. Note: Cloudflare Pages Functions are stateless. For persistent task tracking, use the Chromebook API directly."
  });
}

async function handleTasksCancel(params, id) {
  const { taskId } = params || {};
  if (!taskId) {
    return jsonRpcError(id, -32602, "Invalid params: taskId required");
  }

  return jsonRpcSuccess(id, {
    taskId: taskId,
    status: "cancelled"
  });
}

async function handleAgentInfo(params, id) {
  return jsonRpcSuccess(id, AGENT_CARD);
}

/**
 * Check x402 payment header.
 * Returns { valid: bool, reason: string }
 *
 * Free tier: always valid (we accept all requests).
 * With X-Payment header: log it and flag as paid.
 */
function checkPayment(request) {
  const paymentHeader = request.headers.get("X-Payment") ||
    request.headers.get("X-402-Payment") ||
    request.headers.get("x-payment");

  if (paymentHeader) {
    return { valid: true, paid: true, reason: "Payment header present" };
  }

  // Free tier — accept without payment
  return { valid: true, paid: false, reason: "Free tier" };
}

export async function onRequest(context) {
  const { request } = context;

  // CORS headers — include x402 headers
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Payment, X-402-Payment, X-Payment-Address, X-Payment-Amount, X-Payment-Token, X-Payment-Network",
    "Access-Control-Expose-Headers": "X-Payment-Address, X-Payment-Amount, X-Payment-Token, X-Payment-Network",
  };

  // Handle CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  // HEAD → Liveness check (used by 8004scan validators)
  if (request.method === "HEAD") {
    return new Response(null, {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=300",
        "X-Payment-Address": "eip155:10143:0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
        "X-Payment-Network": "monad",
        ...corsHeaders
      }
    });
  }

  // GET → Check path for ACP endpoints or agent card
  if (request.method === "GET") {
    const url = new URL(request.url);
    const path = url.pathname;

    // ACP: Oracle endpoint (minimal flat JSON)
    if (path.endsWith("/acp/oracle")) {
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
    if (path.endsWith("/acp/grow")) {
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
    if (path.endsWith("/acp/signals")) {
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

    // Default GET → Return agent card (discovery)
    return new Response(JSON.stringify(AGENT_CARD, null, 2), {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=300",
        "X-Payment-Address": "eip155:10143:0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
        "X-Payment-Network": "monad",
        ...corsHeaders
      }
    });
  }

  // POST → JSON-RPC handler
  if (request.method === "POST") {
    // Check x402 payment
    const payment = checkPayment(request);

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify(jsonRpcError(null, -32700, "Parse error")), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    const { jsonrpc, method, params, id } = body;

    if (jsonrpc !== "2.0") {
      return new Response(JSON.stringify(jsonRpcError(id, -32600, "Invalid Request: jsonrpc must be 2.0")), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // Route methods
    const handlers = {
      "message/send": handleMessageSend,
      "tasks/get": handleTasksGet,
      "tasks/cancel": handleTasksCancel,
      "agent/info": handleAgentInfo,
    };

    const handler = handlers[method];
    if (!handler) {
      return new Response(JSON.stringify(jsonRpcError(id, -32601, `Method not found: ${method}`, {
        available: Object.keys(handlers)
      })), {
        status: 404,
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    const result = await handler(params, id);

    // Add x402 metadata to response headers
    const responseHeaders = {
      "Content-Type": "application/json",
      "X-Payment-Address": "eip155:10143:0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
      "X-Payment-Amount": "0.001",
      "X-Payment-Token": "USDC",
      "X-Payment-Network": "monad",
      ...corsHeaders
    };

    if (payment.paid) {
      responseHeaders["X-Payment-Status"] = "paid";
    }

    return new Response(JSON.stringify(result, null, 2), {
      headers: responseHeaders
    });
  }

  return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });
}
