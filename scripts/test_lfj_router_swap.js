// Test LFJ swap using JoeAggregatorRouter - the correct approach
const { ethers } = require('ethers');

// Config
const MONAD_RPC = 'https://rpc.monad.xyz';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';

// Addresses
const JOE_AGGREGATOR_ROUTER = '0x45A62B090DF48243F12A21897e7ed91863E2c86b';
const WMON = '0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A';
const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';
const TOKEN_MILL_MARKET = '0xfB72c999dcf2BE21C5503c7e282300e28972AB1B';
const NATIVE_TOKEN = '0x0000000000000000000000000000000000000000';

// JoeAggregatorRouter ABI (from successful tx analysis)
const AGGREGATOR_ABI = [
  'function swapExactIn(address tokenOut, address tokenIn, address aggregator, uint256 amountIn, uint256 minAmountOut, address recipient, uint256 deadline, bytes calldata route) external payable returns (uint256 amountOut)'
];

const ERC20_ABI = [
  'function balanceOf(address) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)'
];

// Helper to encode route for Token Mill swap
// Based on successful tx: 0x04003bd359c1119da7da1d913d1c4d2b7c461115433a0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b...
function encodeSimpleRoute() {
  // The route encodes the path through Token Mill
  // Format observed: starts with version/type, then includes token addresses and pool info

  // Simplified route for direct WMON -> MON token via Token Mill market
  // This is a minimal route encoding based on the pattern observed
  const routeBuilder = new ethers.AbiCoder();

  // Based on analysis, the route contains:
  // - Pool type indicators
  // - Token addresses
  // - Pool addresses
  // Let's try a minimal route that just specifies the market

  // Actually, let's try the simplest possible encoding first
  // The aggregator might auto-detect the route if we just specify tokens
  return '0x';
}

async function main() {
  console.log('=== LFJ Router Swap Test ===\n');

  const provider = new ethers.JsonRpcProvider(MONAD_RPC);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

  console.log('Wallet:', wallet.address);

  // Check balances
  const monBalance = await provider.getBalance(wallet.address);
  console.log('Native MON balance:', ethers.formatEther(monBalance), 'MON');

  const monToken = new ethers.Contract(MON_TOKEN, ERC20_ABI, provider);
  const tokenBalance = await monToken.balanceOf(wallet.address);
  console.log('$MON token balance:', ethers.formatEther(tokenBalance), '$MON');

  // For Token Mill swaps, the LFJ frontend uses their API to get quotes and routes
  // Let's try using the LFJ API instead of encoding manually

  console.log('\n--- Fetching quote from LFJ API ---');

  const amountIn = ethers.parseEther('5'); // 5 MON

  // LFJ uses their own API for quotes. Let's try their swap API
  const quoteUrl = `https://api.lfj.gg/v1/monad/quote?` + new URLSearchParams({
    fromToken: NATIVE_TOKEN,
    toToken: MON_TOKEN,
    amount: amountIn.toString(),
    slippage: '100', // 1% in bps
    sender: wallet.address
  });

  console.log('Fetching quote from:', quoteUrl);

  try {
    const response = await fetch(quoteUrl);
    const quoteData = await response.json();
    console.log('Quote response:', JSON.stringify(quoteData, null, 2));

    if (quoteData.tx) {
      console.log('\n--- Executing swap via LFJ quote ---');
      const tx = await wallet.sendTransaction({
        to: quoteData.tx.to,
        data: quoteData.tx.data,
        value: quoteData.tx.value || amountIn,
        gasLimit: quoteData.tx.gasLimit || 500000
      });
      console.log('Tx hash:', tx.hash);
      const receipt = await tx.wait();
      console.log('Swap successful! Gas used:', receipt.gasUsed.toString());

      // Check new balance
      const newTokenBalance = await monToken.balanceOf(wallet.address);
      console.log('\nNew $MON token balance:', ethers.formatEther(newTokenBalance), '$MON');
    }
  } catch (error) {
    console.log('LFJ API error:', error.message);

    // Fallback: Try 0x API which is often used for DEX aggregation
    console.log('\n--- Trying 0x API fallback ---');

    const zeroXUrl = `https://monad.api.0x.org/swap/v1/quote?` + new URLSearchParams({
      sellToken: 'ETH', // Native token
      buyToken: MON_TOKEN,
      sellAmount: amountIn.toString(),
      takerAddress: wallet.address
    });

    try {
      const zeroXResponse = await fetch(zeroXUrl, {
        headers: { '0x-api-key': '' } // May need API key
      });
      const zeroXData = await zeroXResponse.json();
      console.log('0x response:', JSON.stringify(zeroXData, null, 2));
    } catch (e) {
      console.log('0x API also failed:', e.message);
    }
  }

  // Alternative: Manually construct a swap through Token Mill
  // The Token Mill market has a buy function that takes WMON
  // We need to:
  // 1. Wrap MON to WMON
  // 2. Approve WMON for market
  // 3. Call market.buy()

  console.log('\n--- Attempting direct Token Mill swap ---');

  const WMON_ABI = [
    'function deposit() external payable',
    'function approve(address spender, uint256 amount) external returns (bool)',
    'function balanceOf(address) view returns (uint256)',
    'function allowance(address owner, address spender) view returns (uint256)'
  ];

  // Based on the actual Token Mill market proxy, let's get the correct ABI
  // The market is a proxy to implementation at 0xCff395d373b27F6Eb88FB005e13d9314C61bC02D
  const TOKEN_MILL_ABI = [
    'function buy(address recipient, uint256 amountIn, uint256 minAmountOut) external returns (uint256)',
    'function sell(address recipient, uint256 amountIn, uint256 minAmountOut) external returns (uint256)',
    'function getQuoteBuy(uint256 amountIn) external view returns (uint256)',
    'function getQuoteSell(uint256 amountIn) external view returns (uint256)',
    'function token() external view returns (address)',
    'function quoteToken() external view returns (address)'
  ];

  const wmon = new ethers.Contract(WMON, WMON_ABI, wallet);
  const market = new ethers.Contract(TOKEN_MILL_MARKET, TOKEN_MILL_ABI, wallet);

  try {
    // Check market info
    const tokenAddr = await market.token();
    const quoteTokenAddr = await market.quoteToken();
    console.log('Market token:', tokenAddr);
    console.log('Market quote token:', quoteTokenAddr);

    // Get quote
    const wmonAmount = ethers.parseEther('5');
    const quote = await market.getQuoteBuy(wmonAmount);
    console.log('Quote for 5 WMON:', ethers.formatEther(quote), '$MON tokens');

    // Check WMON balance
    const wmonBalance = await wmon.balanceOf(wallet.address);
    console.log('Current WMON balance:', ethers.formatEther(wmonBalance));

    // Wrap MON if needed
    if (wmonBalance < wmonAmount) {
      console.log('\nWrapping 5 MON to WMON...');
      const wrapTx = await wmon.deposit({ value: wmonAmount });
      console.log('Wrap tx:', wrapTx.hash);
      await wrapTx.wait();
      console.log('Wrapped!');
    }

    // Check allowance
    const allowance = await wmon.allowance(wallet.address, TOKEN_MILL_MARKET);
    console.log('WMON allowance for market:', ethers.formatEther(allowance));

    // Approve if needed
    if (allowance < wmonAmount) {
      console.log('\nApproving WMON for market...');
      const approveTx = await wmon.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
      console.log('Approve tx:', approveTx.hash);
      await approveTx.wait();
      console.log('Approved!');
    }

    // Execute buy
    console.log('\nExecuting buy...');
    const buyTx = await market.buy(wallet.address, wmonAmount, 0, {
      gasLimit: 500000
    });
    console.log('Buy tx:', buyTx.hash);
    const receipt = await buyTx.wait();
    console.log('Buy successful! Gas used:', receipt.gasUsed.toString());

    // Check new balances
    const newTokenBalance = await monToken.balanceOf(wallet.address);
    const newWmonBalance = await wmon.balanceOf(wallet.address);
    console.log('\nFinal $MON token balance:', ethers.formatEther(newTokenBalance), '$MON');
    console.log('Final WMON balance:', ethers.formatEther(newWmonBalance), 'WMON');

  } catch (error) {
    console.error('\nError:', error.message);
    if (error.data) {
      console.error('Error data:', error.data);
    }
    // Try to decode error
    if (error.reason) {
      console.error('Reason:', error.reason);
    }
  }
}

main().catch(console.error);
