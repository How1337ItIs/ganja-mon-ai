# Task: [ONE-LINE DESCRIPTION]

## Objective

[Detailed description of what to accomplish. Be specific about:
- What feature/fix to implement
- What the end state should look like
- Any constraints or requirements]

## Acceptance Criteria

- [ ] Criterion 1: [Specific, testable requirement]
- [ ] Criterion 2: [Specific, testable requirement]
- [ ] Criterion 3: [Specific, testable requirement]
- [ ] All tests pass
- [ ] Build succeeds
- [ ] No type errors

## Verification Commands

Run these commands after each significant change:

```bash
# Type checking
pnpm typecheck

# Run tests
pnpm test

# Build
pnpm build

# Lint (optional)
pnpm lint
```

## Context

[Any relevant context about the codebase:
- Key files to look at
- Existing patterns to follow
- Related previous work]

## Implementation Notes

[Optional: Specific guidance on implementation approach]

## Anti-Patterns (Do NOT)

- Do NOT output completion promise if ANY criterion is unmet
- Do NOT skip verification commands
- Do NOT add features beyond the acceptance criteria
- Do NOT over-engineer or add unnecessary abstractions
- Do NOT leave console.log statements in production code

## Completion Protocol

When ALL acceptance criteria are met AND all verification commands pass:

1. Double-check each criterion is satisfied
2. Run ALL verification commands one final time
3. Commit with a descriptive message
4. If everything passes, output:

<promise>COMPLETE</promise>

## Status Block (Required)

Every response MUST end with this status block:

```
---RALPH_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: [number]
FILES_MODIFIED: [number]
TESTS_STATUS: PASSING | FAILING | NOT_RUN
EXIT_SIGNAL: false | true
CURRENT_TASK: [what you're working on]
RECOMMENDATION: [next action]
---END_RALPH_STATUS---
```

---

## Quick Reference: Loop Behavior

- You are running in a Ralph loop
- Each iteration, you receive this same prompt
- Your previous work is visible in files and git history
- Progress by modifying files and committing
- Only output `<promise>COMPLETE</promise>` when truly done
- Never lie to escape the loop - it will be re-verified
