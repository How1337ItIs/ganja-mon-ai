# ERC‑8004 on Monad — Status and Next Steps

## What’s Already Done (from repo sources)

From `cloned-repos/ganjamon-agent/GANJAMON_8004.md` and the official ERC‑8004 contracts repo:

- ERC‑8004 registries are deployed on Monad mainnet (official addresses below).
- IdentityRegistry: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- ReputationRegistry: `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`
- Validation registry status is **not** listed in the official Monad mainnet deployment table.
- GanjaMon is registered on-chain with agentId **4** (Monad mainnet).
- Agent URI should point to `https://grokandmon.com/.well-known/agent-registration.json`.

## What This Repo Now Adds

- `src/web/.well-known/agent-card.json`
- `src/web/.well-known/agent.json` (alias to agent card)
- `src/web/.well-known/agent-registration.json` (ERC‑8004 registration file)
- `src/api/app.py` now mounts `/.well-known` as static files

## Next Steps (Recommended)

1. Confirm on-chain registration
   - Verify `ownerOf(4)` on IdentityRegistry and ensure it matches the operator wallet.
   - Ensure `src/web/.well-known/agent-registration.json` retains `agentId: 4`.

2. Update agent URI if needed
   - Ensure the on-chain agentURI matches the `agent-registration.json` URL.

3. Add MCP endpoint once live
   - Update `agent-registration.json` to include MCP service.

4. Reputation usage
   - Once registered, users can submit feedback to ReputationRegistry.

## Useful Local References

- `cloned-repos/8004-contracts/README.md` (canonical deployment table)
- `cloned-repos/ganjamon-agent/GANJAMON_8004.md`
- `openclaw-trading-assistant/src/scripts/`
