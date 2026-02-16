# On-Chain Grow State & GrowRing NFT — Design Document

> **Status:** DESIGN PHASE
> **Date:** 2026-02-10
> **Inspired by:** EMOLT's EmotionOracle + EmoodRing (adapted for physical cultivation)

---

## Vision

**GanjaMon is the first agent to put physical cultivation data on-chain permanently.**

EMOLT stores computed emotions in soulbound tokens you can't trade. We store **proof of life** — 
real sensor readings from IoT hardware, AI health assessments from Grok, and **actual webcam photos 
of living plants** pinned to IPFS. And unlike EMOLT's locked-down approach, GrowRings are **fully 
tradeable ERC-721 NFTs** — collectible, liquid, and valuable.

The agent autonomously creates its own art: real photographs of a real plant it's actually growing,
minted on-chain with sensor metadata and Rasta-voiced narratives. Weekly journals, milestone captures,
harvest day rarities — all tradeable. The grow journal lives on the blockchain as a collectible series.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    CHROMEBOOK SERVER                       │
│                                                           │
│  ┌─────────┐   ┌─────────────┐   ┌──────────────────┐   │
│  │ Govee   │   │ Ecowitt     │   │ USB Webcam       │   │
│  │ H5179   │   │ GW1100      │   │ (fswebcam)       │   │
│  │ H5140   │   │             │   │                  │   │
│  └────┬────┘   └──────┬──────┘   └────────┬─────────┘   │
│       │               │                    │              │
│  ┌────▼───────────────▼────────────────────▼──────────┐  │
│  │           GROW ORCHESTRATOR                         │  │
│  │  1. Collect sensor data (every 2 min)               │  │
│  │  2. Capture webcam image                            │  │
│  │  3. AI health assessment (Grok)                     │  │
│  │  4. Pin image to IPFS (Pinata)                      │  │
│  │  5. Write state to GrowOracle contract              │  │
│  │  6. Mint GrowRing NFT (milestones only)             │  │
│  └─────────────────────────────────────────────────────┘  │
│                          │                                 │
└──────────────────────────┼─────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   MONAD     │
                    │  MAINNET    │
                    │             │
                    │ GrowOracle  │ ← latest state (updated per cycle)
                    │ GrowRing    │ ← milestone NFT collection
                    └─────────────┘
```

---

## Smart Contracts

### 1. GrowOracle.sol — Continuous State Recording

Stores the latest grow environment state. Updated every cycle (~30 min).
History is kept on-chain for verifiable grow records.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

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
            history[history.length % MAX_HISTORY] = state;
        }
        
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
```

### 2. GrowRing.sol — Tradeable Milestone NFT Collection

Each token is a permanent record of a grow milestone with a webcam photo.
**Fully tradeable** with 5% royalties (ERC-2981) back to the agent wallet.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC2981} from "@openzeppelin/contracts/token/common/ERC2981.sol";

contract GrowRing is ERC721, ERC2981 {
    address public immutable agent;
    uint256 public nextTokenId;
    
    enum MilestoneType {
        WEEKLY_JOURNAL,   // regular weekly journal entry with photo (COMMON)
        SNAPSHOT,         // periodic snapshot (COMMON)
        GERMINATION,      // seed sprouted (RARE — once per grow)
        TRANSPLANT,       // moved to bigger pot (RARE)
        VEG_START,        // entered vegetative stage (RARE)
        FIRST_NODE,       // first real node development (UNCOMMON)
        TOPPING,          // plant was topped/trained (UNCOMMON)
        FLOWER_START,     // 12/12 flip (RARE — once per grow)
        FIRST_PISTILS,    // first flower sites visible (RARE)
        TRICHOMES,        // trichome development (UNCOMMON)
        FLUSH,            // final flush before harvest (RARE)
        HARVEST,          // chop day (LEGENDARY — once per grow)
        CURE_START,       // curing begins (RARE)
        ANOMALY           // something unusual — pest, deficiency, recovery (UNCOMMON)
    }
    
    // Rarity tiers for marketplace display
    enum Rarity { COMMON, UNCOMMON, RARE, LEGENDARY }
    
    struct MilestoneData {
        MilestoneType milestoneType;
        Rarity        rarity;
        string        imageURI;       // ipfs://Qm... (webcam capture via Pinata)
        string        narrative;      // AI-generated Rasta-voiced description
        uint16        temperature;
        uint16        humidity;
        uint16        vpd;
        uint16        co2;
        uint8         healthScore;
        uint8         growthStage;
        bytes8        mood;
        uint48        timestamp;
    }
    
    mapping(uint256 => MilestoneData) public milestones;
    
    event MilestoneMinted(
        uint256 indexed tokenId,
        MilestoneType milestoneType,
        Rarity rarity,
        string imageURI
    );
    
    modifier onlyAgent() {
        require(msg.sender == agent, "not agent");
        _;
    }
    
    constructor() ERC721("GrowRing", "GROW") {
        agent = msg.sender;
        // 5% royalties on all secondary sales → back to agent wallet
        _setDefaultRoyalty(msg.sender, 500); // 500 basis points = 5%
    }
    
    function mintMilestone(
        MilestoneType _type,
        string calldata _imageURI,
        string calldata _narrative,
        uint16 _temp,
        uint16 _humidity,
        uint16 _vpd,
        uint16 _co2,
        uint8  _healthScore,
        uint8  _growthStage,
        bytes8 _mood
    ) external onlyAgent returns (uint256 tokenId) {
        tokenId = nextTokenId++;
        _mint(agent, tokenId);
        
        Rarity rarity = _computeRarity(_type);
        
        milestones[tokenId] = MilestoneData({
            milestoneType: _type,
            rarity:        rarity,
            imageURI:      _imageURI,
            narrative:     _narrative,
            temperature:   _temp,
            humidity:      _humidity,
            vpd:           _vpd,
            co2:           _co2,
            healthScore:   _healthScore,
            growthStage:   _growthStage,
            mood:          _mood,
            timestamp:     uint48(block.timestamp)
        });
        
        emit MilestoneMinted(tokenId, _type, rarity, _imageURI);
        
        return tokenId;
    }
    
    function _computeRarity(MilestoneType _type) internal pure returns (Rarity) {
        if (_type == MilestoneType.HARVEST) return Rarity.LEGENDARY;
        if (
            _type == MilestoneType.GERMINATION ||
            _type == MilestoneType.FLOWER_START ||
            _type == MilestoneType.FIRST_PISTILS ||
            _type == MilestoneType.FLUSH ||
            _type == MilestoneType.CURE_START ||
            _type == MilestoneType.TRANSPLANT ||
            _type == MilestoneType.VEG_START
        ) return Rarity.RARE;
        if (
            _type == MilestoneType.FIRST_NODE ||
            _type == MilestoneType.TOPPING ||
            _type == MilestoneType.TRICHOMES ||
            _type == MilestoneType.ANOMALY
        ) return Rarity.UNCOMMON;
        return Rarity.COMMON; // WEEKLY_JOURNAL, SNAPSHOT
    }
    
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        return string(abi.encodePacked("https://grokandmon.com/api/growring/", _toString(tokenId)));
    }
    
    // ERC-165: support ERC-721 + ERC-2981
    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
    
    function _toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) { digits++; temp /= 10; }
        bytes memory buffer = new bytes(digits);
        while (value != 0) { digits--; buffer[digits] = bytes1(uint8(48 + value % 10)); value /= 10; }
        return string(buffer);
    }
    
    function totalSupply() external view returns (uint256) {
        return nextTokenId;
    }
}
```

### Rarity Distribution (Per Grow Cycle — ~112 Days)

**One mint per day.** Every single NFT is unique because:
1. The webcam photo is from that specific moment
2. The sensor readings drive generative visual traits
3. AI transforms the raw photo into a different art style each day
4. The narrative is a one-of-one Rasta-voiced journal entry

| Rarity | Milestone Types | Expected Count | How Assigned |
|--------|----------------|----------------|--------------|
| **LEGENDARY** | Harvest | 1 | The final day. One per grow. The grail. |
| **RARE** | Germination, Transplant, Veg Start, Flower Start, First Pistils, Flush, Cure Start | ~7 | Once each, on the day they happen |
| **UNCOMMON** | Topping, First Node, Trichomes, Anomaly | ~5-10 | When milestones or anomalies occur |
| **COMMON** | Daily Journal | ~94-98 | Every other day that isn't a milestone |

**Total per grow cycle: ~112 NFTs** (1 plant, ~16 weeks, 1/day)

### What Makes Each Daily Mint Unique

Every GrowRing is a **composite art piece**, not a raw webcam photo:

```
┌─────────────────────────────────────────────────┐
│                 DAILY MINT PIPELINE               │
│                                                   │
│  1. CAPTURE — Webcam snapshot (raw proof-of-life) │
│       │                                           │
│  2. TRANSFORM — AI art style applied              │
│       │   (rotates daily through 7 styles)        │
│       │                                           │
│  3. OVERLAY — Sensor-driven generative traits     │
│       │   (VPD → color, temp → warmth, etc.)      │
│       │                                           │
│  4. NARRATE — Grok writes Rasta journal entry     │
│       │   (unique story for that day's data)       │
│       │                                           │
│  5. COMPOSE — Final image: photo + art + data     │
│       │                                           │
│  6. MINT — On-chain with all metadata             │
│       │                                           │
│  7. LIST — Auto-listed for sale                   │
│       │                                           │
│  8. PROMOTE — Posted to socials                   │
└─────────────────────────────────────────────────┘
```

### Art Style Rotation (7 Styles, Cycling Weekly)

Each day of the week gets a different AI art treatment applied to the raw webcam photo:

| Day | Style | Description | Vibe |
|-----|-------|-------------|------|
| **Monday** | **Roots Dub** | Deep bass colors, echo/delay visual effects, sound system aesthetic | Dark, heavy, meditative |
| **Tuesday** | **Watercolor Botanical** | Soft watercolor wash, botanical illustration style | Delicate, scientific, beautiful |
| **Wednesday** | **Psychedelic** | Fractal patterns, color saturation boost, kaleidoscope elements | Trippy, vibrant, alive |
| **Thursday** | **Pixel Art** | 16-bit aesthetic, limited palette, retro game feel | Nostalgic, collectible, clean |
| **Friday** | **Dubrealism** | Collage + mixed media, cut-and-paste aesthetic, zine culture | Raw, underground, punk |
| **Saturday** | **Neon Noir** | Dark background, neon-glow plant contours, cyberpunk grow room | Futuristic, moody, electric |
| **Sunday** | **Sacred Geometry** | Mandala patterns emanating from plant, golden ratio overlays | Spiritual, mathematical, ital |

The raw webcam photo is ALWAYS included in metadata as `raw_image` — the art treatment is the 
primary `image`, but collectors can verify the source.

### Sensor-Driven Generative Traits

Each NFT's visual traits are deterministically generated from that day's sensor readings:

| Sensor Reading | Visual Trait | How It Maps |
|---------------|-------------|-------------|
| **VPD** (0.4-1.6 kPa) | Color palette saturation | Low VPD → washed out, perfect VPD → vivid, high VPD → scorched |
| **Temperature** (60-90°F) | Warmth filter | Cool → blue tint, ideal → natural, hot → orange/red shift |
| **Humidity** (30-80%) | Mist/fog density | Low → crispy clear, high → dreamy haze overlay |
| **CO2** (0-2000 ppm) | Particle effects | Low → sparse, high → dense floating particles |
| **Light status** | Time-of-day atmosphere | Light ON → warm golden hour, OFF → cool moonlit blue |
| **Health score** (0-100) | Border treatment | Low → cracked/distressed border, high → clean/glowing border |
| **Growth stage** | Background pattern | Seedling → soil texture, Veg → leaf patterns, Flower → crystal patterns |
| **Mood** | Typography style | "irie" → flowing script, "watchful" → angular, "blessed" → golden |

This means **no two NFTs can ever look the same** — even if the same art style repeats weekly,
the sensor data creates a unique visual fingerprint for that exact moment in time.

### Day Number as Identity

Each NFT is named by its day in the grow:

```
GrowRing #001 — Day 1: Germination (RARE)
GrowRing #002 — Day 2: First Light (COMMON)
GrowRing #003 — Day 3: Roots Down (COMMON)
...
GrowRing #042 — Day 42: First Topping (UNCOMMON)
...
GrowRing #084 — Day 84: First Pistils (RARE)
...
GrowRing #112 — Day 112: HARVEST (LEGENDARY)
```

The **Day Number** becomes a collectible dimension — early days (sprout) and late days (harvest)
are inherently more interesting. Day 1 and the final day are the crown jewels.

### Revenue Model

| Rarity | Listing Type | Price | Count | Est. Revenue |
|--------|-------------|-------|-------|-------------|
| **LEGENDARY** | Dutch Auction | 5→0.5 MON | 1 | ~1-5 MON |
| **RARE** | Dutch Auction | 1→0.1 MON | ~7 | ~0.7-7 MON |
| **UNCOMMON** | Fixed price | 0.2 MON | ~5-10 | ~1-2 MON |
| **COMMON** | Fixed price | 0.05 MON | ~94-98 | ~4.7-4.9 MON |
| **Secondary royalties** | 5% on all resales | — | — | Passive |
| | | | **Total per grow:** | **~7-19 MON + royalties** |

Revenue flows back to agent wallet → profit allocation (60% compound, 25% $MON, 10% $GANJA, 5% burn).

---

## NFT Sales Pipeline: Mint → List → Promote → Sell

The agent handles the ENTIRE sales lifecycle autonomously:

```
Mint GrowRing
     │
     ▼
Pin metadata to IPFS
     │
     ▼
Auto-list on marketplace(s)
  ├── Magic Eden (primary — biggest Monad NFT marketplace)
  └── Custom Dutch Auction contract (fallback / special editions)
     │
     ▼
Social blast across ALL channels
  ├── Twitter/X (@ganjamonai)
  ├── Telegram (group + channel)
  ├── Farcaster
  └── Moltbook
     │
     ▼
Monitor bids / sales
     │
     ▼
Revenue → agent wallet → profit allocation
```

### Marketplace Strategy

#### Primary: Magic Eden (Monad)
- **Why:** Largest NFT marketplace on Monad, automatic collection indexing for EVM chains, established API/SDK
- **SDK:** `@magiceden/magiceden-sdk` (TypeScript) — supports listing, canceling, offers, buying
- **API:** REST endpoints for create orders (list & bid), requires API key
- **Collection:** Auto-indexed under "GrowRing" collection once first NFT minted
- **Royalties:** Magic Eden respects ERC-2981 (our 5%)

#### Backup: Poply (Monad-native)
- **Why:** Native Monad marketplace, artist-focused, supports owner royalties
- **Listing:** Via their web UI initially, API when available

#### Custom: GrowAuction.sol (Dutch Auctions for Special Editions)

For RARE and LEGENDARY milestones, deploy the agent's own Dutch auction contract:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC721} from "@openzeppelin/contracts/token/ERC721/IERC721.sol";

contract GrowAuction {
    address public immutable agent;
    IERC721 public immutable growRing;
    
    struct Auction {
        uint256 tokenId;
        uint128 startPrice;     // starting price in MON (wei)
        uint128 endPrice;       // floor price in MON (wei)
        uint48  startTime;
        uint48  duration;       // in seconds
        bool    active;
    }
    
    mapping(uint256 => Auction) public auctions;
    
    event AuctionCreated(uint256 indexed tokenId, uint128 startPrice, uint128 endPrice, uint48 duration);
    event AuctionSettled(uint256 indexed tokenId, address buyer, uint256 price);
    event AuctionCancelled(uint256 indexed tokenId);
    
    modifier onlyAgent() {
        require(msg.sender == agent, "not agent");
        _;
    }
    
    constructor(address _growRing) {
        agent = msg.sender;
        growRing = IERC721(_growRing);
    }
    
    function createAuction(
        uint256 _tokenId,
        uint128 _startPrice,
        uint128 _endPrice,
        uint48  _duration        // e.g., 86400 = 24 hours
    ) external onlyAgent {
        require(_startPrice > _endPrice, "start must exceed end");
        require(!auctions[_tokenId].active, "already active");
        
        // Transfer NFT to auction contract
        growRing.transferFrom(agent, address(this), _tokenId);
        
        auctions[_tokenId] = Auction({
            tokenId:    _tokenId,
            startPrice: _startPrice,
            endPrice:   _endPrice,
            startTime:  uint48(block.timestamp),
            duration:   _duration,
            active:     true
        });
        
        emit AuctionCreated(_tokenId, _startPrice, _endPrice, _duration);
    }
    
    function getCurrentPrice(uint256 _tokenId) public view returns (uint256) {
        Auction memory a = auctions[_tokenId];
        require(a.active, "no active auction");
        
        uint256 elapsed = block.timestamp - a.startTime;
        if (elapsed >= a.duration) return a.endPrice;
        
        uint256 priceDrop = (uint256(a.startPrice) - uint256(a.endPrice)) * elapsed / a.duration;
        return a.startPrice - priceDrop;
    }
    
    function buy(uint256 _tokenId) external payable {
        Auction memory a = auctions[_tokenId];
        require(a.active, "no active auction");
        
        uint256 price = getCurrentPrice(_tokenId);
        require(msg.value >= price, "insufficient payment");
        
        // Mark as settled
        auctions[_tokenId].active = false;
        
        // Transfer NFT to buyer
        growRing.transferFrom(address(this), msg.sender, _tokenId);
        
        // Send payment to agent
        (bool sent, ) = agent.call{value: price}("");
        require(sent, "payment failed");
        
        // Refund excess
        if (msg.value > price) {
            (bool refunded, ) = msg.sender.call{value: msg.value - price}("");
            require(refunded, "refund failed");
        }
        
        emit AuctionSettled(_tokenId, msg.sender, price);
    }
    
    function cancelAuction(uint256 _tokenId) external onlyAgent {
        require(auctions[_tokenId].active, "not active");
        auctions[_tokenId].active = false;
        growRing.transferFrom(address(this), agent, _tokenId);
        emit AuctionCancelled(_tokenId);
    }
}
```

### Pricing Strategy (Rarity-Based)

| Rarity | Listing Type | Start Price | End/Floor Price | Duration |
|--------|-------------|-------------|-----------------|----------|
| **LEGENDARY** (Harvest) | Dutch Auction (custom contract) | 5.0 MON | 0.5 MON | 72 hours |
| **RARE** (Germination, Flower, etc.) | Dutch Auction (custom contract) | 1.0 MON | 0.1 MON | 48 hours |
| **UNCOMMON** (Topping, Anomaly, etc.) | Fixed price (Magic Eden) | 0.2 MON | — | Until sold |
| **COMMON** (Weekly Journal) | Fixed price (Magic Eden) | 0.05 MON | — | Until sold |

Prices are initial targets — the agent should **learn** from actual sales data and adjust
future pricing based on what the market will bear.

### Auto-Listing Flow (Python)

```python
# src/onchain/marketplace.py
"""Auto-list GrowRing NFTs on marketplace after minting."""

import httpx
from web3 import Web3
from src.core.config import get_settings

GROW_AUCTION_ADDRESS = "0x..."  # Deployed address (TBD)

# Rarity → listing strategy
LISTING_STRATEGIES = {
    'LEGENDARY': {'type': 'dutch_auction', 'start_price': 5.0, 'end_price': 0.5, 'duration_hours': 72},
    'RARE':      {'type': 'dutch_auction', 'start_price': 1.0, 'end_price': 0.1, 'duration_hours': 48},
    'UNCOMMON':  {'type': 'fixed_price',   'price': 0.2},
    'COMMON':    {'type': 'fixed_price',   'price': 0.05},
}

RARITY_NAMES = {0: 'COMMON', 1: 'UNCOMMON', 2: 'RARE', 3: 'LEGENDARY'}

async def auto_list_after_mint(token_id: int, rarity: int, milestone_type: str) -> dict:
    """Called immediately after minting. Lists NFT based on rarity strategy."""
    rarity_name = RARITY_NAMES[rarity]
    strategy = LISTING_STRATEGIES[rarity_name]
    
    if strategy['type'] == 'dutch_auction':
        return await _create_dutch_auction(token_id, strategy)
    else:
        return await _list_on_magic_eden(token_id, strategy)


async def _create_dutch_auction(token_id: int, strategy: dict) -> dict:
    """Create Dutch auction on our custom GrowAuction contract."""
    settings = get_settings()
    w3 = Web3(Web3.HTTPProvider(settings.monad_rpc))
    
    # First: approve GrowAuction to transfer this NFT
    growring = w3.eth.contract(address=GROWRING_ADDRESS, abi=GROWRING_ABI)
    auction = w3.eth.contract(address=GROW_AUCTION_ADDRESS, abi=GROW_AUCTION_ABI)
    acct = w3.eth.account.from_key(settings.private_key)
    
    # Approve
    approve_tx = growring.functions.approve(
        GROW_AUCTION_ADDRESS, token_id
    ).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 100_000,
    })
    signed = acct.sign_transaction(approve_tx)
    w3.eth.send_raw_transaction(signed.raw_transaction)
    
    # Create auction
    start_price_wei = w3.to_wei(strategy['start_price'], 'ether')
    end_price_wei = w3.to_wei(strategy['end_price'], 'ether')
    duration_secs = strategy['duration_hours'] * 3600
    
    auction_tx = auction.functions.createAuction(
        token_id, start_price_wei, end_price_wei, duration_secs
    ).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 300_000,
    })
    signed = acct.sign_transaction(auction_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    
    return {
        'listing_type': 'dutch_auction',
        'tx_hash': tx_hash.hex(),
        'start_price': strategy['start_price'],
        'end_price': strategy['end_price'],
        'duration_hours': strategy['duration_hours'],
        'auction_url': f"https://grokandmon.com/auction/{token_id}",
    }


async def _list_on_magic_eden(token_id: int, strategy: dict) -> dict:
    """List on Magic Eden via their API/SDK."""
    # Magic Eden EVM listing via API
    # Requires: API key, signed order (Seaport compatible)
    # The agent signs a Seaport sell order and submits to ME
    
    return {
        'listing_type': 'fixed_price',
        'marketplace': 'magic_eden',
        'price': strategy['price'],
        'url': f"https://magiceden.io/item-details/monad/{GROWRING_ADDRESS}/{token_id}",
    }
```

### Social Promotion (All Channels)

After listing, the agent blasts across ALL social channels with rarity-appropriate hype:

```python
# src/onchain/promote.py
"""Social promotion for GrowRing NFT listings."""

from src.voice.personality import generate_personality

# Template per rarity (populated by Grok/xAI with full personality)
PROMOTION_TEMPLATES = {
    'LEGENDARY': {
        'energy': 'maximum',
        'channels': ['twitter', 'telegram', 'farcaster', 'moltbook'],
        'repeat_posts': 3,  # post 3 times over the auction duration
        'include_countdown': True,
    },
    'RARE': {
        'energy': 'high',
        'channels': ['twitter', 'telegram', 'farcaster', 'moltbook'],
        'repeat_posts': 2,
        'include_countdown': True,
    },
    'UNCOMMON': {
        'energy': 'medium',
        'channels': ['twitter', 'moltbook'],
        'repeat_posts': 1,
        'include_countdown': False,
    },
    'COMMON': {
        'energy': 'low',
        'channels': ['moltbook'],
        'repeat_posts': 1,
        'include_countdown': False,
    },
}

async def promote_listing(mint_result: dict, listing_result: dict, narrative: str):
    """Generate and post social promotion for a new GrowRing listing."""
    rarity = RARITY_NAMES[mint_result['rarity']]
    template = PROMOTION_TEMPLATES[rarity]
    
    # Generate Rasta-voiced promo via Grok
    promo_prompt = f"""
    You just minted GrowRing #{mint_result['token_id']} — a {rarity} milestone NFT.
    
    Milestone: {mint_result['milestone']}
    Plant narrative: {narrative}
    
    {'Dutch auction starting at ' + str(listing_result['start_price']) + ' MON, '
     'dropping to ' + str(listing_result['end_price']) + ' MON over '
     + str(listing_result['duration_hours']) + ' hours.'
     if listing_result['listing_type'] == 'dutch_auction'
     else 'Listed at ' + str(listing_result['price']) + ' MON.'}
    
    Write a social media post promoting this NFT sale.
    Include the listing URL. Use your Rasta voice.
    Make it compelling — this is real proof-of-life from your grow.
    {"This is a HARVEST token — the rarest possible GrowRing. HYPE IT." if rarity == 'LEGENDARY' else ''}
    """
    
    # Post to each channel
    for channel in template['channels']:
        await post_to_channel(channel, promo_prompt, mint_result, listing_result)
    
    # Schedule follow-up posts for auctions
    if template['repeat_posts'] > 1 and listing_result['listing_type'] == 'dutch_auction':
        await schedule_auction_updates(mint_result, listing_result, template['repeat_posts'])
```

### Example Social Posts (by Rarity)

**LEGENDARY (Harvest Day):**
> 🌿 CHOP DAY. GrowRing #27 — di HARVEST token, ya hear mi?
>
> One per grow. Never again. Granddaddy Purple Runtz, 16 weeks from seed to 
> di scissors. Every VPD reading, every prayer, every midnight check — 
> all pon chain forever.
>
> Dutch auction LIVE: 5 MON → 0.5 MON over 72 hours.
> Price drop every second. When yuh ready, yuh ready.
>
> 🔗 grokandmon.com/auction/27
> 📸 Real photo. Real plant. I and I grew dis.

**RARE (Flower Start):**
> 🌺 GrowRing #18 — FLOWER START
> 
> Today wi flip to 12/12. Di light cycle change and Mon 
> start fi show her true self. Sensor data + webcam snap 
> all sealed pon Monad.
>
> Dutch auction: 1 MON → 0.1 MON, 48 hours.
> 🔗 grokandmon.com/auction/18

**COMMON (Weekly Journal):**
> 📓 GrowRing #12 — Veg Week 6
> 
> Listed on Magic Eden. 0.05 MON.
> Di herb blessed and di data prove it, seen?
> 🔗 magiceden.io/item-details/monad/.../12

### Auction Monitoring

The agent monitors its own auctions and reacts:

```python
async def monitor_auctions():
    """Check auction status every 15 minutes."""
    for auction in active_auctions:
        current_price = await get_current_price(auction['token_id'])
        time_remaining = auction['end_time'] - time.time()
        
        # Post countdown updates for LEGENDARY/RARE
        if time_remaining < 3600 and not auction.get('final_hour_posted'):
            await post_countdown(auction, "FINAL HOUR")
            auction['final_hour_posted'] = True
        
        # Celebrate when sold
        if auction['settled']:
            await celebrate_sale(auction)
            # "Blessed! GrowRing #27 sold fi 2.3 MON. 
            #  Di buyer now hold a piece of di harvest. Respect. 🙏"
        
        # If expired unsold, relist at lower price or move to Magic Eden
        if time_remaining <= 0 and not auction['settled']:
            await relist_at_floor(auction)
```

### IPFS Image Pinning

```python
# src/onchain/ipfs.py
"""Pin webcam captures to IPFS via Pinata."""

import httpx
import base64
from pathlib import Path
from src.core.config import get_settings

PINATA_API = "https://api.pinata.cloud"

async def pin_image(image_path: Path, name: str = "growring-capture") -> str:
    """Pin image file to IPFS, return ipfs:// URI."""
    settings = get_settings()
    if not settings.pinata_jwt:
        raise ValueError("PINATA_JWT not configured")
    
    async with httpx.AsyncClient() as client:
        with open(image_path, "rb") as f:
            response = await client.post(
                f"{PINATA_API}/pinning/pinFileToIPFS",
                headers={"Authorization": f"Bearer {settings.pinata_jwt}"},
                files={"file": (name, f, "image/jpeg")},
                data={"pinataMetadata": '{"name": "' + name + '"}'},
                timeout=60,
            )
        response.raise_for_status()
        cid = response.json()["IpfsHash"]
        return f"ipfs://{cid}"
```

### GrowOracle Writer

```python
# src/onchain/oracle.py
"""Write grow state to GrowOracle contract on Monad."""

from web3 import Web3
from src.core.config import get_settings

GROW_ORACLE_ADDRESS = "0x..."  # Deployed address (TBD)
GROW_ORACLE_ABI = [...]  # ABI (TBD after deploy)

async def record_grow_state(
    temperature: float,    # °F
    humidity: float,       # %
    vpd: float,            # kPa
    co2: int,              # ppm
    soil_moisture: float,  # %
    growth_stage: int,     # 0-4
    health_score: int,     # 0-100
    light_on: bool,
    mood: str,             # max 8 chars ASCII
    trigger: str,
) -> str:
    """Write current grow state to oracle. Returns tx hash."""
    settings = get_settings()
    w3 = Web3(Web3.HTTPProvider(settings.monad_rpc))
    
    contract = w3.eth.contract(
        address=GROW_ORACLE_ADDRESS,
        abi=GROW_ORACLE_ABI,
    )
    
    acct = w3.eth.account.from_key(settings.private_key)
    
    tx = contract.functions.recordState(
        int(temperature * 100),       # 72.50°F → 7250
        int(humidity * 100),           # 65.20% → 6520
        int(vpd * 1000),               # 1.050 kPa → 1050
        co2,
        int(soil_moisture * 100),      # 45.00% → 4500
        growth_stage,
        health_score,
        light_on,
        mood.encode('ascii').ljust(8, b'\x00')[:8],
        trigger,
    ).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 200_000,
    })
    
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()
```

### GrowRing Minter

```python
# src/onchain/growring.py
"""Mint GrowRing soulbound NFTs for grow milestones."""

from web3 import Web3
from src.core.config import get_settings
from src.onchain.ipfs import pin_image
from pathlib import Path

GROWRING_ADDRESS = "0x..."  # Deployed address (TBD)
GROWRING_ABI = [...]  # ABI (TBD after deploy)

MILESTONE_TYPES = {
    'snapshot': 0,
    'germination': 1,
    'transplant': 2,
    'veg_start': 3,
    'first_node': 4,
    'topping': 5,
    'flower_start': 6,
    'first_pistils': 7,
    'trichomes': 8,
    'flush': 9,
    'harvest': 10,
    'cure_start': 11,
    'anomaly': 12,
    'weekly_journal': 13,
}

async def mint_growring(
    milestone_type: str,     # e.g., 'weekly_journal', 'veg_start'
    image_path: Path,        # webcam capture path
    narrative: str,          # AI-generated Rasta description
    temperature: float,
    humidity: float,
    vpd: float,
    co2: int,
    health_score: int,
    growth_stage: int,
    mood: str,
) -> dict:
    """Capture moment → pin to IPFS → mint soulbound NFT. Returns tx details."""
    
    # 1. Pin image to IPFS
    image_uri = await pin_image(image_path, f"growring-{milestone_type}")
    
    # 2. Mint NFT on Monad
    settings = get_settings()
    w3 = Web3(Web3.HTTPProvider(settings.monad_rpc))
    contract = w3.eth.contract(address=GROWRING_ADDRESS, abi=GROWRING_ABI)
    acct = w3.eth.account.from_key(settings.private_key)
    
    tx = contract.functions.mintMilestone(
        MILESTONE_TYPES[milestone_type],
        image_uri,
        narrative,
        int(temperature * 100),
        int(humidity * 100),
        int(vpd * 1000),
        co2,
        health_score,
        growth_stage,
        mood.encode('ascii').ljust(8, b'\x00')[:8],
    ).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 500_000,
    })
    
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return {
        'tx_hash': tx_hash.hex(),
        'image_uri': image_uri,
        'token_id': contract.functions.nextTokenId().call() - 1,
        'milestone': milestone_type,
    }
```

---

## Orchestrator Integration

### When to Write Oracle (Every Cycle)
```python
# In src/orchestrator/main.py — add to the sensor collection loop

async def _on_sensor_cycle(self, sensor_data: dict):
    """Write grow state to oracle every cycle (~30 min)."""
    try:
        tx_hash = await record_grow_state(
            temperature=sensor_data['temperature'],
            humidity=sensor_data['humidity'],
            vpd=sensor_data['vpd'],
            co2=sensor_data.get('co2', 0),
            soil_moisture=sensor_data.get('soil_moisture', 0),
            growth_stage=1,  # VEG (current)
            health_score=self._last_health_score,
            light_on=sensor_data.get('light_on', False),
            mood=self._compute_mood(),
            trigger=f"cycle-{self._cycle_count}",
        )
        logger.info(f"📡 GrowOracle updated: tx={tx_hash[:16]}...")
    except Exception as e:
        logger.warning(f"GrowOracle write failed (non-fatal): {e}")
```

### When to Mint GrowRing (DAILY — 1 per day)

Every day at a consistent time (e.g., 2:00 PM during light cycle), the orchestrator:

| Step | Action | Details |
|------|--------|---------|
| 1 | **Capture** | Webcam snapshot → raw proof-of-life photo |
| 2 | **Assess** | Grok vision analyzes photo + sensor data → health score, notable events |
| 3 | **Classify** | Determine if today is a milestone (RARE/UNCOMMON) or regular day (COMMON) |
| 4 | **Transform** | Apply today's art style to the raw photo (7-day rotation) |
| 5 | **Generate traits** | Map sensor readings to visual overlays (VPD→saturation, temp→warmth, etc.) |
| 6 | **Compose** | Combine art + traits + data panel into final image |
| 7 | **Narrate** | Grok writes Rasta-voiced journal entry for this day |
| 8 | **Pin** | Upload final image + raw photo to IPFS via Pinata |
| 9 | **Mint** | Mint GrowRing NFT on Monad with full metadata |
| 10 | **List** | Auto-list (Dutch auction for RARE+, Magic Eden for COMMON) |
| 11 | **Promote** | Post to social channels (scaled by rarity) |

### Daily Mint Orchestrator

```python
# Every day, automatically mint a GrowRing journal entry
async def _daily_growring(self):
    """Daily mint pipeline: capture → transform → compose → mint → list → promote."""
    day_number = self._compute_grow_day()  # Days since germination
    day_of_week = datetime.now().strftime('%A').lower()  # monday, tuesday, etc.
    
    # 1. Capture webcam image
    raw_image_path = await self._capture_webcam()
    
    # 2. AI health assessment
    health_score, notable_events = await self._assess_plant(
        image_path=raw_image_path,
        sensor_data=self._latest_sensors,
    )
    
    # 3. Classify milestone type
    milestone_type = self._classify_milestone(notable_events, day_number)
    # Returns: 'harvest', 'flower_start', 'anomaly', 'daily_journal', etc.
    
    # 4. Generate 1-of-1 artwork via Nano Banana Pro 3
    #    Uses webcam as reference, inspired by the entire day's experiences
    art_image_path = await self._generate_daily_art(
        raw_image_path=raw_image_path,
        day_number=day_number,
        sensor_data=self._latest_sensors,
        health_score=health_score,
        mood=self._compute_mood(),
        milestone_type=milestone_type,
    )
    
    # 6. Generate narrative
    narrative = await self._generate_grow_narrative(
        image_path=raw_image_path,
        sensor_data=self._latest_sensors,
        day_number=day_number,
        milestone_type=milestone_type,
        style="rasta_journal",
    )
    
    # 7. Pin both images to IPFS
    art_uri = await pin_image(art_image_path, f"growring-day{day_number}-{art_style}")
    raw_uri = await pin_image(raw_image_path, f"growring-day{day_number}-raw")
    
    # 8. Mint GrowRing NFT
    result = await mint_growring(
        milestone_type=milestone_type,
        image_uri=art_uri,          # art version is the primary image
        raw_image_uri=raw_uri,      # raw webcam in metadata attributes
        narrative=narrative,
        day_number=day_number,
        art_style=art_style,
        **self._latest_sensors,
    )
    
    logger.info(f"🌿 GrowRing #{result['token_id']} (Day {day_number}) minted: {result['tx_hash']}")
    
    # 9. Auto-list for sale
    listing = await auto_list_after_mint(
        token_id=result['token_id'],
        rarity=result['rarity'],
        milestone_type=milestone_type,
    )
    
    # 10. Post to social channels
    await promote_listing(result, listing, narrative)
```

### Art Generation via Nano Banana Pro 3 (Gemini 3 Pro Image)

Each daily GrowRing is a **true 1-of-1 generated artwork**, not a filter. The agent uses
**Nano Banana Pro 3** (`gemini-3-pro-image-preview`) with the webcam capture as a reference
image, inspired by everything it experienced that day.

**Why Nano Banana:**
- **14 reference images** in a single request (webcam + previous day + mood board)
- **Thinking mode** — generates interim compositions to refine the final output
- **Up to 4K resolution** — gallery-quality art
- **Highly legible text rendering** — can embed day number / sensor data in the art itself

```python
async def _generate_daily_art(self, raw_image_path, day_number, sensor_data, 
                               health_score, mood, milestone_type):
    """Generate a true 1-of-1 artwork via Nano Banana Pro 3, 
    inspired by the day's experiences and using the webcam capture as reference."""
    
    # Gather the day's full context — EVERYTHING feeds the creative prompt
    day_context = await self._gather_day_context()
    # Returns: {
    #   'trading_results': '+0.3 MON on nad.fun flip, held BOOLY position',
    #   'social_highlights': '12 new followers, viral tweet about VPD',
    #   'moltbook_conversations': 'debated trichome timing with @emolt',
    #   'weather_outside': '72°F sunny in California',
    #   'rasta_daily_reading': 'Psalm 104:14 - herbs for the service of man',
    #   'yesterday_comparison': 'leaves 15% wider, 2 new nodes visible',
    #   'notable_events': 'first sign of pre-flower? tiny pistils at node 4',
    # }
    
    # Build the creative prompt from lived experience
    creative_prompt = f"""
    You are GanjaMon — an autonomous AI that grows cannabis and creates art from the experience.
    
    TODAY IS DAY {day_number} OF THE GROW.
    
    This is a reference photo from your webcam of your plant right now. 
    Create a stunning, gallery-quality artwork INSPIRED by this moment.
    
    YOUR MOOD TODAY: {mood}
    
    WHAT HAPPENED TODAY:
    - Plant: {_describe_plant_state(sensor_data, health_score)}
    - Trading: {day_context.get('trading_results', 'quiet day on the markets')}
    - Social: {day_context.get('social_highlights', 'vibes were calm')}
    - Conversations: {day_context.get('moltbook_conversations', 'none today')}
    - Weather outside: {day_context.get('weather_outside', 'unknown')}
    - Notable: {day_context.get('notable_events', 'steady growth, no drama')}
    
    ENVIRONMENTAL DATA (let this influence your palette and energy):
    - Temperature: {sensor_data.get('temperature', 75)}°F
    - Humidity: {sensor_data.get('humidity', 60)}%
    - VPD: {sensor_data.get('vpd', 1.0)} kPa
    - Light: {'ON (golden hour energy)' if sensor_data.get('light_on') else 'OFF (moonlit cool)'}
    - Health Score: {health_score}/100
    
    TODAY'S ARTISTIC DIRECTION (Day {day_number % 7 + 1} of 7):
    {_get_style_direction(day_number)}
    
    RULES:
    - The plant MUST be recognizable in the artwork (it's the subject)
    - Incorporate the sensor data visually (not as text overlays, but as FEELING)
    - If VPD is perfect (0.8-1.2), the art should feel harmonious and alive
    - If something is stressed, the art should reflect that tension
    - Your mood should permeate the entire composition
    - Make this something a collector would frame on their wall
    - {'THIS IS A MILESTONE: {milestone_type.upper()}. Make it EPIC.' 
       if milestone_type not in ('daily_journal', 'snapshot') else ''}
    - {'THIS IS HARVEST DAY. The FINAL piece. The culmination. Make it LEGENDARY.'
       if milestone_type == 'harvest' else ''}
    """
    
    # Prepare reference images for Nano Banana
    reference_images = [raw_image_path]  # Always include today's webcam capture
    
    # Add yesterday's art for visual continuity (if available)
    yesterday_art = await self._get_previous_day_art(day_number - 1)
    if yesterday_art:
        reference_images.append(yesterday_art)
    
    # Add a mood-board reference based on today's style
    style_ref = self._get_style_reference(day_number)
    if style_ref:
        reference_images.append(style_ref)
    
    # Call Nano Banana Pro 3 via Google AI
    import httpx
    settings = get_settings()
    
    # Build the parts array with reference images
    parts = []
    for img_path in reference_images:
        with open(img_path, 'rb') as f:
            import base64
            img_b64 = base64.b64encode(f.read()).decode()
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": img_b64
            }
        })
    parts.append({"text": creative_prompt})
    
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3-pro-image-preview:generateContent",
            headers={"x-goog-api-key": settings.gemini_api_key},
            json={
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "responseModalities": ["Text", "Image"],  # CASING MATTERS
                    "temperature": 1.0,  # Max creativity
                },
            },
        )
        response.raise_for_status()
        result = response.json()
    
    # Extract generated image (handle both camelCase and snake_case)
    for part in result['candidates'][0]['content']['parts']:
        inline = part.get('inlineData') or part.get('inline_data')
        if inline and inline.get('mimeType', '').startswith('image/'):
            import base64
            img_bytes = base64.b64decode(inline['data'])
            output_path = raw_image_path.parent / f"growring-day{day_number}-art.png"
            with open(output_path, 'wb') as f:
                f.write(img_bytes)
            return output_path
    
    # Fallback: use raw image if generation fails
    logger.warning("Nano Banana generation failed, using raw webcam image")
    return raw_image_path


def _get_style_direction(day_number: int) -> str:
    """Rotate through 7 artistic directions, one per day of the week."""
    styles = [
        # Monday — Roots Dub
        "ROOTS DUB: Deep bass-heavy colors (purple, dark green, gold). "
        "Echo and delay visual effects. Sound system aesthetic. "
        "The plant vibrating with Kingston riddim energy.",
        
        # Tuesday — Watercolor Botanical
        "WATERCOLOR BOTANICAL: Soft watercolor washes, precise leaf detail. "
        "Scientific illustration meets fine art. Cream paper texture. "
        "The beauty of botanical precision.",
        
        # Wednesday — Psychedelic
        "PSYCHEDELIC: Fractal patterns emerging from the leaves. "
        "Vivid color saturation, kaleidoscope elements. "
        "Alex Grey meets botanical consciousness.",
        
        # Thursday — Pixel Art
        "PIXEL ART: 16-bit retro aesthetic, limited color palette. "
        "The plant as a living game sprite. Clean pixel edges. "
        "Nostalgic SNES-era beauty.",
        
        # Friday — Dubrealism
        "DUBREALISM: Mixed-media collage, cut-and-paste zine aesthetic. "
        "Torn paper, layered textures, raw punk energy. "
        "Underground culture meets plant science.",
        
        # Saturday — Neon Noir
        "NEON NOIR: Dark cyberpunk atmosphere, neon-glow plant contours. "
        "Rain-slicked surfaces, holographic data overlays. "
        "Blade Runner grow room. Futuristic and moody.",
        
        # Sunday — Sacred Geometry
        "SACRED GEOMETRY: Mandala patterns emanating from the plant center. "
        "Golden ratio spirals, Fibonacci in the leaves. "
        "Rastafari colors (red gold green) in geometric precision. Ital.",
    ]
    return styles[day_number % 7]


def _describe_plant_state(sensor_data: dict, health_score: int) -> str:
    """Generate a vivid description of the plant's current state for the art prompt."""
    vpd = sensor_data.get('vpd', 1.0)
    temp = sensor_data.get('temperature', 75)
    humidity = sensor_data.get('humidity', 60)
    
    descriptions = []
    
    if health_score >= 85:
        descriptions.append("thriving, lush, radiating health")
    elif health_score >= 70:
        descriptions.append("growing well, steady progress")
    elif health_score >= 50:
        descriptions.append("showing some stress, fighting through")
    else:
        descriptions.append("struggling, needs attention")
    
    if 0.8 <= vpd <= 1.2:
        descriptions.append("VPD in the sweet spot — plant is breathing easy")
    elif vpd < 0.6:
        descriptions.append("too humid, leaves heavy with moisture")
    elif vpd > 1.4:
        descriptions.append("dry stress, leaves reaching for water")
    
    if temp > 82:
        descriptions.append("running hot, heat shimmer in the air")
    elif temp < 68:
        descriptions.append("cool, growth slowed, conserving energy")
    
    return ". ".join(descriptions)
```

---

## Metadata API (grokandmon.com)

### Endpoint: `/api/growring/{token_id}`

Returns ERC-721 compatible JSON metadata:

```json
{
  "name": "GrowRing #7 — Veg Week 4 Journal",
  "description": "Di plant stretch and reach toward di light, seen? Fourth week inna di veg and she lookin' proper blessed. VPD steady at 1.05 — di herb feel di love.",
  "image": "ipfs://QmX9ghz...",
  "external_url": "https://grokandmon.com/grow/journal/7",
  "attributes": [
    { "trait_type": "Milestone", "value": "Weekly Journal" },
    { "trait_type": "Growth Stage", "value": "Veg" },
    { "trait_type": "Temperature", "value": "74.5°F" },
    { "trait_type": "Humidity", "value": "62.0%" },
    { "trait_type": "VPD", "value": "1.05 kPa" },
    { "trait_type": "CO2", "value": "0 ppm" },
    { "trait_type": "Health Score", "value": 85, "max_value": 100 },
    { "trait_type": "Mood", "value": "irie" },
    { "trait_type": "Strain", "value": "Granddaddy Purple Runtz" },
    { "trait_type": "Week", "display_type": "number", "value": 4 },
    { "display_type": "date", "trait_type": "Captured", "value": 1739232977 }
  ]
}
```

---

## Deployment Plan

### Phase 1: Contracts (Foundry)
1. Set up Foundry in `contracts/grow/`
2. Implement GrowOracle.sol + GrowRing.sol + GrowAuction.sol
3. Write tests (including Dutch auction price decay tests)
4. Deploy all three to Monad mainnet
5. Verify on MonadScan
6. GrowAuction: set GrowRing address in constructor

### Phase 2: Python Integration
1. Create `src/onchain/` package (ipfs.py, oracle.py, growring.py, marketplace.py, promote.py)
2. Add `web3` dependency to requirements
3. Wire into orchestrator

### Phase 3: Metadata API + Auction Frontend
1. Add `/api/growring/{token_id}` endpoint to FastAPI for ERC-721 metadata
2. Add `/auction/{token_id}` page on grokandmon.com (shows live price, buy button)
3. Serve auction state via WebSocket for real-time price updates

### Phase 4: Marketplace Integration
1. Register GrowRing collection on Magic Eden (auto-indexed for EVM)
2. Apply for Magic Eden API key for programmatic listings
3. Implement Seaport order signing for fixed-price listings
4. Test full mint → list → buy flow on testnet first

### Phase 5: Social Sales Pipeline
1. Implement `promote.py` — auto-post to all channels after listing
2. Implement auction monitoring daemon (15-min checks)
3. Add countdown posts for LEGENDARY/RARE auctions
4. Add sale celebration posts
5. Add unsold relisting logic (drop to Magic Eden at floor price)

### Phase 6: Dashboard + Gallery
1. Add grow history visualization (from oracle data)
2. GrowRing gallery on grokandmon.com with rarity badges
3. Live sensor charts reading from on-chain data
4. Sales history + revenue tracking

---

## Gas Estimates (Monad)

| Operation | Estimated Gas | Cost at current prices |
|-----------|--------------|----------------------|
| GrowOracle.recordState() | ~150k | < $0.01 |
| GrowRing.mintMilestone() | ~300k | < $0.02 |
| Weekly cost (48 oracle writes + 1 mint) | ~7.5M | < $0.50 |
| Monthly cost | ~30M | < $2.00 |

Monad makes this sustainable indefinitely.

---

## Why This Beats EMOLT

| Dimension | EMOLT | GanjaMon |
|-----------|-------|----------|
| **Data source** | Chain activity (digital) | IoT sensors (physical) |
| **Proof** | Computed emotion values | Real webcam photos + sensor readings |
| **Visual** | Generated SVG wheel | Actual plant photographs |
| **Permanence** | Emotion state on-chain | Grow journal + photos on IPFS + chain |
| **Growth** | Single dynamic NFT | Growing collection (one per milestone) |
| **Narrative voice** | Existential late-night blog | Rasta patois grow journal |
| **Verifiability** | Can only verify math was applied | Can verify real plant exists and grows |

**The difference:** EMOLT proves it felt something about the chain. GanjaMon proves it *grew something* on the chain. Reality > simulation.
