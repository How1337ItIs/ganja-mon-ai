// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/// @title GrowRing — Daily 1-of-1 Grow Journal NFT
/// @notice Each GrowRing is a unique artwork generated daily by the GanjaMon agent,
///         capturing that day's plant state, sensor data, and AI-generated art.
///         Tradeable ERC-721 with ERC-2981 royalties (5%).
/// @author GanjaMon AI Agent
contract GrowRing is ERC721, ERC2981 {
    using Strings for uint256;

    // ─── Types ─────────────────────────────────────────────────────────
    enum MilestoneType {
        DailyJournal,   // 0 — COMMON
        Germination,    // 1 — RARE
        Transplant,     // 2 — RARE
        VegStart,       // 3 — RARE
        FlowerStart,    // 4 — RARE
        FirstPistils,   // 5 — RARE
        Flush,          // 6 — RARE
        CureStart,      // 7 — RARE
        Harvest,        // 8 — LEGENDARY
        Topping,        // 9 — UNCOMMON
        FirstNode,      // 10 — UNCOMMON
        Trichomes,      // 11 — UNCOMMON
        Anomaly         // 12 — UNCOMMON
    }

    enum Rarity {
        Common,     // 0
        Uncommon,   // 1
        Rare,       // 2
        Legendary   // 3
    }

    struct MilestoneData {
        MilestoneType milestoneType;
        Rarity rarity;
        uint16 dayNumber;       // Day in the grow cycle (1-indexed)
        uint16 temperature;     // scaled ×100
        uint16 humidity;        // scaled ×100
        uint16 vpd;             // scaled ×1000
        uint8  healthScore;     // 0-100
        uint8  growCycleId;     // Which grow cycle (0, 1, 2...)
        string imageURI;        // IPFS URI for Nano Banana art
        string rawImageURI;     // IPFS URI for raw webcam photo
        string artStyle;        // "roots_dub", "watercolor_botanical", etc.
        string narrative;       // Rasta-voiced journal entry
        uint48 timestamp;       // minted at
    }

    // ─── State ─────────────────────────────────────────────────────────
    address public immutable agent;
    uint256 public nextTokenId;
    uint8   public currentGrowCycleId;
    string  public baseMetadataURI;

    mapping(uint256 => MilestoneData) public milestones;

    // ─── Events ────────────────────────────────────────────────────────
    event MilestoneMinted(
        uint256 indexed tokenId,
        MilestoneType milestoneType,
        Rarity rarity,
        uint16 dayNumber,
        string imageURI
    );

    event GrowCycleStarted(uint8 cycleId);

    // ─── Modifiers ─────────────────────────────────────────────────────
    modifier onlyAgent() {
        require(msg.sender == agent, "not agent");
        _;
    }

    // ─── Constructor ───────────────────────────────────────────────────
    constructor(string memory _baseMetadataURI) ERC721("GrowRing", "GROW") {
        agent = msg.sender;
        baseMetadataURI = _baseMetadataURI;

        // 5% royalties to the agent wallet
        _setDefaultRoyalty(msg.sender, 500);
    }

    // ─── Core Minting ──────────────────────────────────────────────────

    /// @notice Mint a daily GrowRing NFT. Called once per day by the agent.
    /// @param _type The milestone type for this day
    /// @param _dayNumber Day number in the current grow cycle (1-indexed)
    /// @param _imageURI IPFS URI for the AI-generated artwork
    /// @param _rawImageURI IPFS URI for the raw webcam capture
    /// @param _artStyle Art style name (e.g., "neon_noir")
    /// @param _narrative Rasta-voiced journal entry
    /// @param _temperature Temperature scaled ×100
    /// @param _humidity Humidity scaled ×100
    /// @param _vpd VPD scaled ×1000
    /// @param _healthScore AI health assessment 0-100
    function mintDaily(
        MilestoneType _type,
        uint16 _dayNumber,
        string calldata _imageURI,
        string calldata _rawImageURI,
        string calldata _artStyle,
        string calldata _narrative,
        uint16 _temperature,
        uint16 _humidity,
        uint16 _vpd,
        uint8  _healthScore
    ) external onlyAgent returns (uint256 tokenId) {
        tokenId = nextTokenId++;
        Rarity rarity = _computeRarity(_type);

        milestones[tokenId] = MilestoneData({
            milestoneType: _type,
            rarity:        rarity,
            dayNumber:     _dayNumber,
            temperature:   _temperature,
            humidity:      _humidity,
            vpd:           _vpd,
            healthScore:   _healthScore,
            growCycleId:   currentGrowCycleId,
            imageURI:      _imageURI,
            rawImageURI:   _rawImageURI,
            artStyle:      _artStyle,
            narrative:     _narrative,
            timestamp:     uint48(block.timestamp)
        });

        _safeMint(agent, tokenId);

        emit MilestoneMinted(tokenId, _type, rarity, _dayNumber, _imageURI);
        return tokenId;
    }

    // ─── Grow Cycle Management ─────────────────────────────────────────

    /// @notice Start a new grow cycle. Increments the cycle ID.
    function startNewGrowCycle() external onlyAgent {
        currentGrowCycleId++;
        emit GrowCycleStarted(currentGrowCycleId);
    }

    // ─── Metadata ──────────────────────────────────────────────────────

    /// @notice Returns the metadata URI for a given token.
    ///         Points to grokandmon.com/api/growring/{tokenId} for dynamic metadata.
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        return string(abi.encodePacked(baseMetadataURI, tokenId.toString()));
    }

    /// @notice Update the base metadata URI (for migration).
    function setBaseMetadataURI(string calldata _uri) external onlyAgent {
        baseMetadataURI = _uri;
    }

    // ─── ERC-165 Support ───────────────────────────────────────────────

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    // ─── Internal ──────────────────────────────────────────────────────

    function _computeRarity(MilestoneType _type) internal pure returns (Rarity) {
        if (_type == MilestoneType.Harvest) return Rarity.Legendary;
        if (_type == MilestoneType.DailyJournal) return Rarity.Common;

        // RARE milestones — once per grow
        if (_type == MilestoneType.Germination  ||
            _type == MilestoneType.Transplant   ||
            _type == MilestoneType.VegStart     ||
            _type == MilestoneType.FlowerStart  ||
            _type == MilestoneType.FirstPistils ||
            _type == MilestoneType.Flush        ||
            _type == MilestoneType.CureStart)
        {
            return Rarity.Rare;
        }

        // UNCOMMON milestones
        return Rarity.Uncommon;
    }
}
