// Bridge SOL to Base ETH via Relay
const { Connection, Keypair, Transaction, PublicKey, TransactionInstruction, sendAndConfirmTransaction } = require("@solana/web3.js");
const crypto = require("crypto");

const PRIVATE_KEY = "0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8";
const SOLANA_RPC = "https://api.mainnet-beta.solana.com";

async function main() {
  console.log("=== Relay Bridge: SOL -> Base ETH ===");

  const seed = crypto.createHash("sha256").update(PRIVATE_KEY).digest();
  const solKeypair = Keypair.fromSeed(seed);
  const solConnection = new Connection(SOLANA_RPC);

  const solBal = await solConnection.getBalance(solKeypair.publicKey);
  console.log("Solana wallet:", solKeypair.publicKey.toBase58());
  console.log("SOL balance:", solBal / 1e9);

  // Use most of SOL, leave some for fees
  const bridgeAmount = Math.floor(solBal * 0.95);
  console.log("Bridging:", bridgeAmount / 1e9, "SOL");

  // Get fresh quote from Relay
  const quoteRes = await fetch("https://api.relay.link/quote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user: solKeypair.publicKey.toBase58(),
      originChainId: 792703809,
      destinationChainId: 8453,
      originCurrency: "11111111111111111111111111111111",
      destinationCurrency: "0x0000000000000000000000000000000000000000",
      amount: bridgeAmount.toString(),
      recipient: "0xF909fF1806DbdffEfB7687754eA7a28085d4a80b",
      tradeType: "EXACT_INPUT"
    })
  });

  const quote = await quoteRes.json();

  if (!quote.steps || !quote.steps[0] || !quote.steps[0].items || !quote.steps[0].items[0] ||
      !quote.steps[0].items[0].data || !quote.steps[0].items[0].data.instructions) {
    console.log("Failed to get instructions from quote");
    console.log(JSON.stringify(quote, null, 2));
    return;
  }

  const instructions = quote.steps[0].items[0].data.instructions;
  console.log("Instructions count:", instructions.length);

  const inputSOL = Number(quote.details.currencyIn.amount) / 1e9;
  const outputETH = Number(quote.details.currencyOut.amount) / 1e18;
  console.log("Quote:", inputSOL.toFixed(4), "SOL ->", outputETH.toFixed(6), "ETH on Base");
  console.log("Fees:", quote.fees.relayer.amountFormatted, "SOL (~$" + quote.fees.relayer.amountUsd + ")");

  // Build transaction from instructions
  const transaction = new Transaction();

  for (const ix of instructions) {
    const keys = ix.keys.map(k => ({
      pubkey: new PublicKey(k.pubkey),
      isSigner: k.isSigner,
      isWritable: k.isWritable
    }));

    const programId = new PublicKey(ix.programId);
    const dataHex = ix.data.startsWith("0x") ? ix.data.slice(2) : ix.data;
    const data = Buffer.from(dataHex, "hex");

    transaction.add(new TransactionInstruction({ keys, programId, data }));
  }

  // Get fresh blockhash
  const { blockhash, lastValidBlockHeight } = await solConnection.getLatestBlockhash("confirmed");
  transaction.recentBlockhash = blockhash;
  transaction.feePayer = solKeypair.publicKey;

  console.log("\nSending transaction...");

  try {
    const signature = await sendAndConfirmTransaction(solConnection, transaction, [solKeypair], {
      commitment: "confirmed"
    });
    console.log("SUCCESS! Signature:", signature);
    console.log("\nETH should arrive on Base in ~5 seconds");
    console.log("Check: https://basescan.org/address/0xF909fF1806DbdffEfB7687754eA7a28085d4a80b");
  } catch (e) {
    console.log("Transaction error:", e.message);
    if (e.logs) {
      console.log("Logs:", e.logs.slice(0, 20).join("\n"));
    }
  }
}

main().catch(console.error);
