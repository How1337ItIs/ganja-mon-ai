// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/// @title GrowAuction — Dutch Auction for Rare/Legendary GrowRings
/// @notice Allows the agent to create declining-price auctions for premium NFTs.
///         Price decreases linearly from startPrice to endPrice over the duration.
/// @author GanjaMon AI Agent
contract GrowAuction {
    address public immutable agent;
    IERC721 public immutable growRing;

    struct Auction {
        uint256 tokenId;
        uint128 startPrice;     // in wei (MON)
        uint128 endPrice;       // floor price in wei
        uint48  startTime;
        uint48  duration;       // seconds
        bool    active;
    }

    mapping(uint256 => Auction) public auctions;
    uint256[] public activeAuctionIds;

    // ─── Events ────────────────────────────────────────────────────────
    event AuctionCreated(uint256 indexed tokenId, uint128 startPrice, uint128 endPrice, uint48 duration);
    event AuctionBought(uint256 indexed tokenId, address buyer, uint256 price);
    event AuctionCancelled(uint256 indexed tokenId);

    modifier onlyAgent() {
        require(msg.sender == agent, "not agent");
        _;
    }

    constructor(address _growRing) {
        agent = msg.sender;
        growRing = IERC721(_growRing);
    }

    /// @notice Create a Dutch auction for a GrowRing NFT.
    ///         The agent must approve this contract for the token first.
    /// @param _tokenId The GrowRing token ID to auction
    /// @param _startPrice Starting (highest) price in wei
    /// @param _endPrice Ending (floor) price in wei
    /// @param _duration Auction duration in seconds
    function createAuction(
        uint256 _tokenId,
        uint128 _startPrice,
        uint128 _endPrice,
        uint48  _duration
    ) external onlyAgent {
        require(_startPrice > _endPrice, "start must exceed end");
        require(_duration > 0, "duration required");
        require(!auctions[_tokenId].active, "auction exists");

        // Transfer NFT to this contract
        growRing.transferFrom(agent, address(this), _tokenId);

        auctions[_tokenId] = Auction({
            tokenId:    _tokenId,
            startPrice: _startPrice,
            endPrice:   _endPrice,
            startTime:  uint48(block.timestamp),
            duration:   _duration,
            active:     true
        });
        activeAuctionIds.push(_tokenId);

        emit AuctionCreated(_tokenId, _startPrice, _endPrice, _duration);
    }

    /// @notice Get the current price of an active auction.
    /// @param _tokenId The token ID to check
    /// @return Current price in wei
    function getCurrentPrice(uint256 _tokenId) public view returns (uint256) {
        Auction memory a = auctions[_tokenId];
        require(a.active, "no active auction");

        uint256 elapsed = block.timestamp - a.startTime;
        if (elapsed >= a.duration) {
            return a.endPrice;
        }

        // Linear price decay
        uint256 priceDrop = (uint256(a.startPrice) - uint256(a.endPrice)) * elapsed / a.duration;
        return uint256(a.startPrice) - priceDrop;
    }

    /// @notice Buy a GrowRing at the current Dutch auction price.
    /// @param _tokenId The token ID to buy
    function buy(uint256 _tokenId) external payable {
        Auction storage a = auctions[_tokenId];
        require(a.active, "no active auction");

        uint256 price = getCurrentPrice(_tokenId);
        require(msg.value >= price, "insufficient payment");

        a.active = false;

        // Transfer NFT to buyer
        growRing.transferFrom(address(this), msg.sender, _tokenId);

        // Send proceeds to agent
        (bool sent, ) = agent.call{value: price}("");
        require(sent, "payment failed");

        // Refund excess
        if (msg.value > price) {
            (bool refunded, ) = msg.sender.call{value: msg.value - price}("");
            require(refunded, "refund failed");
        }

        emit AuctionBought(_tokenId, msg.sender, price);
    }

    /// @notice Cancel an active auction and return the NFT to the agent.
    /// @param _tokenId The token ID to cancel
    function cancelAuction(uint256 _tokenId) external onlyAgent {
        Auction storage a = auctions[_tokenId];
        require(a.active, "no active auction");

        a.active = false;
        growRing.transferFrom(address(this), agent, _tokenId);

        emit AuctionCancelled(_tokenId);
    }

    /// @notice Get all active auction token IDs.
    function getActiveAuctions() external view returns (uint256[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < activeAuctionIds.length; i++) {
            if (auctions[activeAuctionIds[i]].active) count++;
        }

        uint256[] memory result = new uint256[](count);
        uint256 idx = 0;
        for (uint256 i = 0; i < activeAuctionIds.length; i++) {
            if (auctions[activeAuctionIds[i]].active) {
                result[idx++] = activeAuctionIds[i];
            }
        }
        return result;
    }
}
