# Ralph Horde/Swarm Research: Multi-Ralph Coordination Systems

> Research findings on coordinating multiple ralph agents (ralph horde/swarm patterns)
> Created: 2026-01-26
> Based on web/GitHub search and cloned repositories

## Executive Summary

**Key Finding**: While there's no single project explicitly called "ralph horde" or "ralph swarm", there are **three highly relevant systems** for coordinating multiple ralph agents:

1. **ralph-orchestrator** (mikeyobrien) - Most sophisticated, Rust-based, hat-based orchestration
2. **workmux** (raine) - Git worktrees + tmux for parallel agents
3. **multi-agent-workflow-kit** (laris-co) - Tmux + git worktree multi-agent workflows

All three use **git worktrees** for isolation and **tmux** for coordination, confirming this is the emerging pattern.

---

## 1. ralph-orchestrator (mikeyobrien)

**Repository**: https://github.com/mikeyobrien/ralph-orchestrator  
**Stars**: 1,385 | **Forks**: 151  
**Language**: Rust  
**Status**: Active development (v2.0.0)

### Key Features

**Hat-Based Orchestration**:
- Specialized Ralph personas ("hats") with distinct behaviors
- Event-driven coordination through typed events with glob pattern matching
- 20+ pre-configured workflow presets (TDD, spec-driven, mob programming, adversarial review, etc.)

**Multi-Loop Concurrency**:
- Run parallel loops in git worktrees with automatic merge workflow
- Primary loop holds `.ralph/loop.lock`, additional loops spawn to `.worktrees/<loop-id>/`
- Each loop has isolated events, tasks, and scratchpad
- Memories are shared (symlinked back to main repo)
- Auto-merge on completion with conflict resolution

**Architecture**:
```
Primary Loop (holds .ralph/loop.lock)
├── Runs in main workspace
├── Processes merge queue on completion
└── Spawns merge-ralph for queued loops

Worktree Loops (.worktrees/<loop-id>/)
├── Isolated filesystem via git worktree
├── Symlinked memories → main repo
├── Queue for merge on completion
└── Exit cleanly (no spawn)
```

**Key Innovation**: **Hat System** - Specialized personas coordinate through events:
- Each hat has triggers (events that activate it) and publishes (events it emits)
- Event routing uses glob-style pattern matching
- Ralph serves as constant coordinator, delegating to hats based on topology

**Example Presets**:
- `tdd-red-green.yml`: Test Writer → Implementer → Refactorer (cyclic)
- `spec-driven.yml`: Spec Writer → Spec Critic → Implementer → Verifier (contract-first)
- `mob-programming.yml`: Navigator → Driver → Observer (rotating roles)
- `adversarial-review.yml`: Builder → Red Team → Fixer (security review)

**Multi-Backend Support**: Claude Code, Kiro, Gemini CLI, Codex, Amp, Copilot CLI, OpenCode

### Key Files Cloned

- `presets/` - 20+ workflow presets
- `AGENTS.md` - Philosophy and patterns
- `README.md` - Comprehensive documentation
- Rust implementation in `crates/`

---

## 2. workmux (raine)

**Repository**: https://github.com/raine/workmux  
**Language**: Rust  
**Status**: Active development

### Key Features

**Git Worktrees + Tmux Integration**:
- Creates git worktree with matching tmux window in single command
- Merges branches and cleans up everything (worktree, tmux window, branches) in one command
- Dashboard TUI for monitoring agents, reviewing changes, sending commands

**Parallel Agent Workflows**:
- Each agent gets isolated worktree (separate directory + branch)
- All agents visible in single tmux session with split panes
- Agent status tracking (🤖 working, 💬 waiting, ✅ done)
- Automatic branch name generation from prompts using LLM

**Key Commands**:
```bash
workmux add feature-name          # Create worktree + tmux window
workmux merge                     # Merge and clean up
workmux dashboard                 # TUI dashboard of all agents
workmux hey 1 "task description"  # Send message to agent
```

**Multi-Worktree Generation**:
- Create multiple worktrees from single command
- Support for agent-specific worktrees (`-a claude -a gemini`)
- Count-based generation (`-n 3`)
- Variable matrices (`--foreach "platform:iOS,Android"`)
- Stdin input for batch processing
- Concurrency limits (`--max-concurrent 3`)

**Dashboard Features**:
- Live preview of agent terminal output
- Diff view (WIP vs review mode)
- Patch mode for selective staging
- Quick jump to agents (1-9 keys)
- Sort modes (priority, project, recency, natural)

**Agent Status Tracking**:
- Integrates with Claude Code hooks to show status in tmux window names
- Icons: 🤖 working, 💬 waiting, ✅ done
- Auto-clears on window focus

### Key Innovation

**"tmux is the interface"** - No separate UI, everything happens in tmux. Perfect for existing tmux users.

---

## 3. multi-agent-workflow-kit (laris-co)

**Repository**: https://github.com/laris-co/multi-agent-workflow-kit  
**Language**: Python (uvx-based)  
**Status**: Proof of concept, early development

### Key Features

**Isolated Git Worktrees**:
- Each agent gets own worktree in `agents/` directory
- Shared tmux session with split panes for visibility
- Default: 3 agent worktrees ready to use

**Agent Communication**:
```bash
maw hey 1 "add user authentication"  # Send to specific agent
maw send "git status"                 # Broadcast to all
maw zoom 1                            # Focus on agent 1
```

**Smart Sync**:
- Context-aware git sync with main branch
- Handles merge conflicts intelligently

**Tmux Profiles**:
- 6 pre-configured layouts (profile0-profile5)
- Custom profiles via `.agents/profiles/custom.sh`

**Configuration**:
- `.agents/agents.yaml` - Agent definitions
- Each agent: branch, worktree_path, model, description

### Key Innovation

**Bootstrap in one command** - `uvx multi-agent-kit init` sets up everything.

---

## Common Patterns Across All Three

### 1. Git Worktrees for Isolation

**All three use git worktrees** to isolate agents:
- Separate directories per agent/branch
- Prevents file conflicts
- Enables true parallel development
- Each worktree = isolated workspace

**Structure**:
```
project/
├── main/                    # Primary workspace
└── project__worktrees/      # Or agents/
    ├── agent-1/            # Isolated worktree
    ├── agent-2/            # Isolated worktree
    └── agent-3/            # Isolated worktree
```

### 2. Tmux for Coordination

**All three use tmux** for:
- Visual monitoring of all agents
- Sending messages/commands to agents
- Managing agent windows/panes
- Dashboard/status views

### 3. Event-Driven Coordination

**ralph-orchestrator** uses explicit event system:
- Hats publish/subscribe to events
- Event routing via glob patterns
- Typed events with payloads

**workmux** and **multi-agent-workflow-kit** use:
- Direct message passing (`hey`, `send`)
- Status tracking via hooks
- Implicit coordination through shared state

### 4. Automatic Merge Workflows

**ralph-orchestrator** has sophisticated merge:
- Queues worktree loops for merge
- Spawns merge-ralph with specialized hats
- AI-powered conflict resolution
- Handoff summaries between loops

**workmux** has simple merge:
- `workmux merge` - merges and cleans up
- Manual conflict resolution

### 5. Status Tracking

**All three track agent status**:
- ralph-orchestrator: TUI with real-time activity
- workmux: Icons in tmux window names (🤖💬✅)
- multi-agent-workflow-kit: Status in dashboard

---

## Comparison Matrix

| Feature | ralph-orchestrator | workmux | multi-agent-workflow-kit |
|---------|-------------------|---------|--------------------------|
| **Language** | Rust | Rust | Python (uvx) |
| **Isolation** | Git worktrees | Git worktrees | Git worktrees |
| **Coordination** | Event-driven (hats) | Direct messaging | Direct messaging |
| **Presets/Workflows** | 20+ presets | Custom config | 6 tmux profiles |
| **Multi-Loop** | ✅ Auto-merge | ✅ Manual merge | ✅ Manual sync |
| **Dashboard** | TUI (built-in) | TUI dashboard | Tmux panes |
| **Status Tracking** | TUI activity | Tmux icons | Dashboard |
| **Conflict Resolution** | AI-powered | Manual | Manual |
| **Backend Support** | 7 backends | Claude-focused | Configurable |
| **Maturity** | v2.0.0 (active) | Active | POC (early) |

---

## Key Insights

### 1. Git Worktrees Are Essential

**All three systems use git worktrees** - this is the standard pattern for:
- File isolation (no conflicts)
- Parallel development
- Easy cleanup (just remove worktree)
- Branch management

### 2. Hat-Based Orchestration (ralph-orchestrator)

**Most sophisticated approach**:
- Specialized personas (hats) with clear roles
- Event-driven handoffs
- 20+ proven workflow patterns
- Extensible via custom hats

**Best for**: Complex workflows requiring role separation (TDD, spec-driven, security review)

### 3. Simple Messaging (workmux, multi-agent-workflow-kit)

**Simpler approach**:
- Direct message passing
- No event system overhead
- Easier to understand
- Faster to set up

**Best for**: Parallel feature development, independent tasks

### 4. Auto-Merge Is Complex But Valuable

**ralph-orchestrator's auto-merge**:
- Queues completed loops
- Spawns merge-ralph with specialized hats
- AI resolves conflicts
- Handles edge cases (unresolvable → manual review)

**This is the most advanced pattern** - worth studying for our orchestrator.

### 5. Dashboard/Status Is Critical

**All three provide visibility**:
- ralph-orchestrator: Built-in TUI
- workmux: Dashboard + tmux icons
- multi-agent-workflow-kit: Tmux panes + dashboard

**Key insight**: You need to see what all agents are doing at a glance.

---

## Recommended Patterns for LARP Protocol

### Pattern 1: Hat-Based Orchestration (ralph-orchestrator style)

**Use when**:
- Complex workflows with distinct phases
- Need role separation (planner, builder, reviewer)
- Want reusable workflow patterns

**Implementation**:
- Define hats with triggers/publishes
- Event-driven coordination
- Presets for common patterns

### Pattern 2: Simple Parallel Loops (workmux style)

**Use when**:
- Independent features/tasks
- Simple parallel development
- Quick setup needed

**Implementation**:
- Git worktrees per agent
- Tmux windows for visibility
- Direct messaging for coordination

### Pattern 3: Hybrid Approach

**Combine both**:
- Use hats for complex workflows
- Use simple loops for independent tasks
- Dashboard to monitor everything

---

## Code to Study

### ralph-orchestrator (Most Relevant)

**Key Files**:
- `presets/tdd-red-green.yml` - TDD workflow
- `presets/spec-driven.yml` - Spec-first development
- `presets/mob-programming.yml` - Rotating roles
- `presets/adversarial-review.yml` - Security review
- `AGENTS.md` - Philosophy and patterns
- `crates/ralph-core/src/worktree.rs` - Worktree coordination
- `crates/ralph-core/src/loop_registry.rs` - Loop tracking
- `crates/ralph-core/src/merge_queue.rs` - Merge queue

**Key Concepts**:
- Hat system (specialized personas)
- Event routing (glob patterns)
- Multi-loop concurrency (git worktrees)
- Auto-merge workflow (conflict resolution)

### workmux (Practical Patterns)

**Key Files**:
- `README.md` - Comprehensive usage guide
- Dashboard implementation
- Agent status tracking
- Multi-worktree generation

**Key Concepts**:
- Git worktree automation
- Tmux integration
- Dashboard for monitoring
- Status icons in tmux

### multi-agent-workflow-kit (Simple Approach)

**Key Files**:
- `.agents/agents.yaml` - Configuration
- Agent communication patterns
- Tmux profile layouts

**Key Concepts**:
- Simple agent management
- Direct messaging
- Tmux-based coordination

---

## Next Steps

1. **Study ralph-orchestrator's hat system** - Most sophisticated pattern
2. **Study workmux's dashboard** - Best monitoring approach
3. **Study auto-merge workflow** - Most advanced conflict resolution
4. **Adapt patterns to our tmux orchestrator** - Integrate best ideas
5. **Test with LARP Protocol** - Validate patterns in practice

---

## References

- [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) - Hat-based orchestration
- [workmux](https://github.com/raine/workmux) - Git worktrees + tmux
- [multi-agent-workflow-kit](https://github.com/laris-co/multi-agent-workflow-kit) - Simple multi-agent setup
- [Introduction to workmux](https://raine.dev/blog/introduction-to-workmux/) - Blog post
- [Git worktrees for parallel AI coding](https://raine.dev/blog/git-worktrees-parallel-agents/) - Blog post

---

## Implementation Details

### ralph-orchestrator: Multi-Loop Concurrency

**Key Files**:
- `crates/ralph-core/src/worktree.rs` - Git worktree creation/management
- `crates/ralph-core/src/loop_registry.rs` - Loop tracking with PID-based stale detection
- `crates/ralph-core/src/merge_queue.rs` - Event-sourced merge queue
- `crates/ralph-cli/src/loop_runner.rs` - Queue processing and merge spawning
- `crates/ralph-cli/presets/merge-loop.yml` - Specialized merge workflow

**Lock Mechanism**:
- Primary loop acquires `.ralph/loop.lock` (contains PID + prompt)
- Additional loops detect lock → spawn to worktree automatically
- Lock file prevents recursive worktree spawning

**Merge Workflow**:
1. Worktree loop completes → queues in `merge-queue.jsonl` → exits
2. Primary loop completes → calls `process_pending_merges()`
3. For each queued entry → spawns merge-ralph with specialized hats:
   - **merger**: Performs git merge, runs tests
   - **resolver**: Resolves conflicts by understanding intent
   - **tester**: Verifies tests pass after conflict resolution
   - **cleaner**: Removes worktree and branch
   - **failure_handler**: Marks for manual review if unresolvable

**Key Innovation**: Queue-based merge prevents recursive worktree spawning. Worktree loops queue themselves, primary loop processes queue when done.

### workmux: Git Worktrees + Tmux

**Key Features**:
- One command creates worktree + tmux window
- Dashboard TUI for monitoring all agents
- Agent status icons in tmux window names
- Multi-worktree generation from single command
- Automatic branch name generation from prompts (LLM-based)

**Dashboard Capabilities**:
- Live preview of agent terminal output
- Diff view (WIP vs review mode)
- Patch mode for selective staging
- Quick jump to agents (1-9 keys)
- Sort modes (priority, project, recency)

### multi-agent-workflow-kit: Simple Coordination

**Key Features**:
- Bootstrap in one command (`uvx multi-agent-kit init`)
- Direct messaging (`maw hey <agent> <message>`)
- Smart sync with context awareness
- 6 pre-configured tmux profiles

---

## Patterns to Adopt for LARP Protocol

### 1. Git Worktree Isolation (All Three)

**Pattern**: Each agent gets isolated worktree
```bash
# ralph-orchestrator style
.worktrees/ralph-20250124-a3f2/

# workmux style  
project__worktrees/feature-name/

# multi-agent-workflow-kit style
agents/1/
```

**Benefits**:
- No file conflicts
- True parallel development
- Easy cleanup
- Branch isolation

### 2. Hat-Based Orchestration (ralph-orchestrator)

**Pattern**: Specialized personas coordinate through events
```yaml
hats:
  planner:
    triggers: ["task.start"]
    publishes: ["plan.ready"]
  builder:
    triggers: ["plan.ready"]
    publishes: ["build.done"]
```

**Benefits**:
- Clear role separation
- Reusable workflow patterns
- Event-driven coordination
- Extensible via custom hats

### 3. Auto-Merge Workflow (ralph-orchestrator)

**Pattern**: Queue-based merge with AI conflict resolution
```
Worktree Loop → Queue → Primary Loop → Merge-Ralph → Cleanup
```

**Benefits**:
- Automatic merge on completion
- AI-powered conflict resolution
- Test verification after merge
- Graceful failure handling

### 4. Dashboard/Status Tracking (workmux)

**Pattern**: Visual monitoring of all agents
- Status icons in tmux (🤖💬✅)
- TUI dashboard with live preview
- Quick navigation between agents

**Benefits**:
- At-a-glance visibility
- Easy agent management
- Real-time monitoring

### 5. Multi-Worktree Generation (workmux)

**Pattern**: Create multiple worktrees from single command
```bash
workmux add feature -a claude -a gemini -p "Implement API"
# Creates: feature-claude, feature-gemini
```

**Benefits**:
- Parallel experiments
- Agent comparison
- Batch task processing

---

## Recommended Implementation for LARP Protocol

### Phase 1: Basic Multi-Ralph (workmux pattern)

1. **Git worktree per ralph**
   - Create worktree for each ralph
   - Isolated filesystem
   - Shared git history

2. **Tmux windows for visibility**
   - One window per ralph
   - Status tracking
   - Easy navigation

3. **Simple messaging**
   - Direct message passing
   - No event system overhead
   - Quick to implement

### Phase 2: Hat-Based Orchestration (ralph-orchestrator pattern)

4. **Add hat system**
   - Specialized personas
   - Event-driven coordination
   - Reusable presets

5. **Auto-merge workflow**
   - Queue completed loops
   - AI conflict resolution
   - Test verification

### Phase 3: Advanced Features

6. **Dashboard**
   - TUI for monitoring
   - Live preview
   - Diff view

7. **Multi-worktree generation**
   - Batch creation
   - Agent comparison
   - Parallel experiments

---

*All three repos have been cloned to `docs/long-running-claude/repos/` for detailed study.*
