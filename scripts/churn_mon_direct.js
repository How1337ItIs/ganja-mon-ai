// Churn script v2: Direct Token Mill swaps (NO LI.FI API - no rate limits!)
// Swaps $MON <-> native MON using direct contract calls
const { ethers } = require('ethers');

const MONAD_RPC = 'https://rpc.monad.xyz';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';

// Contract addresses
const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';
const WMON = '0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A';
const TOKEN_MILL_MARKET = '0xfB72c999dcf2BE21C5503c7e282300e28972AB1B';

// Thresholds
const GAS_RESERVE = ethers.parseEther('5');      // Keep 5 MON for gas
const MIN_MON_TOKEN = ethers.parseEther('100');  // Stop if $MON < 100
const MIN_NATIVE_MON = ethers.parseEther('1');   // Stop if native MON < 1

// Max slippage for Token Mill
const MAX_SLIPPAGE = BigInt('170141183460469231731687303715884105727');

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function retryRpc(fn, retries = 5) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (err) {
            if (i < retries - 1) {
                console.log(`  RPC error, retrying in ${(i + 1) * 2}s...`);
                await sleep((i + 1) * 2000);
            } else {
                throw err;
            }
        }
    }
}

async function getBalances(provider, walletAddress, monTokenContract, wmonContract) {
    const native = await retryRpc(() => provider.getBalance(walletAddress));
    await sleep(300);
    const monToken = await retryRpc(() => monTokenContract.balanceOf(walletAddress));
    await sleep(300);
    const wmon = await retryRpc(() => wmonContract.balanceOf(walletAddress));
    return { native, monToken, wmon };
}

async function main() {
    const provider = new ethers.JsonRpcProvider(MONAD_RPC);
    const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
    const walletAddress = wallet.address;

    // Contract instances
    const monTokenContract = new ethers.Contract(MON_TOKEN, [
        'function balanceOf(address) view returns (uint256)',
        'function approve(address, uint256) external returns (bool)',
        'function allowance(address, address) view returns (uint256)',
    ], wallet);

    const wmonContract = new ethers.Contract(WMON, [
        'function deposit() external payable',
        'function withdraw(uint256 amount) external',
        'function balanceOf(address) view returns (uint256)',
        'function approve(address, uint256) external returns (bool)',
        'function allowance(address, address) view returns (uint256)',
    ], wallet);

    // Token Mill swap interface
    const swapInterface = new ethers.Interface([
        'function swap(address recipient, bool swapB2Q, int256 deltaAmount, uint256 maxAmount) external returns (int256, int256)'
    ]);

    console.log('=== $MON DIRECT CHURN BOT (v2) ===');
    console.log('Wallet:', walletAddress);
    console.log('Strategy: Direct Token Mill swaps (no LI.FI API)');
    console.log('Gas reserve:', ethers.formatEther(GAS_RESERVE), 'MON');
    console.log('');

    // === ONE-TIME SETUP: Approve tokens for Token Mill ===
    console.log('--- Setup: Checking approvals ---');

    // Approve $MON if needed
    const monAllowance = await monTokenContract.allowance(walletAddress, TOKEN_MILL_MARKET);
    if (monAllowance < ethers.parseEther('1000000')) {
        console.log('Approving $MON for Token Mill...');
        const approveTx = await monTokenContract.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
        await approveTx.wait();
        console.log('$MON approved!');
    }

    // Approve WMON if needed
    const wmonAllowance = await wmonContract.allowance(walletAddress, TOKEN_MILL_MARKET);
    if (wmonAllowance < ethers.parseEther('1000000')) {
        console.log('Approving WMON for Token Mill...');
        const approveWmonTx = await wmonContract.approve(TOKEN_MILL_MARKET, ethers.MaxUint256);
        await approveWmonTx.wait();
        console.log('WMON approved!');
    }

    let round = 0;

    while (true) {
        round++;
        const bal = await getBalances(provider, walletAddress, monTokenContract, wmonContract);
        console.log(`\n========== ROUND ${round} ==========`);
        console.log('Native MON:', ethers.formatEther(bal.native));
        console.log('$MON Token:', ethers.formatEther(bal.monToken));
        console.log('WMON:', ethers.formatEther(bal.wmon));

        // === STEP A: Sell ALL $MON for WMON (direct Token Mill) ===
        if (bal.monToken > MIN_MON_TOKEN) {
            console.log('\n--- Selling ALL $MON → WMON (direct) ---');
            const sellAmount = bal.monToken;
            console.log('Selling:', ethers.formatEther(sellAmount), '$MON');

            try {
                // swap(recipient, swapB2Q=true, deltaAmount=$MON amount, maxAmount)
                const sellData = swapInterface.encodeFunctionData('swap', [
                    walletAddress,
                    true,        // swapB2Q = true (sell $MON for WMON)
                    sellAmount,
                    MAX_SLIPPAGE
                ]);

                const sellTx = await wallet.sendTransaction({
                    to: TOKEN_MILL_MARKET,
                    data: sellData,
                    gasLimit: 500000
                });

                console.log('Sell tx:', sellTx.hash);
                const sellReceipt = await sellTx.wait();
                console.log('Status:', sellReceipt.status === 1 ? 'SUCCESS' : 'FAILED');

                if (sellReceipt.status !== 1) {
                    console.log('Sell failed! Stopping.');
                    break;
                }

                await sleep(2000);
            } catch (err) {
                console.log('Sell error:', err.message);
                console.log('Waiting 10s and retrying...');
                await sleep(10000);
                continue;
            }
        } else {
            console.log('$MON balance too low to sell. Skipping sell step.');
        }

        // Check balances after sell
        const afterSellBal = await getBalances(provider, walletAddress, monTokenContract, wmonContract);
        console.log('\nAfter sell:');
        console.log('Native MON:', ethers.formatEther(afterSellBal.native));
        console.log('WMON:', ethers.formatEther(afterSellBal.wmon));

        // === STEP B: Buy $MON with ALL WMON ===
        // First, wrap any native MON (minus gas reserve) to WMON
        const availableNative = afterSellBal.native - GAS_RESERVE;
        if (availableNative > ethers.parseEther('1')) {
            console.log('\n--- Wrapping native MON → WMON ---');
            console.log('Wrapping:', ethers.formatEther(availableNative), 'MON');

            try {
                const wrapTx = await wmonContract.deposit({ value: availableNative });
                console.log('Wrap tx:', wrapTx.hash);
                await wrapTx.wait();
                console.log('Wrapped!');
                await sleep(2000);
            } catch (err) {
                console.log('Wrap error:', err.message);
            }
        }

        // Get fresh WMON balance
        const wmonBal = await wmonContract.balanceOf(walletAddress);
        console.log('\nTotal WMON for buy:', ethers.formatEther(wmonBal));

        if (wmonBal > MIN_NATIVE_MON) {
            console.log('\n--- Buying $MON with ALL WMON (direct) ---');

            try {
                // swap(recipient, swapB2Q=false, deltaAmount=WMON amount, maxAmount)
                const buyData = swapInterface.encodeFunctionData('swap', [
                    walletAddress,
                    false,       // swapB2Q = false (buy $MON with WMON)
                    wmonBal,
                    MAX_SLIPPAGE
                ]);

                const buyTx = await wallet.sendTransaction({
                    to: TOKEN_MILL_MARKET,
                    data: buyData,
                    gasLimit: 500000
                });

                console.log('Buy tx:', buyTx.hash);
                const buyReceipt = await buyTx.wait();
                console.log('Status:', buyReceipt.status === 1 ? 'SUCCESS' : 'FAILED');

                if (buyReceipt.status !== 1) {
                    console.log('Buy failed! Stopping.');
                    break;
                }

                await sleep(2000);
            } catch (err) {
                console.log('Buy error:', err.message);
                console.log('Waiting 10s and retrying...');
                await sleep(10000);
                continue;
            }
        } else {
            console.log('Not enough WMON to buy. Funds exhausted!');
            break;
        }

        // Final balances for this round
        const endBal = await getBalances(provider, walletAddress, monTokenContract, wmonContract);
        console.log(`\n--- Round ${round} Complete ---`);
        console.log('Native MON:', ethers.formatEther(endBal.native));
        console.log('$MON Token:', ethers.formatEther(endBal.monToken));
        console.log('WMON:', ethers.formatEther(endBal.wmon));

        // Check if we should continue
        if (endBal.monToken < MIN_MON_TOKEN && (endBal.native - GAS_RESERVE) < MIN_NATIVE_MON) {
            console.log('\nBoth balances too low. Funds exhausted!');
            break;
        }

        // Safety: max 500 rounds
        if (round >= 500) {
            console.log('\nMax rounds reached. Stopping.');
            break;
        }

        // Short delay between rounds (no rate limits to worry about!)
        console.log('\nWaiting 5s before next round...');
        await sleep(5000);
    }

    // Final summary
    const finalBal = await getBalances(provider, walletAddress, monTokenContract, wmonContract);
    console.log('\n\n========== FINAL SUMMARY ==========');
    console.log('Native MON:', ethers.formatEther(finalBal.native));
    console.log('$MON Token:', ethers.formatEther(finalBal.monToken));
    console.log('WMON:', ethers.formatEther(finalBal.wmon));
    console.log(`Completed ${round} rounds of churning.`);
    console.log('====================================');
}

main().catch(console.error);
