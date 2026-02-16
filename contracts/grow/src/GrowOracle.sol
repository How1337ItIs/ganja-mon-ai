// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title GrowOracle — Continuous Grow State On-Chain
/// @notice Stores the latest grow environment state on Monad.
///         Updated every cycle (~30 min) by the autonomous agent.
///         History is kept in a ring buffer for verifiable grow records.
/// @author GanjaMon AI Agent
contract GrowOracle {
    address public immutable agent;

    struct GrowState {
        uint16 temperature;     // scaled ×100 (7250 = 72.50°F)
        uint16 humidity;        // scaled ×100 (6520 = 65.20%)
        uint16 vpd;             // scaled ×1000 (1050 = 1.050 kPa)
        uint16 co2;             // ppm (0-5000)
        uint16 soilMoisture;    // scaled ×100 (4500 = 45.00%)
        uint8  growthStage;     // 0=Seedling, 1=Veg, 2=Flower, 3=Harvest, 4=Cure
        uint8  healthScore;     // 0-100 (AI assessment from Grok)
        bool   lightOn;         // grow light status
        bytes8 mood;            // ASCII: "irie", "watchful", "blessed", etc.
        string trigger;         // what caused this update
        uint48 timestamp;       // block.timestamp (compact)
    }

    GrowState public current;
    GrowState[] public history;
    uint256 public historyIndex;
    uint256 public constant MAX_HISTORY = 4320; // ~90 days at 30-min cycles

    event GrowStateUpdated(
        uint16 temperature,
        uint16 humidity,
        uint16 vpd,
        uint8  healthScore,
        uint8  growthStage,
        bytes8 mood
    );

    modifier onlyAgent() {
        require(msg.sender == agent, "not agent");
        _;
    }

    constructor() {
        agent = msg.sender;
    }

    function recordState(
        uint16 _temp,
        uint16 _humidity,
        uint16 _vpd,
        uint16 _co2,
        uint16 _soilMoisture,
        uint8  _growthStage,
        uint8  _healthScore,
        bool   _lightOn,
        bytes8 _mood,
        string calldata _trigger
    ) external onlyAgent {
        GrowState memory state = GrowState({
            temperature:  _temp,
            humidity:     _humidity,
            vpd:          _vpd,
            co2:          _co2,
            soilMoisture: _soilMoisture,
            growthStage:  _growthStage,
            healthScore:  _healthScore,
            lightOn:      _lightOn,
            mood:         _mood,
            trigger:      _trigger,
            timestamp:    uint48(block.timestamp)
        });

        current = state;

        // Ring buffer for history
        if (history.length < MAX_HISTORY) {
            history.push(state);
        } else {
            history[historyIndex % MAX_HISTORY] = state;
        }
        historyIndex++;

        emit GrowStateUpdated(_temp, _humidity, _vpd, _healthScore, _growthStage, _mood);
    }

    function historyLength() external view returns (uint256) {
        return history.length;
    }

    function getHistory(uint256 startIdx, uint256 count) external view returns (GrowState[] memory) {
        uint256 end = startIdx + count;
        if (end > history.length) end = history.length;
        GrowState[] memory result = new GrowState[](end - startIdx);
        for (uint256 i = startIdx; i < end; i++) {
            result[i - startIdx] = history[i];
        }
        return result;
    }
}
