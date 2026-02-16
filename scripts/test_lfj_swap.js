// Test LFJ swap using JoeAggregatorRouter
const { ethers } = require('ethers');

// Config - use public Monad RPC
const MONAD_RPC = 'https://rpc.monad.xyz';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';

// Addresses
const JOE_AGGREGATOR_ROUTER = '0x45A62B090DF48243F12A21897e7ed91863E2c86b';
const WMON = '0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A';
const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';
const TOKEN_MILL_MARKET = '0xfB72c999dcf2BE21C5503c7e282300e28972AB1B';

// ABIs
const AGGREGATOR_ABI = [
  'function swapExactIn(address tokenOut, address tokenIn, address aggregator, uint256 amountIn, uint256 minAmountOut, address recipient, uint256 deadline, bytes calldata route) external payable returns (uint256 amountOut)'
];

const ERC20_ABI = [
  'function balanceOf(address) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)'
];

async function main() {
  console.log('=== LFJ Swap Test ===\n');

  const provider = new ethers.JsonRpcProvider(MONAD_RPC);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

  console.log('Wallet:', wallet.address);

  // Check balances
  const monBalance = await provider.getBalance(wallet.address);
  console.log('Native MON balance:', ethers.formatEther(monBalance), 'MON');

  const monToken = new ethers.Contract(MON_TOKEN, ERC20_ABI, provider);
  const tokenBalance = await monToken.balanceOf(wallet.address);
  console.log('$MON token balance:', ethers.formatEther(tokenBalance), '$MON');

  // Swap parameters
  const amountIn = ethers.parseEther('10'); // 10 MON
  const minAmountOut = 0; // No slippage protection for testing
  const deadline = Math.floor(Date.now() / 1000) + 3600; // 1 hour

  console.log('\n--- Executing swap ---');
  console.log('Input: 10 native MON');
  console.log('Output: $MON token');

  // The route needs to encode the path: native MON -> WMON -> Token Mill Market -> MON token
  // Based on the successful tx, the route format is complex
  // Let's try a simpler direct approach first using the Token Mill market

  // Actually let's check the Token Mill market interface directly
  const TOKEN_MILL_MARKET_ABI = [
    'function buy(address recipient, uint256 amountIn, uint256 minAmountOut) external returns (uint256)',
    'function getQuote(uint256 amountIn, bool isBuy) external view returns (uint256)',
    'function baseToken() external view returns (address)',
    'function quoteToken() external view returns (address)'
  ];

  const market = new ethers.Contract(TOKEN_MILL_MARKET, TOKEN_MILL_MARKET_ABI, wallet);

  // Check market info
  try {
    const baseToken = await market.baseToken();
    const quoteToken = await market.quoteToken();
    console.log('\nMarket base token:', baseToken);
    console.log('Market quote token:', quoteToken);

    // Get a quote for 10 WMON
    const quote = await market.getQuote(ethers.parseEther('10'), true);
    console.log('Quote for 10 WMON:', ethers.formatEther(quote), '$MON');

    // We need to wrap MON to WMON first
    const WMON_ABI = [
      'function deposit() external payable',
      'function approve(address spender, uint256 amount) external returns (bool)',
      'function balanceOf(address) view returns (uint256)'
    ];

    const wmon = new ethers.Contract(WMON, WMON_ABI, wallet);

    // Check WMON balance
    const wmonBalance = await wmon.balanceOf(wallet.address);
    console.log('\nCurrent WMON balance:', ethers.formatEther(wmonBalance), 'WMON');

    // If we don't have enough WMON, wrap some MON
    if (wmonBalance < amountIn) {
      console.log('\nWrapping 10 MON to WMON...');
      const wrapTx = await wmon.deposit({ value: amountIn });
      console.log('Wrap tx:', wrapTx.hash);
      await wrapTx.wait();
      console.log('Wrapped successfully!');

      const newWmonBalance = await wmon.balanceOf(wallet.address);
      console.log('New WMON balance:', ethers.formatEther(newWmonBalance), 'WMON');
    }

    // Approve WMON for the market
    console.log('\nApproving WMON for Token Mill market...');
    const approveTx = await wmon.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
    console.log('Approve tx:', approveTx.hash);
    await approveTx.wait();
    console.log('Approved!');

    // Now buy tokens from the market
    console.log('\nBuying $MON tokens...');
    const buyTx = await market.buy(wallet.address, amountIn, 0);
    console.log('Buy tx:', buyTx.hash);
    const receipt = await buyTx.wait();
    console.log('Buy successful!');
    console.log('Gas used:', receipt.gasUsed.toString());

    // Check new balance
    const newTokenBalance = await monToken.balanceOf(wallet.address);
    console.log('\nNew $MON token balance:', ethers.formatEther(newTokenBalance), '$MON');
    console.log('Tokens received:', ethers.formatEther(newTokenBalance - tokenBalance), '$MON');

  } catch (error) {
    console.error('\nError:', error.message);
    if (error.data) {
      console.error('Error data:', error.data);
    }
  }
}

main().catch(console.error);
