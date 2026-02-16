# Verification Strategies Reference

Verification is non-negotiable. Always give Ralph a way to verify its work.

---

## Strategy 1: Tests-First Verification

Best when possible. Write tests before implementation.

### Prompt Template

```markdown
## Verification
Before marking task complete, run:
- npm test
- npm run typecheck
- npm run lint

Only set EXIT_SIGNAL: true if ALL tests pass.
```

### Benefits

- Objective, automated feedback
- Prevents false completion signals
- Forces correct implementation

### Limitations

- Not all tasks have testable outputs
- UI changes, documentation updates

---

## Strategy 2: Stop-Hook Validation

Claude Code hook intercepts stop attempts and verifies before allowing exit.

### Configuration (`.claude/settings.json`)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "if ! npm test 2>/dev/null; then echo 'Tests failed - blocking stop'; exit 2; fi"
          },
          {
            "type": "command",
            "command": "if ! npm run typecheck 2>/dev/null; then echo 'Typecheck failed - blocking stop'; exit 2; fi"
          },
          {
            "type": "command",
            "command": "if ! npm run lint 2>/dev/null; then echo 'Lint failed - blocking stop'; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

### How It Works

1. Claude completes work and tries to stop
2. Stop hook runs verification commands
3. If any check fails (exit code 2), Claude is blocked
4. Claude receives feedback and continues
5. Loop repeats until all checks pass

### Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Allow stop |
| 2    | Block stop, feed prompt back |
| Other | Error, allow stop with warning |

---

## Strategy 3: Structural Verification

Check file structure and content without running tests.

### Implementation

```typescript
verifyCompletion: async () => {
  const checks = await Promise.all([
    fileExists('vitest.config.ts'),
    !await fileExists('jest.config.js'),
    noFilesMatch('**/*.test.ts', /from ['"]@jest/),
    fileContains('package.json', '"vitest"'),
  ]);

  return {
    complete: checks.every(Boolean),
    reason: checks.every(Boolean) ? 'Migration complete' : 'Structural checks failed'
  };
}
```

### Use Cases

- Migration tasks (Jest → Vitest)
- Configuration changes
- File cleanup operations

---

## Strategy 4: UI Verification

Tests can pass while UI is broken. Visual verification catches this.

### Protocol

1. Take screenshot of UI changes: `screenshot.png`
2. In next iteration, verify screenshot shows expected UI
3. Rename to `screenshot-verified.png` if correct
4. Only set EXIT_SIGNAL after verification

### Prompt Template

```markdown
## UI Verification Protocol
1. After implementing UI changes, take a screenshot
2. In the next iteration, review the screenshot
3. If UI matches requirements, rename to screenshot-verified.png
4. Only output completion promise after screenshot verification
```

### Tools

- Playwright for automated screenshots
- Chrome DevTools via MCP
- Manual review at phase completion

---

## Strategy 5: Spec-Driven Verification

Compare implementation against specification.

### Process

1. Write design/spec artifact first (durable file)
2. Use agent loop to implement against spec
3. Rely on compiler/test feedback as backpressure
4. Verify implementation matches spec

### Example

```typescript
verifyCompletion: async () => {
  const spec = await readFile('specs/api.md');
  const implementation = await readFile('src/api.ts');

  const checks = [
    spec.includes('GET /users') && implementation.includes('app.get("/users"'),
    spec.includes('POST /users') && implementation.includes('app.post("/users"'),
    spec.includes('DELETE /users/:id') && implementation.includes('app.delete("/users/:id"'),
  ];

  return {
    complete: checks.every(Boolean),
    reason: checks.every(Boolean) ? 'Matches spec' : 'Missing requirements'
  };
}
```

---

## Combining Verification Methods

Best practice: Use multiple verification methods.

### Multi-Layer Verification

```typescript
verifyCompletion: async () => {
  // 1. Structural checks
  const structural = await checkStructure();

  // 2. Test execution
  const tests = await runTests();

  // 3. Spec compliance
  const spec = await checkSpec();

  // 4. Judge review (for complex changes)
  const review = await judgeReview();

  return {
    complete: structural && tests && spec && review,
    reason: 'All verification checks passed'
  };
}
```

### Priority Order

1. **Automated tests** (highest confidence)
2. **Type checking** (catches many errors)
3. **Linting** (code quality)
4. **Structural checks** (file existence, patterns)
5. **Spec comparison** (requirements coverage)
6. **UI verification** (visual correctness)
7. **Judge review** (semantic review)

---

## Backpressure Mechanisms

Automated feedback that keeps agents aligned over time.

### Types

| Mechanism | Description |
|-----------|-------------|
| Build/Test | Compile, read errors, self-correct |
| Type System | Expressive types, quality compiler errors |
| UI Feedback | Agents see rendered output |
| Lint/LSP | Static analysis through tools |
| Spec-Driven | Compare against schemas |
| Fuzzing | Hard acceptance gates |

### Why Backpressure Matters

- Loop without gates → drift / overconfidence
- Loop with gates → gradual improvement toward "passes"
- Ralph-style loops are cheap repetition
- Backpressure makes repetition converge

---

## Verification Command Templates

### Node.js Project

```bash
npm test && npm run typecheck && npm run lint && npm run build
```

### Python Project

```bash
pytest && mypy . && ruff check . && python -m build
```

### Rust Project

```bash
cargo test && cargo clippy -- -D warnings && cargo build --release
```

### Go Project

```bash
go test ./... && go vet ./... && golangci-lint run && go build .
```

---

## Common Pitfalls

### 1. Tests Pass But UI Broken

**Solution**: Add screenshot verification

### 2. False Positive Completion

**Solution**: Dual-condition exit (indicators + explicit signal)

### 3. Verification Too Slow

**Solution**: Run fast checks first (typecheck before full test suite)

### 4. Verification Flaky

**Solution**: Retry flaky tests, increase timeouts

### 5. No Tests Available

**Solution**: Use structural checks or spec comparison
