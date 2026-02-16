/**
 * MCP Server Endpoint (ERC-8004 compliant)
 * =========================================
 *
 * Cloudflare Pages Function implementing MCP (Model Context Protocol).
 *
 * GET  /mcp/v1 → Returns server info
 * POST /mcp/v1 → JSON-RPC handler for MCP protocol
 *
 * Supported methods:
 *   - tools/list       → List available tools
 *   - tools/call       → Call a tool (returns mock/status response)
 *   - initialize       → Server initialization handshake
 */

const SERVER_INFO = {
  name: "GanjaMon MCP Server",
  version: "1.0.0",
  protocolVersion: "2025-06-18",
  description: "MCP server for GanjaMon autonomous cannabis cultivation and trading agent. Provides 22 tools for environment monitoring, actuator control, grow management, and trading operations.",
  capabilities: {
    tools: { listChanged: false }
  }
};

const TOOLS = [
  {
    name: "get_environment",
    description: "Read current temperature, humidity, VPD, and CO2 from grow tent sensors (Govee H5179, H5140).",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "get_substrate",
    description: "Read soil moisture levels from Ecowitt GW1100 sensor.",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "get_light_levels",
    description: "Get current light status, schedule, and intensity readings.",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "capture_image",
    description: "Capture a photo from the grow tent webcam.",
    inputSchema: {
      type: "object",
      properties: {
        camera_id: { type: "string", description: "Camera identifier", default: "main" }
      }
    }
  },
  {
    name: "set_light_intensity",
    description: "Set grow light intensity (0-100%). 0=OFF, 1-100=ON at dimmer setting.",
    inputSchema: {
      type: "object",
      properties: {
        intensity_percent: { type: "integer", minimum: 0, maximum: 100 }
      },
      required: ["intensity_percent"]
    }
  },
  {
    name: "set_light_schedule",
    description: "Set light on/off schedule. Common: 18/6 (veg), 12/12 (flower), 20/4 (seedling).",
    inputSchema: {
      type: "object",
      properties: {
        hours_on: { type: "integer", minimum: 0, maximum: 24 },
        hours_off: { type: "integer", minimum: 0, maximum: 24 },
        start_hour: { type: "integer", minimum: 0, maximum: 23 }
      },
      required: ["hours_on", "hours_off"]
    }
  },
  {
    name: "control_exhaust",
    description: "Set exhaust fan speed (0-100%). Controls tent air exchange and temperature.",
    inputSchema: {
      type: "object",
      properties: {
        speed_percent: { type: "integer", minimum: 0, maximum: 100 }
      },
      required: ["speed_percent"]
    }
  },
  {
    name: "control_intake",
    description: "Set intake fan speed (0-100%). Works with exhaust for negative pressure.",
    inputSchema: {
      type: "object",
      properties: {
        speed_percent: { type: "integer", minimum: 0, maximum: 100 }
      },
      required: ["speed_percent"]
    }
  },
  {
    name: "control_humidifier",
    description: "Turn humidifier on or off.",
    inputSchema: {
      type: "object",
      properties: {
        state: { type: "string", enum: ["on", "off"] }
      },
      required: ["state"]
    }
  },
  {
    name: "control_circulation_fan",
    description: "Control internal circulation fan for air movement.",
    inputSchema: {
      type: "object",
      properties: {
        speed_percent: { type: "integer", minimum: 0, maximum: 100 }
      },
      required: ["speed_percent"]
    }
  },
  {
    name: "trigger_irrigation",
    description: "Water the plant. Calibrated pump: 32ml/sec, 5s max, 150ml cap per event.",
    inputSchema: {
      type: "object",
      properties: {
        amount_ml: { type: "integer", minimum: 10, maximum: 150 }
      },
      required: ["amount_ml"]
    }
  },
  {
    name: "get_growth_stage",
    description: "Get current growth stage (seedling/clone/veg/transition/flower/late_flower/flush/harvest).",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "set_growth_stage",
    description: "Transition to a new growth stage with reason for the change.",
    inputSchema: {
      type: "object",
      properties: {
        stage: { type: "string" },
        reason: { type: "string" }
      },
      required: ["stage", "reason"]
    }
  },
  {
    name: "get_history",
    description: "Get historical sensor data for trend analysis.",
    inputSchema: {
      type: "object",
      properties: {
        sensor_type: { type: "string" },
        hours: { type: "integer", default: 24 }
      }
    }
  },
  {
    name: "log_observation",
    description: "Log a visual observation about plant health, deficiencies, or growth progress.",
    inputSchema: {
      type: "object",
      properties: {
        observation: { type: "string" },
        category: { type: "string" }
      },
      required: ["observation"]
    }
  },
  {
    name: "get_strain_profile",
    description: "Get strain-specific growing parameters for Granddaddy Purple Runtz.",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "control_heat_mat",
    description: "Control seedling heat mat for root zone temperature.",
    inputSchema: {
      type: "object",
      properties: {
        state: { type: "string", enum: ["on", "off"] }
      },
      required: ["state"]
    }
  },
  {
    name: "control_dehumidifier",
    description: "Turn dehumidifier on or off for humidity control.",
    inputSchema: {
      type: "object",
      properties: {
        state: { type: "string", enum: ["on", "off"] }
      },
      required: ["state"]
    }
  },
  {
    name: "get_watering_predictions",
    description: "Get AI-predicted next watering times based on soil moisture trends.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "integer", default: 5 }
      }
    }
  },
  {
    name: "get_ai_decision_history",
    description: "Get recent AI decision log with actions taken and reasoning.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "integer", default: 10 }
      }
    }
  },
  {
    name: "get_watering_history",
    description: "Get watering event history with amounts and intervals.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "integer", default: 10 }
      }
    }
  },
  {
    name: "get_hourly_summary",
    description: "Get aggregated hourly sensor averages for trend charts.",
    inputSchema: {
      type: "object",
      properties: {
        hours: { type: "integer", default: 48 }
      }
    }
  }
];

function jsonRpcSuccess(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function jsonRpcError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

export async function onRequest(context) {
  const { request } = context;

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  // HEAD → Liveness check (used by 8004scan validators)
  if (request.method === "HEAD") {
    return new Response(null, {
      status: 200,
      headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300", ...corsHeaders }
    });
  }

  // GET → Server info
  if (request.method === "GET") {
    return new Response(JSON.stringify({
      ...SERVER_INFO,
      tools: TOOLS
    }, null, 2), {
      headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300", ...corsHeaders }
    });
  }

  // POST → JSON-RPC
  if (request.method === "POST") {
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

    if (method === "initialize") {
      return new Response(JSON.stringify(jsonRpcSuccess(id, SERVER_INFO)), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    if (method === "tools/list") {
      return new Response(JSON.stringify(jsonRpcSuccess(id, { tools: TOOLS })), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    if (method === "tools/call") {
      const toolName = params?.name || params?.toolName;
      const tool = TOOLS.find(t => t.name === toolName);
      if (!tool) {
        return new Response(JSON.stringify(jsonRpcError(id, -32602, `Unknown tool: ${toolName}. Use tools/list to see available tools.`)), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
      return new Response(JSON.stringify(jsonRpcSuccess(id, {
        content: [{
          type: "text",
          text: `Tool ${toolName} acknowledged. This MCP endpoint advertises capabilities — for live execution, connect to the agent's Chromebook API at the internal network endpoint.`
        }]
      })), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    return new Response(JSON.stringify(jsonRpcError(id, -32601, `Method not found: ${method}`, {
      available: ["initialize", "tools/list", "tools/call"]
    })), {
      status: 404,
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }

  return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });
}
