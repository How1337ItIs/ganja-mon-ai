// Test round-trip swap: $MON -> WMON -> $MON (net zero impact)
const { ethers } = require('ethers');

// Config
const MONAD_RPC = 'https://rpc.monad.xyz';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';

// Addresses on Monad
const WMON = '0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A';
const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';
const TOKEN_MILL_MARKET = '0xfB72c999dcf2BE21C5503c7e282300e28972AB1B';

const ERC20_ABI = [
  'function balanceOf(address) view returns (uint256)',
  'function approve(address spender, uint256 amount) external returns (bool)',
  'function allowance(address owner, address spender) view returns (uint256)',
];

const WMON_ABI = [
  'function deposit() external payable',
  'function withdraw(uint256 amount) external',
  'function approve(address spender, uint256 amount) external returns (bool)',
  'function balanceOf(address) view returns (uint256)',
  'function allowance(address owner, address spender) view returns (uint256)'
];

// Swap function interface
const swapInterface = new ethers.Interface([
  'function swap(address recipient, bool swapB2Q, int256 deltaAmount, uint256 maxAmount) external returns (int256, int256)'
]);

async function main() {
  console.log('=== Round-Trip Swap Test (Net Zero Impact) ===\n');

  const provider = new ethers.JsonRpcProvider(MONAD_RPC);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

  console.log('Wallet:', wallet.address);

  // Contracts
  const wmon = new ethers.Contract(WMON, WMON_ABI, wallet);
  const monToken = new ethers.Contract(MON_TOKEN, ERC20_ABI, wallet);

  // === STEP 1: Check starting balances ===
  console.log('\n--- Step 1: Starting Balances ---');
  const startNativeMon = await provider.getBalance(wallet.address);
  const startWmon = await wmon.balanceOf(wallet.address);
  const startMonToken = await monToken.balanceOf(wallet.address);

  console.log('Native MON:', ethers.formatEther(startNativeMon));
  console.log('WMON:', ethers.formatEther(startWmon));
  console.log('$MON Token:', ethers.formatEther(startMonToken));

  // Amount to test: 500 $MON (small amount to minimize impact)
  const sellAmount = ethers.parseEther('500');

  // Check we have enough $MON
  if (startMonToken < sellAmount) {
    console.error('Not enough $MON tokens for test! Need 500 $MON, have:', ethers.formatEther(startMonToken));
    return;
  }

  // Max slippage value
  const maxSlippage = BigInt('170141183460469231731687303715884105727'); // max int128

  // === STEP 2: Approve $MON for Token Mill ===
  console.log('\n--- Step 2: Approving $MON for Token Mill ---');
  const monTokenAllowance = await monToken.allowance(wallet.address, TOKEN_MILL_MARKET);
  if (monTokenAllowance < sellAmount) {
    console.log('Approving $MON...');
    const approveTx = await monToken.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
    console.log('Approve tx:', approveTx.hash);
    await approveTx.wait();
    console.log('Approved!');
  } else {
    console.log('$MON already approved');
  }

  // === STEP 3: Execute sell ($MON -> WMON) ===
  console.log('\n--- Step 3: Selling $MON for WMON ---');
  console.log('Selling:', ethers.formatEther(sellAmount), '$MON');

  // swap(recipient, swapB2Q, deltaAmount, maxAmount)
  // swapB2Q = true means selling base token ($MON) for quote token (WMON)
  const sellData = swapInterface.encodeFunctionData('swap', [
    wallet.address,  // recipient
    true,            // swapB2Q = true (sell $MON for WMON)
    sellAmount,      // deltaAmount (amount of $MON to sell)
    maxSlippage      // maxAmount (no slippage limit)
  ]);

  const sellTx = await wallet.sendTransaction({
    to: TOKEN_MILL_MARKET,
    data: sellData,
    gasLimit: 500000
  });

  console.log('Sell tx:', sellTx.hash);
  const sellReceipt = await sellTx.wait();
  console.log('Sell status:', sellReceipt.status === 1 ? 'SUCCESS' : 'FAILED');
  console.log('Gas used:', sellReceipt.gasUsed.toString());

  if (sellReceipt.status !== 1) {
    console.error('Sell transaction failed!');
    return;
  }

  // Check balances after sell
  const afterSellWmon = await wmon.balanceOf(wallet.address);
  const afterSellMonToken = await monToken.balanceOf(wallet.address);
  const wmonReceived = afterSellWmon - startWmon;

  console.log('\nAfter sell:');
  console.log('WMON balance:', ethers.formatEther(afterSellWmon));
  console.log('$MON balance:', ethers.formatEther(afterSellMonToken));
  console.log('WMON received:', ethers.formatEther(wmonReceived));

  // === STEP 4: Approve WMON for Token Mill ===
  console.log('\n--- Step 4: Approving WMON for Token Mill ---');
  const wmonAllowance = await wmon.allowance(wallet.address, TOKEN_MILL_MARKET);
  if (wmonAllowance < wmonReceived) {
    console.log('Approving WMON...');
    const approveWmonTx = await wmon.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
    console.log('Approve WMON tx:', approveWmonTx.hash);
    await approveWmonTx.wait();
    console.log('WMON Approved!');
  } else {
    console.log('WMON already approved');
  }

  // === STEP 5: Buy back $MON with WMON received ===
  console.log('\n--- Step 5: Buying $MON with WMON ---');
  console.log('Buying with:', ethers.formatEther(wmonReceived), 'WMON');

  // swapB2Q = false means buying base token ($MON) with quote token (WMON)
  const buyData = swapInterface.encodeFunctionData('swap', [
    wallet.address,  // recipient
    false,           // swapB2Q = false (buy $MON with WMON)
    wmonReceived,    // deltaAmount (amount of WMON to spend)
    maxSlippage      // maxAmount (no slippage limit)
  ]);

  const buyTx = await wallet.sendTransaction({
    to: TOKEN_MILL_MARKET,
    data: buyData,
    gasLimit: 500000
  });

  console.log('Buy tx:', buyTx.hash);
  const buyReceipt = await buyTx.wait();
  console.log('Buy status:', buyReceipt.status === 1 ? 'SUCCESS' : 'FAILED');
  console.log('Gas used:', buyReceipt.gasUsed.toString());

  // === STEP 6: Final balances and comparison ===
  console.log('\n--- Step 6: Final Balances ---');
  const endNativeMon = await provider.getBalance(wallet.address);
  const endWmon = await wmon.balanceOf(wallet.address);
  const endMonToken = await monToken.balanceOf(wallet.address);

  console.log('Native MON:', ethers.formatEther(endNativeMon));
  console.log('WMON:', ethers.formatEther(endWmon));
  console.log('$MON Token:', ethers.formatEther(endMonToken));

  console.log('\n--- Summary ---');
  const monTokenDiff = endMonToken - startMonToken;
  const wmonDiff = endWmon - startWmon;
  const nativeDiff = endNativeMon - startNativeMon;

  console.log('$MON change:', ethers.formatEther(monTokenDiff), '(', monTokenDiff >= 0 ? '+' : '', Number(ethers.formatEther(monTokenDiff)).toFixed(4), ')');
  console.log('WMON change:', ethers.formatEther(wmonDiff));
  console.log('Native MON change:', ethers.formatEther(nativeDiff), '(gas fees)');

  // Calculate net impact
  const netImpact = Number(ethers.formatEther(monTokenDiff));
  const percentImpact = (netImpact / Number(ethers.formatEther(startMonToken))) * 100;

  console.log('\n=== RESULT ===');
  console.log('Net $MON impact:', netImpact.toFixed(4), '$MON');
  console.log('Percentage impact:', percentImpact.toFixed(4), '%');
  console.log('Total gas cost:', ethers.formatEther(-nativeDiff), 'MON');

  if (Math.abs(percentImpact) < 5) {
    console.log('✅ Round-trip successful! Minimal chart impact (slippage < 5%).');
  } else {
    console.log('⚠️ Significant slippage occurred during round-trip.');
  }
}

main().catch(console.error);
