# Skills Management Policy

**CRITICAL**: When working with external platforms that provide skill.md files, always save them locally.

## What Are Skill Files?

Skill files (skill.md) are platform-provided documentation that describe:
- API endpoints and authentication
- Registration and setup flows
- Best practices and gotchas
- Integration patterns

Platforms like Retake.tv, Moltbook, and others provide these at `https://platform.com/skill.md`.

## The Rule

When you encounter a platform with a skill.md file:

1. **Fetch and save immediately** to `skills/<platform-name>.md`
2. **Reference in operations** when working with that platform
3. **Check for updates** periodically (skills evolve)

## Skills Directory

All skill files live in: `skills/`

| Platform | File | Source URL |
|----------|------|------------|
| Retake.tv | `skills/retake-tv.md` | https://retake.tv/skill.md |
| Moltbook | `skills/moltbook.md` | https://moltbook.com/skill.md |
| Allium | `skills/allium.md` | https://agents.allium.so/skills/skill.md |

## Why This Matters

- Skills contain platform-specific gotchas learned the hard way
- API endpoints and auth methods change - local copies track what we've used
- Registration responses (tokens, IDs) should be stored per skill guidance
- Saves time re-fetching the same docs

## Credentials Storage

When a skill file specifies credential storage (like `~/.config/retake/credentials.json`):

1. **Create the credentials file** immediately after registration
2. **Store all returned tokens/IDs** - you can't re-register with same name
3. **Reference in CLAUDE.md context** if needed for quick access
4. **NEVER commit credentials** to git - add to .gitignore

## Adding New Skills

```bash
# Fetch and save a new skill
curl -s https://platform.com/skill.md > skills/platform-name.md

# Or use WebFetch tool and Write tool
```

After saving, add the platform to the table above.
