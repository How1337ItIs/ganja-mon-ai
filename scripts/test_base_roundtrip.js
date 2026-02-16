// End-to-end test: Base ETH → $MON → Base ETH
const { ethers } = require('ethers');

// Config
const MONAD_RPC = 'https://rpc.monad.xyz';
const BASE_RPC = 'https://mainnet.base.org';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';
const LIFI_API = 'https://li.quest/v1';

// Chain IDs
const MONAD_CHAIN_ID = 143;
const BASE_CHAIN_ID = 8453;

// Addresses
const NATIVE_TOKEN = '0x0000000000000000000000000000000000000000';
const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getLifiQuote(fromChain, toChain, fromToken, toToken, amount, wallet) {
  const url = new URL(`${LIFI_API}/quote`);
  url.searchParams.append('fromChain', fromChain);
  url.searchParams.append('toChain', toChain);
  url.searchParams.append('fromToken', fromToken);
  url.searchParams.append('toToken', toToken);
  url.searchParams.append('fromAmount', amount);
  url.searchParams.append('fromAddress', wallet);
  url.searchParams.append('toAddress', wallet);
  url.searchParams.append('slippage', '0.05');

  const res = await fetch(url);
  return await res.json();
}

async function checkBridgeStatus(txHash, fromChain, toChain) {
  const url = new URL(`${LIFI_API}/status`);
  url.searchParams.append('txHash', txHash);
  url.searchParams.append('fromChain', fromChain);
  url.searchParams.append('toChain', toChain);

  const res = await fetch(url);
  return await res.json();
}

async function main() {
  console.log('=== Base ETH ↔ $MON Round-Trip Test ===\n');

  const monadProvider = new ethers.JsonRpcProvider(MONAD_RPC);
  const baseProvider = new ethers.JsonRpcProvider(BASE_RPC);
  const monadWallet = new ethers.Wallet(PRIVATE_KEY, monadProvider);
  const baseWallet = new ethers.Wallet(PRIVATE_KEY, baseProvider);

  const walletAddress = monadWallet.address;
  console.log('Wallet:', walletAddress);

  // === STEP 1: Check starting balances ===
  console.log('\n--- Step 1: Starting Balances ---');
  const startBaseBal = await baseProvider.getBalance(walletAddress);
  const startMonadBal = await monadProvider.getBalance(walletAddress);

  const monToken = new ethers.Contract(MON_TOKEN, ['function balanceOf(address) view returns (uint256)'], monadProvider);
  const startMonTokenBal = await monToken.balanceOf(walletAddress);

  console.log('Base ETH:', ethers.formatEther(startBaseBal));
  console.log('Monad MON:', ethers.formatEther(startMonadBal));
  console.log('$MON Token:', ethers.formatEther(startMonTokenBal));

  // Bridge amount: 0.0005 ETH (small test)
  const bridgeAmount = ethers.parseEther('0.0005').toString();

  // === STEP 2: Get quote for Base ETH → $MON ===
  console.log('\n--- Step 2: Getting quote for Base ETH → $MON ---');
  const buyQuote = await getLifiQuote(
    BASE_CHAIN_ID, MONAD_CHAIN_ID,
    NATIVE_TOKEN, MON_TOKEN,
    bridgeAmount, walletAddress
  );

  if (buyQuote.message || buyQuote.error) {
    console.log('Quote error:', buyQuote.message || buyQuote.error);
    return;
  }

  console.log('Quote:');
  console.log('  Input:', ethers.formatEther(buyQuote.estimate?.fromAmount || '0'), 'ETH');
  console.log('  Output:', ethers.formatEther(buyQuote.estimate?.toAmount || '0'), '$MON');
  console.log('  Bridge:', buyQuote.toolDetails?.name);
  console.log('  Est. time:', buyQuote.estimate?.executionDuration, 'seconds');

  // === STEP 3: Execute Base ETH → $MON bridge+swap ===
  console.log('\n--- Step 3: Executing Base ETH → $MON ---');
  const buyTx = buyQuote.transactionRequest;

  console.log('Sending transaction...');
  const buyTxResponse = await baseWallet.sendTransaction({
    to: buyTx.to,
    data: buyTx.data,
    value: buyTx.value,
    gasLimit: buyTx.gasLimit || 500000
  });

  console.log('Tx hash:', buyTxResponse.hash);
  const buyReceipt = await buyTxResponse.wait();
  console.log('Status:', buyReceipt.status === 1 ? 'SUCCESS' : 'FAILED');
  console.log('Gas used:', buyReceipt.gasUsed.toString());

  if (buyReceipt.status !== 1) {
    console.log('Buy transaction failed!');
    return;
  }

  // === STEP 4: Wait for bridge completion ===
  console.log('\n--- Step 4: Waiting for bridge completion ---');
  console.log('This may take 1-5 minutes...');

  let bridgeComplete = false;
  let attempts = 0;
  const maxAttempts = 60; // 5 minutes max

  while (!bridgeComplete && attempts < maxAttempts) {
    await sleep(5000);
    attempts++;

    try {
      const status = await checkBridgeStatus(buyTxResponse.hash, BASE_CHAIN_ID, MONAD_CHAIN_ID);
      console.log(`  Attempt ${attempts}: ${status.status || 'PENDING'}`);

      if (status.status === 'DONE') {
        bridgeComplete = true;
        console.log('✅ Bridge completed!');
        if (status.receiving) {
          console.log('  Received:', ethers.formatEther(status.receiving.amount), '$MON');
        }
      } else if (status.status === 'FAILED') {
        console.log('❌ Bridge failed!');
        return;
      }
    } catch (e) {
      console.log(`  Attempt ${attempts}: Checking...`);
    }
  }

  if (!bridgeComplete) {
    console.log('Bridge taking too long, continuing anyway...');
  }

  // Wait a bit more for balance to update
  await sleep(10000);

  // === STEP 5: Check intermediate balances ===
  console.log('\n--- Step 5: Intermediate Balances ---');
  const midBaseBal = await baseProvider.getBalance(walletAddress);
  const midMonadBal = await monadProvider.getBalance(walletAddress);
  const midMonTokenBal = await monToken.balanceOf(walletAddress);

  console.log('Base ETH:', ethers.formatEther(midBaseBal));
  console.log('Monad MON:', ethers.formatEther(midMonadBal));
  console.log('$MON Token:', ethers.formatEther(midMonTokenBal));

  const monTokenReceived = midMonTokenBal - startMonTokenBal;
  console.log('$MON received:', ethers.formatEther(monTokenReceived));

  if (monTokenReceived <= 0) {
    console.log('No $MON received, waiting more...');
    await sleep(30000);
    const newMonTokenBal = await monToken.balanceOf(walletAddress);
    console.log('Updated $MON balance:', ethers.formatEther(newMonTokenBal));
  }

  // === STEP 6: Get quote for $MON → Base ETH ===
  console.log('\n--- Step 6: Getting quote for $MON → Base ETH ---');

  // Use all the $MON tokens we received (or current balance if different)
  const currentMonTokenBal = await monToken.balanceOf(walletAddress);
  const sellAmount = currentMonTokenBal > startMonTokenBal
    ? (currentMonTokenBal - startMonTokenBal).toString()
    : ethers.parseEther('500').toString(); // Fallback to 500 $MON

  const sellQuote = await getLifiQuote(
    MONAD_CHAIN_ID, BASE_CHAIN_ID,
    MON_TOKEN, NATIVE_TOKEN,
    sellAmount, walletAddress
  );

  if (sellQuote.message || sellQuote.error) {
    console.log('Sell quote error:', sellQuote.message || sellQuote.error);
    console.log('Full response:', JSON.stringify(sellQuote, null, 2));

    // Show final balances anyway
    console.log('\n--- Final Balances (Buy completed, Sell skipped) ---');
    const finalBaseBal = await baseProvider.getBalance(walletAddress);
    const finalMonTokenBal = await monToken.balanceOf(walletAddress);
    console.log('Base ETH:', ethers.formatEther(finalBaseBal));
    console.log('$MON Token:', ethers.formatEther(finalMonTokenBal));
    return;
  }

  console.log('Sell Quote:');
  console.log('  Input:', ethers.formatEther(sellQuote.estimate?.fromAmount || '0'), '$MON');
  console.log('  Output:', ethers.formatEther(sellQuote.estimate?.toAmount || '0'), 'ETH');
  console.log('  Bridge:', sellQuote.toolDetails?.name);

  // === STEP 7: Approve $MON for LI.FI ===
  console.log('\n--- Step 7: Approving $MON for LI.FI ---');
  const monTokenContract = new ethers.Contract(MON_TOKEN, [
    'function approve(address, uint256) external returns (bool)',
    'function allowance(address, address) view returns (uint256)'
  ], monadWallet);

  const approveAddress = sellQuote.estimate?.approvalAddress || sellQuote.transactionRequest?.to;
  const currentAllowance = await monTokenContract.allowance(walletAddress, approveAddress);

  if (currentAllowance < BigInt(sellAmount)) {
    console.log('Approving $MON for', approveAddress);
    const approveTx = await monTokenContract.approve(approveAddress, ethers.MaxUint256);
    console.log('Approve tx:', approveTx.hash);
    await approveTx.wait();
    console.log('Approved!');
  } else {
    console.log('Already approved');
  }

  // === STEP 8: Execute $MON → Base ETH ===
  console.log('\n--- Step 8: Executing $MON → Base ETH ---');
  const sellTx = sellQuote.transactionRequest;

  const sellTxResponse = await monadWallet.sendTransaction({
    to: sellTx.to,
    data: sellTx.data,
    value: sellTx.value || 0,
    gasLimit: sellTx.gasLimit || 500000
  });

  console.log('Tx hash:', sellTxResponse.hash);
  const sellReceipt = await sellTxResponse.wait();
  console.log('Status:', sellReceipt.status === 1 ? 'SUCCESS' : 'FAILED');
  console.log('Gas used:', sellReceipt.gasUsed.toString());

  // === STEP 9: Wait for return bridge ===
  console.log('\n--- Step 9: Waiting for return bridge ---');

  bridgeComplete = false;
  attempts = 0;

  while (!bridgeComplete && attempts < maxAttempts) {
    await sleep(5000);
    attempts++;

    try {
      const status = await checkBridgeStatus(sellTxResponse.hash, MONAD_CHAIN_ID, BASE_CHAIN_ID);
      console.log(`  Attempt ${attempts}: ${status.status || 'PENDING'}`);

      if (status.status === 'DONE') {
        bridgeComplete = true;
        console.log('✅ Return bridge completed!');
      } else if (status.status === 'FAILED') {
        console.log('❌ Return bridge failed!');
        break;
      }
    } catch (e) {
      console.log(`  Attempt ${attempts}: Checking...`);
    }
  }

  await sleep(10000);

  // === STEP 10: Final balances ===
  console.log('\n--- Step 10: Final Balances ---');
  const endBaseBal = await baseProvider.getBalance(walletAddress);
  const endMonadBal = await monadProvider.getBalance(walletAddress);
  const endMonTokenBal = await monToken.balanceOf(walletAddress);

  console.log('Base ETH:', ethers.formatEther(endBaseBal));
  console.log('Monad MON:', ethers.formatEther(endMonadBal));
  console.log('$MON Token:', ethers.formatEther(endMonTokenBal));

  // === Summary ===
  console.log('\n=== SUMMARY ===');
  const baseChange = endBaseBal - startBaseBal;
  const monTokenChange = endMonTokenBal - startMonTokenBal;

  console.log('Base ETH change:', ethers.formatEther(baseChange));
  console.log('$MON change:', ethers.formatEther(monTokenChange));

  const percentLoss = Number(ethers.formatEther(-baseChange)) / Number(ethers.formatEther(startBaseBal)) * 100;
  console.log('Round-trip cost:', percentLoss.toFixed(2), '% of starting ETH');

  console.log('\n✅ Round-trip test complete!');
}

main().catch(console.error);
