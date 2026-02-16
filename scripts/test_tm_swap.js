// Test Token Mill swap using raw transaction with manually encoded data
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
];

const WMON_ABI = [
  'function deposit() external payable',
  'function approve(address spender, uint256 amount) external returns (bool)',
  'function balanceOf(address) view returns (uint256)',
  'function allowance(address owner, address spender) view returns (uint256)'
];

async function main() {
  console.log('=== Token Mill Swap Test (Raw TX) ===\n');

  const provider = new ethers.JsonRpcProvider(MONAD_RPC);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

  console.log('Wallet:', wallet.address);

  // Check balances
  const monBalance = await provider.getBalance(wallet.address);
  console.log('Native MON balance:', ethers.formatEther(monBalance), 'MON');

  const monToken = new ethers.Contract(MON_TOKEN, ERC20_ABI, provider);
  const tokenBalance = await monToken.balanceOf(wallet.address);
  console.log('$MON token balance:', ethers.formatEther(tokenBalance), '$MON');

  const wmon = new ethers.Contract(WMON, WMON_ABI, wallet);

  try {
    // Swap amount - 5 WMON
    const wmonAmount = ethers.parseEther('5');

    // Check WMON balance
    const wmonBalance = await wmon.balanceOf(wallet.address);
    console.log('\nCurrent WMON balance:', ethers.formatEther(wmonBalance));

    // Wrap MON if needed
    if (wmonBalance < wmonAmount) {
      console.log('Wrapping 5 MON to WMON...');
      const wrapTx = await wmon.deposit({ value: wmonAmount });
      console.log('Wrap tx:', wrapTx.hash);
      await wrapTx.wait();
      console.log('Wrapped!');
    }

    // Approve WMON for market
    const allowance = await wmon.allowance(wallet.address, TOKEN_MILL_MARKET);
    console.log('WMON allowance for market:', ethers.formatEther(allowance));

    if (allowance < wmonAmount) {
      console.log('Approving WMON for market...');
      const approveTx = await wmon.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
      console.log('Approve tx:', approveTx.hash);
      await approveTx.wait();
      console.log('Approved!');
    }

    // Manually encode the swap function call
    // swap(address recipient, bool swapB2Q, int256 deltaAmount, uint256 maxAmount)
    // MethodID: 0xabb1db2a
    const swapInterface = new ethers.Interface([
      'function swap(address recipient, bool swapB2Q, int256 deltaAmount, uint256 maxAmount) external returns (int256, int256)'
    ]);

    const maxSlippage = BigInt('170141183460469231731687303715884105727'); // max int128

    const swapData = swapInterface.encodeFunctionData('swap', [
      wallet.address,  // recipient
      false,           // swapB2Q = false (buy tokens)
      wmonAmount,      // deltaAmount (5 WMON)
      maxSlippage      // maxAmount (no slippage limit)
    ]);

    console.log('\n--- Executing swap ---');
    console.log('Encoded data:', swapData.slice(0, 10) + '...');
    console.log('Swapping 5 WMON for $MON tokens...');

    // Send raw transaction
    const tx = await wallet.sendTransaction({
      to: TOKEN_MILL_MARKET,
      data: swapData,
      gasLimit: 400000
    });

    console.log('Swap tx:', tx.hash);
    const receipt = await tx.wait();
    console.log('Transaction status:', receipt.status === 1 ? 'SUCCESS' : 'FAILED');
    console.log('Gas used:', receipt.gasUsed.toString());

    if (receipt.status === 1) {
      // Check final balances
      const newTokenBalance = await monToken.balanceOf(wallet.address);
      const newWmonBalance = await wmon.balanceOf(wallet.address);
      console.log('\n--- Final Balances ---');
      console.log('$MON tokens:', ethers.formatEther(newTokenBalance));
      console.log('WMON:', ethers.formatEther(newWmonBalance));
      console.log('Tokens received:', ethers.formatEther(newTokenBalance - tokenBalance));
    }

  } catch (error) {
    console.error('\nError:', error.message);
    if (error.receipt) {
      console.error('Tx hash:', error.receipt.hash);
      console.error('Status:', error.receipt.status);
    }
  }
}

main().catch(console.error);
