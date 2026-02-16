# NAD.FUN Contract Addresses & Factory ABI

Source: [Naddotfun/contract-v3-abi](https://github.com/Naddotfun/contract-v3-abi) (official integration guide / SDK docs).

## Monad Mainnet Addresses

| Contract              | Address |
|-----------------------|---------|
| **DEX_FACTORY**       | `0x6B5F564339DbAD6b780249827f2198a841FEB7F3` |
| WMON                 | `0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A` |
| BONDING_CURVE_ROUTER  | `0x6F6B8F1a20703309951a5127c45B49b1CD981A22` |
| BONDING_CURVE         | `0xA7283d07812a02AFB7C09B60f8896bCEA3F90aCE` |
| DEX_ROUTER            | `0x0B79d71AE99528D1dB24A4148b5f4F865cc2b137` |
| LENS                  | `0x7e78A8DE94f21804F7a17F4E8BF9EC2c872187ea` |

## DEX Factory ABI

The contract-v3-abi repo does **not** publish an `IFactory.json`. The DEX is Capricorn V3 (Uniswap V3–style). Use this minimal factory ABI for `getPool(tokenA, tokenB, fee)`:

```json
[
  {
    "type": "function",
    "name": "getPool",
    "inputs": [
      { "name": "tokenA", "type": "address", "internalType": "address" },
      { "name": "tokenB", "type": "address", "internalType": "address" },
      { "name": "fee", "type": "uint24", "internalType": "uint24" }
    ],
    "outputs": [{ "name": "pool", "type": "address", "internalType": "address" }],
    "stateMutability": "view"
  }
]
```

Saved locally: `cloned-repos/ganjamon-agent/abi/nadfun_factory_abi.json` (or use the repo’s raw ABIs for router/lens).

## Official ABI Repo

- **Repo:** https://github.com/Naddotfun/contract-v3-abi  
- **Published ABIs:** `IBondingCurve.json`, `IBondingCurveRouter.json`, `IDexRouter.json`, `ILens.json`, `IToken.json`  
- **No factory ABI** in repo; use the minimal ABI above for pool lookups.

## Usage (ethers v6)

```javascript
const factoryAddress = "0x6B5F564339DbAD6b780249827f2198a841FEB7F3";
const factoryAbi = [/* getPool ABI above */];
const pool = await factory.getPool(wmonAddress, tokenAddress, feeTier);
```

## Chain

- **Monad mainnet** — Chain ID: 143  
- RPC: `https://mainnet.monad.xyz/rpc` (or other public RPCs).
