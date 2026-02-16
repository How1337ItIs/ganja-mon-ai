// Test Solana round-trip: MON → SOL → $MON → (can't do back due to minimums)
const { ethers } = require('ethers');
const { Keypair, Connection, LAMPORTS_PER_SOL, Transaction, SystemProgram, sendAndConfirmTransaction } = require('@solana/web3.js');
const crypto = require('crypto');

// Config
const MONAD_RPC = 'https://rpc.monad.xyz';
const SOLANA_RPC = 'https://api.mainnet-beta.solana.com';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';
const DEBRIDGE_API = 'https://api.dln.trade/v1.0';

// Chain IDs
const DEBRIDGE_MONAD_CHAIN_ID = 100000030;
const DEBRIDGE_SOLANA_CHAIN_ID = 7565164;

// Addresses
const MONAD_NATIVE = '0x0000000000000000000000000000000000000000';
const SOLANA_NATIVE = '11111111111111111111111111111111';
const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('=== Solana Round-Trip Test ===\n');

  // Setup providers and wallets
  const monadProvider = new ethers.JsonRpcProvider(MONAD_RPC);
  const monadWallet = new ethers.Wallet(PRIVATE_KEY, monadProvider);
  const evmAddress = monadWallet.address;

  // Derive Solana keypair from same seed
  const seed = crypto.createHash('sha256').update(PRIVATE_KEY).digest();
  const solKeypair = Keypair.fromSeed(seed);
  const solConnection = new Connection(SOLANA_RPC);

  console.log('EVM Wallet:', evmAddress);
  console.log('Solana Wallet:', solKeypair.publicKey.toBase58());

  // === STEP 1: Check starting balances ===
  console.log('\n--- Step 1: Starting Balances ---');
  const startMonadBal = await monadProvider.getBalance(evmAddress);
  const startSolBal = await solConnection.getBalance(solKeypair.publicKey);

  const monToken = new ethers.Contract(MON_TOKEN, ['function balanceOf(address) view returns (uint256)'], monadProvider);
  const startMonTokenBal = await monToken.balanceOf(evmAddress);

  console.log('Monad MON:', ethers.formatEther(startMonadBal));
  console.log('Solana SOL:', startSolBal / LAMPORTS_PER_SOL);
  console.log('$MON Token:', ethers.formatEther(startMonTokenBal));

  // Check if we already have SOL
  if (startSolBal >= 0.001 * LAMPORTS_PER_SOL) {
    console.log('\n✅ Already have SOL, skipping MON → SOL bridge');
  } else {
    // === STEP 2: Bridge MON → SOL ===
    console.log('\n--- Step 2: Bridging MON → SOL via deBridge ---');

    // Get quote for 50 MON
    const bridgeAmount = ethers.parseEther('50').toString();

    const quoteUrl = new URL(`${DEBRIDGE_API}/dln/order/quote`);
    quoteUrl.searchParams.append('srcChainId', DEBRIDGE_MONAD_CHAIN_ID);
    quoteUrl.searchParams.append('srcChainTokenIn', MONAD_NATIVE);
    quoteUrl.searchParams.append('srcChainTokenInAmount', bridgeAmount);
    quoteUrl.searchParams.append('dstChainId', DEBRIDGE_SOLANA_CHAIN_ID);
    quoteUrl.searchParams.append('dstChainTokenOut', SOLANA_NATIVE);
    quoteUrl.searchParams.append('prependOperatingExpenses', 'true');

    const quoteRes = await fetch(quoteUrl);
    const quote = await quoteRes.json();

    if (quote.error) {
      console.log('Quote error:', quote.error, quote.errorMessage);
      return;
    }

    const inputMON = Number(quote.estimation.srcChainTokenIn.amount) / 1e18;
    const outputSOL = Number(quote.estimation.dstChainTokenOut.amount) / 1e9;
    console.log('Quote: ~', inputMON.toFixed(2), 'MON →', outputSOL.toFixed(6), 'SOL');

    // Get transaction
    const txUrl = new URL(`${DEBRIDGE_API}/dln/order/create-tx`);
    txUrl.searchParams.append('srcChainId', DEBRIDGE_MONAD_CHAIN_ID);
    txUrl.searchParams.append('srcChainTokenIn', MONAD_NATIVE);
    txUrl.searchParams.append('srcChainTokenInAmount', bridgeAmount);
    txUrl.searchParams.append('dstChainId', DEBRIDGE_SOLANA_CHAIN_ID);
    txUrl.searchParams.append('dstChainTokenOut', SOLANA_NATIVE);
    txUrl.searchParams.append('dstChainTokenOutRecipient', solKeypair.publicKey.toBase58());
    txUrl.searchParams.append('srcChainOrderAuthorityAddress', evmAddress);
    txUrl.searchParams.append('dstChainOrderAuthorityAddress', solKeypair.publicKey.toBase58());
    txUrl.searchParams.append('prependOperatingExpenses', 'true');

    const txRes = await fetch(txUrl);
    const txData = await txRes.json();

    if (txData.error) {
      console.log('Transaction error:', txData.error, txData.errorMessage);
      return;
    }

    console.log('Executing MON → SOL bridge...');
    // Use gas limit from API if available, otherwise use high default
    const gasLimit = txData.estimatedTransactionFee?.details?.gasLimit || 1500000;
    console.log('Gas limit:', gasLimit);
    console.log('TX value:', txData.tx.value);
    console.log('TX data length:', txData.tx.data?.length || 0);

    const bridgeTx = await monadWallet.sendTransaction({
      to: txData.tx.to,
      data: txData.tx.data,
      value: txData.tx.value,
      gasLimit: gasLimit
    });
    console.log('Bridge tx:', bridgeTx.hash);
    const bridgeReceipt = await bridgeTx.wait();
    console.log('Status:', bridgeReceipt.status === 1 ? 'SUCCESS' : 'FAILED');

    if (bridgeReceipt.status !== 1) {
      console.log('Bridge failed!');
      return;
    }

    // Wait for bridge completion
    console.log('\nWaiting for SOL to arrive (may take 1-5 minutes)...');
    let solReceived = false;
    for (let i = 0; i < 60 && !solReceived; i++) {
      await sleep(5000);
      const newSolBal = await solConnection.getBalance(solKeypair.publicKey);
      console.log(`  Check ${i + 1}: ${newSolBal / LAMPORTS_PER_SOL} SOL`);
      if (newSolBal > startSolBal) {
        solReceived = true;
        console.log('✅ SOL received!');
      }
    }
  }

  // === STEP 3: Check SOL balance ===
  await sleep(5000);
  const currentSolBal = await solConnection.getBalance(solKeypair.publicKey);
  console.log('\n--- Step 3: Current SOL Balance ---');
  console.log('SOL:', currentSolBal / LAMPORTS_PER_SOL);

  if (currentSolBal < 0.001 * LAMPORTS_PER_SOL) {
    console.log('Not enough SOL for testing. Need at least 0.001 SOL');
    return;
  }

  // === STEP 4: Test SOL → $MON ===
  console.log('\n--- Step 4: Testing SOL → $MON via deBridge ---');

  // Use half of available SOL
  const solToSwap = Math.floor(currentSolBal / 2);
  console.log('Swapping:', solToSwap / LAMPORTS_PER_SOL, 'SOL for $MON');

  const solQuoteUrl = new URL(`${DEBRIDGE_API}/dln/order/quote`);
  solQuoteUrl.searchParams.append('srcChainId', DEBRIDGE_SOLANA_CHAIN_ID);
  solQuoteUrl.searchParams.append('srcChainTokenIn', SOLANA_NATIVE);
  solQuoteUrl.searchParams.append('srcChainTokenInAmount', solToSwap.toString());
  solQuoteUrl.searchParams.append('dstChainId', DEBRIDGE_MONAD_CHAIN_ID);
  solQuoteUrl.searchParams.append('dstChainTokenOut', MON_TOKEN);
  solQuoteUrl.searchParams.append('prependOperatingExpenses', 'true');

  const solQuoteRes = await fetch(solQuoteUrl);
  const solQuote = await solQuoteRes.json();

  if (solQuote.error) {
    console.log('SOL → $MON quote error:', solQuote.error, solQuote.errorMessage);
    console.log('May need more SOL for minimum amount');

    // Try with native MON instead
    console.log('\nTrying SOL → native MON instead...');
    solQuoteUrl.searchParams.set('dstChainTokenOut', MONAD_NATIVE);
    const solQuoteRes2 = await fetch(solQuoteUrl);
    const solQuote2 = await solQuoteRes2.json();

    if (solQuote2.error) {
      console.log('SOL → MON also failed:', solQuote2.error, solQuote2.errorMessage);
      return;
    }

    const outMON = Number(solQuote2.estimation.dstChainTokenOut.amount) / 1e18;
    console.log('Would receive:', outMON.toFixed(4), 'native MON');
    console.log('\n⚠️ Note: deBridge has high minimums for Solana swaps');
    console.log('The swap UI quotes work, but actual execution requires ~$20+ value');
    return;
  }

  const outMonToken = Number(solQuote.estimation.dstChainTokenOut.amount) / 1e18;
  console.log('Quote:', solToSwap / LAMPORTS_PER_SOL, 'SOL →', outMonToken.toFixed(2), '$MON');

  // Get SOL → $MON transaction
  const solTxUrl = new URL(`${DEBRIDGE_API}/dln/order/create-tx`);
  solTxUrl.searchParams.append('srcChainId', DEBRIDGE_SOLANA_CHAIN_ID);
  solTxUrl.searchParams.append('srcChainTokenIn', SOLANA_NATIVE);
  solTxUrl.searchParams.append('srcChainTokenInAmount', solToSwap.toString());
  solTxUrl.searchParams.append('dstChainId', DEBRIDGE_MONAD_CHAIN_ID);
  solTxUrl.searchParams.append('dstChainTokenOut', MON_TOKEN);
  solTxUrl.searchParams.append('dstChainTokenOutRecipient', evmAddress);
  solTxUrl.searchParams.append('srcChainOrderAuthorityAddress', solKeypair.publicKey.toBase58());
  solTxUrl.searchParams.append('dstChainOrderAuthorityAddress', evmAddress);
  solTxUrl.searchParams.append('prependOperatingExpenses', 'true');

  const solTxRes = await fetch(solTxUrl);
  const solTxData = await solTxRes.json();

  if (solTxData.error) {
    console.log('SOL → $MON tx error:', solTxData.error, solTxData.errorMessage);
    return;
  }

  console.log('\nSOL → $MON transaction data received');
  console.log('This requires signing a Solana transaction...');

  // The tx.data for Solana is a serialized transaction
  // We need to deserialize, sign, and send
  const txBase64 = solTxData.tx?.data;
  if (txBase64) {
    console.log('Transaction ready for Solana wallet signature');
    console.log('Tx size:', txBase64.length, 'bytes');

    // Decode and sign
    const txBuffer = Buffer.from(txBase64, 'base64');
    const transaction = Transaction.from(txBuffer);

    console.log('\nSigning and sending Solana transaction...');
    try {
      const signature = await sendAndConfirmTransaction(solConnection, transaction, [solKeypair], {
        commitment: 'confirmed'
      });
      console.log('Solana tx signature:', signature);
      console.log('✅ SOL → $MON transaction sent!');

      // Wait for $MON arrival
      console.log('\nWaiting for $MON to arrive on Monad...');
      for (let i = 0; i < 60; i++) {
        await sleep(5000);
        const newMonTokenBal = await monToken.balanceOf(evmAddress);
        if (newMonTokenBal > startMonTokenBal) {
          console.log('✅ $MON received!');
          console.log('New $MON balance:', ethers.formatEther(newMonTokenBal));
          break;
        }
        console.log(`  Check ${i + 1}: waiting...`);
      }
    } catch (err) {
      console.log('Solana tx error:', err.message);
    }
  }

  // === Final Summary ===
  console.log('\n=== Final Balances ===');
  const endMonadBal = await monadProvider.getBalance(evmAddress);
  const endSolBal = await solConnection.getBalance(solKeypair.publicKey);
  const endMonTokenBal = await monToken.balanceOf(evmAddress);

  console.log('Monad MON:', ethers.formatEther(endMonadBal));
  console.log('Solana SOL:', endSolBal / LAMPORTS_PER_SOL);
  console.log('$MON Token:', ethers.formatEther(endMonTokenBal));
}

main().catch(console.error);
