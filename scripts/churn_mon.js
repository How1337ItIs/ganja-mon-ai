// Churn script: Swap $MON <-> native MON back and forth until fees eat all funds
const { ethers } = require('ethers');

const MONAD_RPC = 'https://rpc.monad.xyz';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';
const LIFI_API = 'https://li.quest/v1';
const MONAD_CHAIN_ID = 143; // LI.FI uses 143 for Monad

const MON_TOKEN = '0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b';
const NATIVE = '0x0000000000000000000000000000000000000000';
const WMON = '0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A';

const GAS_RESERVE = ethers.parseEther('5'); // Keep 5 MON for gas
const MIN_MON_TOKEN = ethers.parseEther('100'); // Stop if $MON < 100
const MIN_NATIVE_MON = ethers.parseEther('0.5'); // Stop if native MON < 0.5

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function retryRpc(fn, retries = 5) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (err) {
            if (err.message && err.message.includes('request limit reached') && i < retries - 1) {
                console.log(`  RPC rate limited, waiting ${(i + 1) * 3}s...`);
                await sleep((i + 1) * 3000);
            } else if (i < retries - 1) {
                console.log(`  RPC error, retrying in ${(i + 1) * 2}s...`);
                await sleep((i + 1) * 2000);
            } else {
                throw err;
            }
        }
    }
}

async function getBalances(provider, wallet, monTokenContract) {
    const native = await retryRpc(() => provider.getBalance(wallet));
    await sleep(500);
    const monToken = await retryRpc(() => monTokenContract.balanceOf(wallet));
    return { native, monToken };
}

async function getLifiQuote(fromToken, toToken, amount, walletAddress) {
    const params = new URLSearchParams({
        fromChain: MONAD_CHAIN_ID.toString(),
        toChain: MONAD_CHAIN_ID.toString(),
        fromToken,
        toToken,
        fromAmount: amount.toString(),
        fromAddress: walletAddress,
        toAddress: walletAddress,
        slippage: '0.05', // 5% slippage
    });

    const res = await fetch(`${LIFI_API}/quote?${params}`);
    return await res.json();
}

// Wrapper that retries on LI.FI rate limits
async function getLifiQuoteWithRetry(fromToken, toToken, amount, walletAddress, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        const quote = await getLifiQuote(fromToken, toToken, amount, walletAddress);

        const msg = quote.message || '';
        if (msg.includes('Rate limit exceeded') || msg.includes('rate limit')) {
            // Parse "retry in X minutes" from message
            const match = msg.match(/retry in (\d+) minutes/i);
            const waitMinutes = match ? parseInt(match[1]) : 10;
            // Add 2 extra minutes buffer
            const waitMs = (waitMinutes + 2) * 60 * 1000;
            console.log(`  LI.FI rate limited! Waiting ${waitMinutes + 2} minutes before retry (attempt ${attempt + 1}/${maxRetries})...`);
            await sleep(waitMs);
            continue;
        }

        return quote;
    }
    // Return last failed quote after all retries
    return { message: 'Rate limit retries exhausted' };
}

async function main() {
    const provider = new ethers.JsonRpcProvider(MONAD_RPC);
    const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
    const walletAddress = wallet.address;

    const monTokenContract = new ethers.Contract(MON_TOKEN, [
        'function balanceOf(address) view returns (uint256)',
        'function approve(address, uint256) external returns (bool)',
        'function allowance(address, address) view returns (uint256)',
    ], wallet);

    console.log('=== $MON CHURN BOT ===');
    console.log('Wallet:', walletAddress);
    console.log('Strategy: Sell $MON → MON → Buy $MON → repeat until broke');
    console.log('Gas reserve:', ethers.formatEther(GAS_RESERVE), 'MON');
    console.log('');

    let round = 0;

    while (true) {
        round++;
        const bal = await getBalances(provider, walletAddress, monTokenContract);
        console.log(`\n========== ROUND ${round} ==========`);
        console.log('Native MON:', ethers.formatEther(bal.native));
        console.log('$MON Token:', ethers.formatEther(bal.monToken));

        // === STEP A: Sell $MON for native MON ===
        if (bal.monToken > MIN_MON_TOKEN) {
            console.log('\n--- Selling $MON → native MON ---');
            const sellAmount = bal.monToken; // Sell everything

            try {
                const sellQuote = await getLifiQuoteWithRetry(MON_TOKEN, NATIVE, sellAmount.toString(), walletAddress);

                if (sellQuote.message || sellQuote.code) {
                    console.log('Sell quote failed:', sellQuote.message || sellQuote.code);
                    console.log('Waiting 60s and retrying round...');
                    await sleep(60000);
                    continue;
                }

                const outputMon = parseFloat(ethers.formatEther(sellQuote.estimate?.toAmount || '0'));
                console.log(`Selling ${ethers.formatEther(sellAmount)} $MON → ~${outputMon.toFixed(4)} MON`);

                // Approve if needed
                const approvalAddr = sellQuote.estimate?.approvalAddress || sellQuote.transactionRequest?.to;
                if (approvalAddr) {
                    const allowance = await monTokenContract.allowance(walletAddress, approvalAddr);
                    if (allowance < sellAmount) {
                        console.log('Approving $MON for', approvalAddr);
                        const approveTx = await monTokenContract.approve(approvalAddr, ethers.MaxUint256);
                        await approveTx.wait();
                        console.log('Approved!');
                    }
                }

                // Execute sell
                const tx = sellQuote.transactionRequest;
                console.log('Executing sell...');
                const sellTx = await wallet.sendTransaction({
                    to: tx.to,
                    data: tx.data,
                    value: tx.value || 0,
                    gasLimit: tx.gasLimit || 500000,
                });
                console.log('Tx:', sellTx.hash);
                await sleep(3000); // Wait before polling receipt
                const receipt = await retryRpc(() => sellTx.wait());
                console.log('Status:', receipt.status === 1 ? 'SUCCESS' : 'FAILED');

                if (receipt.status !== 1) {
                    console.log('Sell failed! Stopping.');
                    break;
                }

                await sleep(5000); // Wait for balance update
            } catch (err) {
                console.log('Sell error:', err.message);
                console.log('Waiting 30s and retrying...');
                await sleep(30000);
                continue;
            }
        } else {
            console.log('$MON balance too low to sell. Skipping sell step.');
        }

        // Check updated balances
        const midBal = await getBalances(provider, walletAddress, monTokenContract);
        console.log('\nAfter sell:');
        console.log('Native MON:', ethers.formatEther(midBal.native));
        console.log('$MON Token:', ethers.formatEther(midBal.monToken));

        // === STEP B: Buy $MON with native MON (ALL AT ONCE - bigger swaps!) ===
        const MAX_BUY_CHUNK = ethers.parseEther('9999999'); // No limit - buy all at once
        let availableForBuy = midBal.native - GAS_RESERVE;
        if (availableForBuy > MIN_NATIVE_MON) {
            console.log('\n--- Buying $MON with native MON ---');
            console.log(`Total available: ${ethers.formatEther(availableForBuy)} MON (keeping ${ethers.formatEther(GAS_RESERVE)} for gas)`);

            let buyChunkNum = 0;
            let consecutiveFailures = 0;
            while (availableForBuy > MIN_NATIVE_MON) {
                buyChunkNum++;
                if (consecutiveFailures >= 5) {
                    console.log('  Too many consecutive failures, moving to next round...');
                    break;
                }
                const chunkAmount = availableForBuy > MAX_BUY_CHUNK ? MAX_BUY_CHUNK : availableForBuy;
                console.log(`\n  Buy chunk ${buyChunkNum}: ${ethers.formatEther(chunkAmount)} MON`);

                try {
                    const buyQuote = await getLifiQuoteWithRetry(NATIVE, MON_TOKEN, chunkAmount.toString(), walletAddress);

                    if (buyQuote.message || buyQuote.code) {
                        console.log('  Buy quote failed:', buyQuote.message || buyQuote.code);
                        consecutiveFailures++;
                        console.log('  Waiting 60s before retrying chunk...');
                        await sleep(60000);
                        continue;
                    }

                    const outputMonToken = parseFloat(ethers.formatEther(buyQuote.estimate?.toAmount || '0'));
                    console.log(`  Buying ~${outputMonToken.toFixed(0)} $MON`);

                    const tx = buyQuote.transactionRequest;
                    const buyTx = await wallet.sendTransaction({
                        to: tx.to,
                        data: tx.data,
                        value: tx.value,
                        gasLimit: tx.gasLimit || 500000,
                    });
                    console.log('  Tx:', buyTx.hash);
                    await sleep(3000);
                    const receipt = await retryRpc(() => buyTx.wait());
                    console.log('  Status:', receipt.status === 1 ? 'SUCCESS' : 'FAILED');

                    if (receipt.status !== 1) {
                        console.log('  Buy chunk failed!');
                        consecutiveFailures++;
                        break;
                    }

                    consecutiveFailures = 0; // Reset on success
                    await sleep(5000);
                    // Update available balance
                    const freshBal = await retryRpc(() => provider.getBalance(walletAddress));
                    availableForBuy = freshBal - GAS_RESERVE;
                } catch (err) {
                    console.log('  Buy chunk error:', err.message);
                    consecutiveFailures++;
                    console.log('  Waiting 15s before retrying...');
                    await sleep(15000);
                    // Refresh balance and retry
                    const freshBal = await retryRpc(() => provider.getBalance(walletAddress));
                    availableForBuy = freshBal - GAS_RESERVE;
                }
            }
        } else {
            console.log('Not enough native MON to buy (need >', ethers.formatEther(GAS_RESERVE + MIN_NATIVE_MON), 'MON)');
            console.log('Funds exhausted!');
            break;
        }

        // Final balances for this round
        const endBal = await getBalances(provider, walletAddress, monTokenContract);
        console.log(`\n--- Round ${round} Complete ---`);
        console.log('Native MON:', ethers.formatEther(endBal.native));
        console.log('$MON Token:', ethers.formatEther(endBal.monToken));

        // Check if we should continue
        if (endBal.monToken < MIN_MON_TOKEN && (endBal.native - GAS_RESERVE) < MIN_NATIVE_MON) {
            console.log('\nBoth balances too low. Funds exhausted!');
            break;
        }

        // Safety: max 200 rounds
        if (round >= 200) {
            console.log('\nMax rounds reached. Stopping.');
            break;
        }

        console.log('\nWaiting 90s before next round...');
        await sleep(90000);
    }

    // Final summary
    const finalBal = await getBalances(provider, walletAddress, monTokenContract);
    console.log('\n\n========== FINAL SUMMARY ==========');
    console.log('Native MON:', ethers.formatEther(finalBal.native));
    console.log('$MON Token:', ethers.formatEther(finalBal.monToken));
    console.log(`Completed ${round} rounds of churning.`);
    console.log('====================================');
}

main().catch(console.error);
