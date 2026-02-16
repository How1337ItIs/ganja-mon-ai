// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/GrowOracle.sol";
import "../src/GrowRing.sol";
import "../src/GrowAuction.sol";

/// @title Deploy GrowRing System to Monad
/// @notice Deploys GrowOracle, GrowRing, and GrowAuction in sequence.
///
/// Usage:
///   forge script script/Deploy.s.sol --rpc-url monad --broadcast --private-key $PRIVATE_KEY
contract DeployGrowSystem is Script {
    function run() public {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        string memory baseURI = vm.envOr("GROWRING_BASE_URI", string("https://grokandmon.com/api/growring/"));

        vm.startBroadcast(deployerKey);

        // 1) GrowOracle — continuous grow state
        GrowOracle oracle = new GrowOracle();
        console.log("GrowOracle deployed:", address(oracle));

        // 2) GrowRing — daily 1/1 NFT journal
        GrowRing ring = new GrowRing(baseURI);
        console.log("GrowRing deployed:", address(ring));

        // 3) GrowAuction — Dutch auctions for RARE/LEGENDARY
        GrowAuction auction = new GrowAuction(address(ring));
        console.log("GrowAuction deployed:", address(auction));

        vm.stopBroadcast();

        // Log addresses for config
        console.log("---");
        console.log("Add to .env:");
        console.log("GROW_ORACLE_ADDRESS=", address(oracle));
        console.log("GROWRING_ADDRESS=", address(ring));
        console.log("GROW_AUCTION_ADDRESS=", address(auction));
    }
}
