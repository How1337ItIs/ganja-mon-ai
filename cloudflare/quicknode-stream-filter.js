/**
 * QuickNode Streams Filter Function for GrowRing Events on Monad
 *
 * This filter runs server-side on QuickNode infrastructure.
 * It filters the logs dataset for GrowRing contract events:
 * - MilestoneMinted (daily NFT mints)
 * - GrowStateUpdated (oracle state changes)
 * - Transfer (NFT transfers)
 * - AuctionCreated (rare/legendary auction listings)
 *
 * Setup: Base64-encode this function and pass it as `filter_function`
 * when creating a Stream via the QuickNode REST API.
 *
 * Stream config:
 *   network: "monad-mainnet"
 *   dataset: "block_with_receipts" (or "logs")
 *   destination: "https://grokandmon.com/webhook/quicknode-stream"
 */
function main(stream) {
  try {
    const data = stream.data;

    // GrowRing contract on Monad mainnet
    const GROWRING = "0x1e4343bab5d0bc47a5ef83b90808b0db64e9e43b";
    // GrowOracle contract on Monad mainnet
    const GROWORACLE = "0xc532820de55363633263f6a95fa0762ed86e8425";
    // GrowAuction contract on Monad mainnet
    const GROWAUCTION = "0xc07ca3a855b9623db3aa733b86daf2fa8ea9a5a4";

    const CONTRACTS = new Set([GROWRING, GROWORACLE, GROWAUCTION]);

    // Event signatures (keccak256)
    const EVENTS = new Set([
      "0xef2e64b382d24fff9ba66c43a7b16c65379eba5f3586b31bc014ccebd2e91f1c", // MilestoneMinted
      "0xc7d6f7db626b33182a5a7193002ea098ea96e9859ad0aef9206090309eea2af3", // GrowStateUpdated
      "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef", // Transfer (ERC-721)
      "0xa9c8dfcda5664a5a124c713e386da27de87432d5b668e79458501eb296389ba7", // AuctionCreated
    ]);

    const matched = [];

    // Handle block_with_receipts dataset (nested receipts → logs)
    if (data && data.receipts) {
      for (const receipt of data.receipts) {
        if (!receipt.logs) continue;
        for (const log of receipt.logs) {
          const addr = (log.address || "").toLowerCase();
          const topic0 = log.topics && log.topics[0];
          if (CONTRACTS.has(addr) && EVENTS.has(topic0)) {
            matched.push({
              address: log.address,
              topics: log.topics,
              data: log.data,
              blockNumber: data.number || log.blockNumber,
              transactionHash: receipt.transactionHash || log.transactionHash,
              logIndex: log.logIndex,
            });
          }
        }
      }
    }

    // Handle logs dataset (flat array of log arrays)
    if (Array.isArray(data)) {
      for (const item of data) {
        const logs = Array.isArray(item) ? item : [item];
        for (const log of logs) {
          const addr = (log.address || "").toLowerCase();
          const topic0 = log.topics && log.topics[0];
          if (CONTRACTS.has(addr) && EVENTS.has(topic0)) {
            matched.push({
              address: log.address,
              topics: log.topics,
              data: log.data,
              blockNumber: log.blockNumber,
              transactionHash: log.transactionHash,
              logIndex: log.logIndex,
            });
          }
        }
      }
    }

    // Return null to skip delivery if no matches
    return matched.length > 0 ? matched : null;

  } catch (error) {
    return null;
  }
}
