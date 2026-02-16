// Test deBridge bridge: Monad → Solana
const { ethers } = require('ethers');

// Config
const MONAD_RPC = 'https://monad.drpc.org';
const PRIVATE_KEY = '0xeb51e1b9bd8f8b0661277e087d30a98dda507af8eddd196e7c38db46917f7cb8';

// Test wallet
const WALLET_ADDRESS = '0xF909fF1806DbdffEfB7687754eA7a28085d4a80b';

// deBridge chain IDs
const DEBRIDGE_MONAD_CHAIN_ID = 100000030;
const DEBRIDGE_SOLANA_CHAIN_ID = 7565164;

// Native token addresses
const MONAD_NATIVE = '0x0000000000000000000000000000000000000000';
const SOLANA_NATIVE = '11111111111111111111111111111111';

async function getDebridgeQuote(srcChain, dstChain, srcToken, dstToken, amount) {
    const url = new URL('https://api.dln.trade/v1.0/dln/order/quote');
    url.searchParams.append('srcChainId', srcChain);
    url.searchParams.append('srcChainTokenIn', srcToken);
    url.searchParams.append('srcChainTokenInAmount', amount);
    url.searchParams.append('dstChainId', dstChain);
    url.searchParams.append('dstChainTokenOut', dstToken);
    url.searchParams.append('prependOperatingExpenses', 'false');

    const response = await fetch(url);
    return await response.json();
}

async function getDebridgeTransaction(srcChain, dstChain, srcToken, dstToken, amount, srcAddress, dstAddress) {
    const url = new URL('https://api.dln.trade/v1.0/dln/order/create-tx');
    url.searchParams.append('srcChainId', srcChain);
    url.searchParams.append('srcChainTokenIn', srcToken);
    url.searchParams.append('srcChainTokenInAmount', amount);
    url.searchParams.append('dstChainId', dstChain);
    url.searchParams.append('dstChainTokenOut', dstToken);
    url.searchParams.append('dstChainTokenOutRecipient', dstAddress);
    url.searchParams.append('srcChainOrderAuthorityAddress', srcAddress);
    url.searchParams.append('dstChainOrderAuthorityAddress', dstAddress);
    url.searchParams.append('prependOperatingExpenses', 'true');

    const response = await fetch(url);
    return await response.json();
}

async function main() {
    console.log('=== deBridge Bridge Test ===\n');

    const provider = new ethers.JsonRpcProvider(MONAD_RPC);
    const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

    console.log('Wallet:', wallet.address);

    // Check balance
    const balance = await provider.getBalance(wallet.address);
    console.log('MON Balance:', ethers.formatEther(balance), 'MON');

    // Bridge amount: 1 MON
    const bridgeAmount = ethers.parseEther('1').toString();
    console.log('\nBridge Amount: 1 MON');

    // Get quote for MON → SOL
    console.log('\n--- Getting deBridge Quote ---');
    const quote = await getDebridgeQuote(
        DEBRIDGE_MONAD_CHAIN_ID,
        DEBRIDGE_SOLANA_CHAIN_ID,
        MONAD_NATIVE,
        SOLANA_NATIVE,
        bridgeAmount
    );

    if (quote.error) {
        console.error('Quote error:', quote.error);
        return;
    }

    console.log('Input:', quote.estimation?.srcChainTokenIn?.amount, 'MON');
    console.log('Output:', quote.estimation?.dstChainTokenOut?.amount, 'lamports (SOL)');
    console.log('Output USD:', '$' + quote.estimation?.dstChainTokenOut?.approximateUsdValue?.toFixed(2));
    console.log('Estimated time:', quote.order?.approximateFulfillmentDelay, 'seconds');

    // For actual bridge, we need a Solana destination address
    // Using a placeholder - replace with actual Solana address
    const SOLANA_DEST = 'So11111111111111111111111111111111111111112'; // Placeholder

    console.log('\n--- Getting Transaction Data ---');
    console.log('Destination Solana address:', SOLANA_DEST);

    const txData = await getDebridgeTransaction(
        DEBRIDGE_MONAD_CHAIN_ID,
        DEBRIDGE_SOLANA_CHAIN_ID,
        MONAD_NATIVE,
        SOLANA_NATIVE,
        bridgeAmount,
        wallet.address,
        SOLANA_DEST
    );

    if (txData.error) {
        console.error('Transaction data error:', txData.error);
        console.log('Full response:', JSON.stringify(txData, null, 2));
        return;
    }

    console.log('Transaction to:', txData.tx?.to);
    console.log('Transaction value:', txData.tx?.value);
    console.log('Data length:', txData.tx?.data?.length);

    // Uncomment to execute
    // console.log('\n--- Executing Bridge ---');
    // const tx = await wallet.sendTransaction({
    //     to: txData.tx.to,
    //     data: txData.tx.data,
    //     value: txData.tx.value,
    //     gasLimit: 500000
    // });
    // console.log('Tx hash:', tx.hash);
    // await tx.wait();
    // console.log('Bridge initiated!');
}

main().catch(console.error);
