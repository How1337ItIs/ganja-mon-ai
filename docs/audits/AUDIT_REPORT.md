# Grok & Mon Codebase Audit Report

## Overview
The Grok & Mon system is an AI-driven cannabis cultivation platform designed for autonomous plant management, leveraging xAI's Grok and the Monad blockchain. It represents an evolution of the SOLTOMATO concept, focusing on cannabis-specific environmental controls and integration.

## System Architecture

The system operates on a "Smart Agent, Dumb Hardware" principle, orchestrating various components to achieve autonomous cultivation:

*   **Brain (`src/brain/agent.py`)**: This is the core decision-making unit. It operates in a periodic loop (default 30 minutes) to:
    1.  **Observe**: Collects current environmental data from sensors and captures images from cameras.
    2.  **Think**: Formulates a comprehensive prompt, incorporating sensor data, current images, and "episodic memory" (historical context of past grow cycles), which is then sent to xAI's Grok API.
    3.  **Decide**: Grok processes the prompt and returns recommended actions and commentary.
    4.  **Act**: The agent executes the AI-approved actions (e.g., watering, adjusting lighting, CO2 injection) through hardware abstraction layers.
    5.  **Safeguards**: Critical safety mechanisms, such as the `WateringSafeguard`, are implemented to prevent over-watering by enforcing strict cooldown periods (e.g., 45 minutes between waterings) and daily volume limits based on the plant's growth stage, overriding AI decisions if necessary.
    6.  **Logging & Social**: Decisions and actions are thoroughly logged to JSONL files. The agent can also post updates and insights to social media platforms like X (formerly Twitter) if configured.

*   **API (`src/api/app.py`)**: A central **FastAPI** server that provides the backbone for data exchange and control:
    *   **Endpoints**: Offers various endpoints for frontend consumption, such as retrieving the latest sensor readings (`/api/sensors/latest`), AI decisions (`/api/ai/latest`), and managing authentication.
    *   **Hardware Abstraction**: Designed for resilience, it attempts to initialize with real hardware drivers (`GoveeSensorHub`, `KasaActuatorHub`) but gracefully falls back to mock implementations if real hardware is unavailable or unconfigured, ensuring continuous operation (though potentially with simulated data).
    *   **Real-time Capabilities**: Features a WebSocket endpoint (`/ws/sensors`) to provide real-time sensor updates to connected clients (e.g., a dashboard frontend).

*   **Hardware Integration**:
    *   **Sensors**: Primarily uses **Govee** devices (H5179 for temperature/humidity, H5140 for CO2) which communicate via their **Cloud API**, necessitating internet connectivity for environmental data. **Ecowitt** sensors provide soil moisture data via a local gateway, offering some local resilience.
    *   **Actuators**: **Kasa** smart plugs are utilized for controlling grow lights, exhaust fans, and irrigation pumps via local Wi-Fi, minimizing cloud dependency for critical actions.
    *   **Vision**: Supports both local **USB webcams** (`ContinuousWebcam` for efficient frame buffering and analysis enhancements) and external **IP cameras**, enabling visual monitoring and AI-driven image analysis for plant health.

*   **Blockchain Integration**:
    *   **Token ($MON)**: The system monitors the $MON token on the Monad blockchain through a `NadFunClient`, which likely integrates with the LFJ Token Mill for market data.
    *   **Bridge**: The `mon-bridge/` directory contains utility scripts (e.g., `check_vaa.sh`) aimed at manually monitoring the status of Wormhole NTT bridge transfers. These scripts serve more as debugging or verification tools rather than automated bridging services.

## Key Findings & Risks

1.  **Cloud Dependency for Critical Sensors**: The primary environmental sensors (Govee) rely on a cloud API for data acquisition. This introduces a single point of failure: an internet outage would prevent the AI from receiving vital temperature and humidity data, potentially hindering optimal decision-making. While there's a fallback to mock data, it doesn't provide real-world insights.
2.  **Cost Management for AI Vision**: The system dynamically selects AI models, using the more expensive `grok-4-vision` when an image is available. If image capture and analysis are frequent, the xAI API costs could escalate quickly.
3.  **Mock Fallback Obscurity**: While robust, the API's graceful fallback to mock hardware can obscure real hardware failures. A dashboard might display "live" but simulated data, potentially leading to misinformed decisions by human operators if the `sensor_source` isn't prominently displayed or if critical alerts for hardware disconnections are not robust.
4.  **Security Practices**: The project correctly uses `.env` files for managing sensitive credentials, which are excluded from version control via `.gitignore`. The FastAPI API includes basic OAuth2 token-based authentication, contributing to endpoint security.
5.  **Manual Bridge Monitoring**: The presence of shell scripts for checking Wormhole VAA status suggests that bridge operations (for the $MON token) might still require manual intervention or verification, indicating a potential area for further automation.

## Component Status

*   **AI Agent (`src/brain/agent.py`)**: 🟢 **Robust**. Features episodic memory, well-defined decision cycles, and essential hard-coded safety mechanisms (e.g., watering limits).
*   **API (`src/api/app.py`)**: 🟢 **Production-ready**. Provides a comprehensive set of endpoints, handles hardware failures gracefully with mock fallbacks, and offers real-time updates via WebSockets.
*   **Blockchain Bridge (`mon-bridge/`)**: 🟡 **Partially Automated**. Contains tools for monitoring, but active bridging and full automation are not explicitly apparent from the audit. Requires manual execution/verification for VAA status.
*   **Hardware Integration**: 🟡 **Mixed Dependency**. Local control for actuators (Kasa) is resilient, but critical sensor data from Govee relies on internet connectivity, posing a risk during network outages.

This report provides a comprehensive overview of the Grok & Mon system's architecture and current state, highlighting both strengths and areas for potential enhancement or deeper scrutiny.
