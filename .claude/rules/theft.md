# Liberal Ethical Theft Policy

**CRITICAL**: When building new features, ALWAYS search for existing open source implementations first.

## The Rule

Before writing code from scratch:
1. Search GitHub for existing implementations
2. Clone relevant repos to `cloned-repos/`
3. Security audit before using (see below)
4. Adapt for our use case
5. Respect licenses, attribute appropriately

## Why

- Other people have solved these problems
- Production-tested code > untested new code
- Speed to market matters
- Don't reinvent wheels

## Audit Checklist

Before using ANY cloned code:

```bash
# Check for dangerous patterns
grep -r "eval\|exec\|subprocess" repo-name/
grep -r "requests\.post\|aiohttp\.post" repo-name/ | grep -v "api\."

# Check for key exfiltration
grep -r "private_key\|secret\|password" repo-name/

# Check hardcoded URLs
grep -rE "https?://" repo-name/ | head -50
```

Red flags:
- `eval()` or `exec()` with user input
- Obfuscated/minified code in repos that shouldn't have it
- Unexpected outbound network calls
- Private keys logged or sent anywhere
- Base64 encoded strings being decoded and executed

## Documentation

When cloning repos:
1. Add entry to `docs/CLONED_TRADING_REPOS.md` (if trading related)
2. Note: what was cloned, why, what we're using from it
3. Document any security concerns found

## Quick Clone Template

```bash
cd /mnt/c/Users/natha/sol-cannabis/cloned-repos
git clone --depth 1 https://github.com/user/repo.git local-name
```

## Current Cloned Repos

See: `cloned-repos/CLAUDE.md` for full inventory of trading-related clones.
