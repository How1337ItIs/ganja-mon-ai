# Model-Hierarchy Skill — Adoption Plan (No Code Yet)

**Source:** [zscole/model-hierarchy-skill](https://github.com/zscole/model-hierarchy-skill) — OpenClaw skill for cost-optimized model routing by task complexity.  
**Goal:** Plan how to adapt it for the Grok & Mon / GanjaMon OpenClaw stack without changing any code yet.

---

## 1. What the Skill Does

- Teaches the agent to **classify tasks** as ROUTINE / MODERATE / COMPLEX.
- Maps each class to a **model tier** (cheap / mid / premium).
- Encourages: default to cheaper models for routine work, escalate to premium only when needed, use cheap models for heartbeats/cron and sub-agents.
- **Result (claimed):** ~10x cost reduction vs running everything on a premium model, with similar quality on hard tasks.

---

## 2. Our Current Model Setup (Reference Only)

- **Config source:** `openclaw-workspace/config/openclaw.json` (deployed to `~/.openclaw/openclaw.json`).
- **Current primary:** `openrouter/moonshotai/kimi-k2.5` (from last read).
- **Current fallbacks:** `openrouter/moonshotai/kimi-k2-thinking`.
- **Heartbeat:** Same model as primary, every 2h; prompt reads HEARTBEAT.md, sensor snapshot, memory append.
- **Other providers in play (from docs/env):** xAI (Grok), Gemini (skills/content), Claude (fallback when activated). OpenRouter gives access to many models (Kimi, DeepSeek, etc.) under one API.

So we already have a **primary + fallback** chain; we do **not** today route by task type. Adding model-hierarchy would mean the agent *chooses* when to suggest/use a different model (or we configure heartbeat/cron to use a cheaper model explicitly).

---

## 3. Where It Would Live

- **Skill:** `openclaw-workspace/ganjamon/skills/model-hierarchy/SKILL.md` (workspace skill, highest precedence).
- **Optional:** Keep a copy or submodule of the upstream repo under `cloned-repos/model-hierarchy-skill/` for reference/tests; install would copy or symlink `SKILL.md` into the workspace skill dir.
- **Config:** No new config *required*; tier-to-model mapping could stay inside the skill text. If we want runtime control, we could later add `skills.entries["model-hierarchy"].config` (e.g. tier model IDs) in `openclaw.json`.

---

## 4. Adaptations for Our Stack

### 4.1 Tier ↔ Model Mapping

- **Upstream** uses concrete names (DeepSeek, GPT-4o-mini, Claude Sonnet/Opus, etc.). We need a mapping that matches **our** providers and config.
- **Proposed (to be validated against actual config):**
  - **Tier 1 (routine):** Cheapest model we’re willing to use — e.g. same as current primary (`openrouter/moonshotai/kimi-k2.5`) or a cheaper OpenRouter option (e.g. DeepSeek) if we add it as fallback or primary for routine.
  - **Tier 2 (moderate):** Current primary or a dedicated “mid” (e.g. Kimi K2.5 or Gemini 2.5 Flash for content).
  - **Tier 3 (complex):** “Thinking” or premium — e.g. `openrouter/moonshotai/kimi-k2-thinking`, or when enabled, Claude/Opus for oracle-style review.
- **Constraint:** OpenClaw’s model list is configured in `agents.defaults.model.primary` and `fallbacks`; the skill can’t add new models, only tell the agent *which of the configured models* to prefer for which task. So the plan should assume we **add at most one or two** cheaper/mid models to the config if we want real tier separation (e.g. OpenRouter DeepSeek for Tier 1).

#### Optional: More tiers (4-tier or 5-tier)

Three tiers can be too coarse: **Opus 4.6** (and similar frontier models) are clearly *more* capable than strong open-weight models like **Kimi K2.5** and **GLM 5**, but those open-weight models are in turn *more* capable than classic “Tier 2” models (e.g. Claude Sonnet, GPT-4o, Gemini Pro) on many benchmarks. So the hierarchy could separate:

| Tier | Role | Examples (upstream-style) |
|------|------|---------------------------|
| **1** | Cheapest routine | DeepSeek V3, GPT-4o-mini, Haiku, Gemini Flash, GLM 5 (text-only) |
| **2** | Classic mid | Claude Sonnet, GPT-4o, Gemini Pro |
| **3** | Strong open-weight / upper-mid | Kimi K2.5, GLM 5 (when task needs more than Tier 2) — more capable than Tier 2 in many dimensions, still cheaper than frontier |
| **4** | Frontier | Claude Opus 4.6, GPT-4.5, o1 — hardest reasoning, architecture, novel problems |

- **Task mapping:** ROUTINE → Tier 1; MODERATE → Tier 2 or 3 (use Tier 3 when you want “best non-frontier”); COMPLEX → Tier 3 or 4 (escalate to Tier 4 when Tier 3 has failed or task is clearly frontier-grade). Heartbeats / cron stay Tier 1; “oracle”-style deep review or security-sensitive work → Tier 4.
- **Our stack:** We could map Tier 1 = GLM 5 (text-only) or DeepSeek for routine; Tier 2 = (optional classic mid if we add one); Tier 3 = Kimi K2.5, Kimi K2 Thinking; Tier 4 = Claude Opus when enabled. Or keep 3 tiers and treat Kimi K2.5 as “Tier 2” and Opus as “Tier 3” for simplicity; the skill text can still say “frontier models (e.g. Opus 4.6) are more capable than open-weight (Kimi K2.5, GLM 5), which are more capable than classic mid (Sonnet, GPT-4o).”

#### Cost separation: does 4-tier make sense?

**Short answer: not if "tier" = cost band.** In the 4-tier table above, **Tier 3 (Kimi K2.5, GLM 5) is cheaper than Tier 2** (Sonnet, GPT-4o, Gemini Pro). Rough $/M: Tier 1 ~$0.10–0.50, Tier 3 ~$0.45–2.25 (Kimi), Tier 2 ~$1–15 (Sonnet etc.), Tier 4 ~$10–75. So cost order is **1 ≤ 3 < 2 < 4** — tier number and cost don't line up.

- **For clear cost separation**, use **3 cost bands** and keep capability as a nuance inside each band:
  - **Cheap (~$0.10–0.50/M):** DeepSeek, mini, Haiku, Flash, **GLM 5, Kimi K2.5** — routine and many moderate tasks. Within this band, Kimi K2.5 / GLM 5 are *more capable* than mini/Haiku; use them when you want "best in cheap" (including vision with K2.5).
  - **Mid (~$1–5/M):** Sonnet, GPT-4o, Gemini Pro — classic mid when you want a different provider or established mid-tier.
  - **Premium (~$10–75/M):** Opus 4.6, GPT-4.5, o1, Kimi K2 Thinking — complex/frontier only.
  That way **tier = cost band** and the skill can say "within Cheap, prefer Kimi K2.5 or GLM 5 when you need more capability."

- **If we keep 4 tiers by capability**, make it explicit that tiers are **capability** levels, not cost levels: Tier 3 is "high capability, lower cost than Tier 2" (open-weight is both strong and cheap). That's great for budget but can confuse "higher tier = higher cost." The skill should state: "Tier 3 models (e.g. Kimi K2.5) are often *cheaper* than Tier 2; use them when you need more than Tier 2 but don't need frontier."

**Recommendation:** For a *cost* separation standpoint, **3 cost bands** (Cheap / Mid / Premium) with "strong open-weight in Cheap" is clearer. Use 4 tiers only if we want a *capability* ladder and are okay with Tier 3 being cheaper than Tier 2.

#### Most logical system (recommendation)

Reasoning (cost + capability + simplicity):

1. **Tier should mean one thing.** If tier = cost band, then "higher tier = spend more" and "use Tier 1 for 80% of work" are simple. If tier = capability, we get Tier 3 cheaper than Tier 2, which breaks "escalate = pay more."
2. **The real decision is:** (A) How much am I willing to spend? (cost band) → (B) Which model in that band? (capability + vision within band). Three cost bands support that; a fourth "capability" tier mixes cost and capability and makes Tier 2 (classic mid) a corner case ("use when Tier 3 isn't available or you need a specific provider").
3. **Within Cheap:** We already have a capability spread (mini vs Kimi K2.5 vs GLM 5). Handle it by rules: "within Tier 1, if task needs vision → Kimi K2.5; if text-only and routine/moderate → GLM 5 or Kimi K2.5; if best-in-tier rate-limited → next in tier."
4. **Conclusion:** Use **3 tiers = 3 cost bands** (Cheap / Mid / Premium). Tier number = cost order. Document that "best in Cheap" (Kimi K2.5, GLM 5) can exceed Mid in some dimensions while costing less. No fourth tier; keep the skill's decision flow: task complexity → cost band → within-band selection by capability and vision.

#### GLM 5 (Zhipu) as Tier 1 / Tier 2

- **GLM 5** (Zhipu AI, 745B MoE, 200K context) is **very cheap and very capable** and is a strong candidate for Tier 1 (routine) or Tier 2 (moderate) in the hierarchy. OpenRouter lists Z.AI (Zhipu) as a provider; GLM-5 is available there as a **text-only** model.
- **Critical limitation: no image/vision.** GLM 5 does **not** support image inputs or vision. Therefore:
  - **Do NOT use GLM 5 for:** Any task that requires viewing or analyzing images — e.g. `nano-banana-pro` (image gen/edit), plant photo analysis, screenshot understanding, document/chart parsing, or any tool/skill that takes image input.
  - **Route image/vision tasks** to a model with vision (e.g. Gemini, Grok, or OpenRouter vision models like GLM-4.5V/4.6V if we add them).
- **Use GLM 5 for:** Heartbeat (sensor log, memory append, HEARTBEAT.md — no images), cron status/digest, HAL curl and status checks, text-only social compose, A2A discovery, trading snapshot/read-only, file ops, summarization of text. That covers most routine and many moderate tasks.
- **Skill text must encode:** “If the task involves an image (photo, screenshot, diagram, or image-generation skill), do not use GLM 5; use a vision-capable model.” So the model-hierarchy skill should include a **vision check** before assigning Tier 1/2 for GLM 5.
- **Config:** Add OpenRouter GLM 5 (e.g. `openrouter/z-ai/glm-5` or whatever the canonical ID is on OpenRouter) to `agents.defaults.model.fallbacks` or as primary for heartbeat. Validate exact model ID on [OpenRouter Z.AI](https://openrouter.ai/z-ai) before implementation.

#### Kimi K2.5 (Moonshot) as Tier 1 / Tier 2

- **Kimi K2.5** (Moonshot AI) is **native multimodal**: text, image, and video in a unified model (1T MoE, 32B active params, ~262K context). Available on [OpenRouter Moonshot](https://openrouter.ai/moonshotai) as `openrouter/moonshotai/kimi-k2.5`. Pricing (OpenRouter, Feb 2026): ~$0.45/M input, ~$2.25/M output — very competitive for a vision-capable model.
- **Vision:** Unlike GLM 5, Kimi K2.5 **has image/vision** (MoonViT encoder; image, video, PDF input). Use it for routine or moderate tasks that may involve photos, screenshots, or document parsing without stepping up to premium vision models.
- **Use Kimi K2.5 for:** Heartbeat (including turns that might attach a sensor screenshot), cron digest, HAL + status, social compose (with or without image), plant photo or chart analysis, nano-banana-pro orchestration, A2A, trading snapshot — i.e. Tier 1 and Tier 2 including vision. We already use it as primary in our config.
- **Kimi K2 Thinking** (`kimi-k2-thinking`) is the reasoning variant (higher cost); keep that as Tier 3 for complex/debug/architecture. The model-hierarchy skill can say: Tier 1/2 = K2.5, Tier 3 = K2-thinking or Claude/Opus when enabled.
- **Config:** We already have `openrouter/moonshotai/kimi-k2.5` as primary and `openrouter/moonshotai/kimi-k2-thinking` as fallback; no change required. For Zak’s upstream skill, adding Kimi K2.5 to the Tier 1 table (and optionally Tier 2) gives OpenRouter users a cheap, vision-capable option alongside GLM 5 (text-only).

### 4.2 Domain-Specific Classification (GanjaMon)

- **Grow / HAL:**  
  - ROUTINE: Sensor read, log to memory, status check, HAL health check.  
  - MODERATE: Grow decision from sensor + VPD targets (clear rules, multi-step but deterministic).  
  - COMPLEX: Novel diagnosis, “why is the plant stressed,” or after a cheaper model failed.
- **Trading:**  
  - ROUTINE: Portfolio snapshot, signal list, read-only HAL.  
  - MODERATE: Summarize P&L, draft trade rationale.  
  - COMPLEX: Actual trade execution (and always via lobster), architecture of strategy, debugging execution failures.
- **Social:**  
  - ROUTINE: Post a pre-approved message, check mentions.  
  - MODERATE: Compose post (social-composer + gemini), pick platform.  
  - COMPLEX: Crisis/controversy response, new voice strategy.
- **A2A / Moltbook / Clawk:**  
  - ROUTINE: Discovery scan, publish 10 signals, post from HEARTBEAT checklist.  
  - MODERATE: Compose Moltbook/Clawk post with verification, handle rate limits.  
  - COMPLEX: Appeal/negotiation, novel verification flows.
- **Heartbeat / Cron:**  
  - Heartbeat: Explicitly **Tier 1** in the skill (sensor + memory + HEARTBEAT.md checklist).  
  - Cron isolated jobs: Tier 1 for “daily digest” / status; Tier 2 if the job is “weekly analysis” or “deep review.”

### 4.3 Behavioral Rules (Aligned With Us)

- **Main session:** Default to Tier 2 for interactive work; suggest downgrade for routine (“I can do this on the cheaper model”); request upgrade when stuck.
- **Sub-agents / sessions_spawn:** Default to Tier 1 unless task is clearly moderate+ (e.g. batch URL fetch, file ops); escalate to parent on failure.
- **Automated:** Heartbeats and simple cron → Tier 1; scheduled reports → Tier 1 or 2 by complexity; alert response → start Tier 2, escalate if needed.
- **Lobster:** No change to when we use lobster (watering, trades, posting); model-hierarchy only affects *which model* is used for the agent turn that *triggers* the pipeline.

### 4.4 Anti-Patterns to Encode

- Don’t run heartbeats on the thinking/premium model.
- Don’t use premium for: HAL curl, sensor logging, file read/write, status checks.
- **Don’t use GLM 5 (or any text-only Tier 1/2 model) for image/vision tasks** — no plant photo analysis, nano-banana-pro, screenshot parsing, or image-in prompts; route those to a vision-capable model.
- Do use `model-usage` skill to track cost per task type over time and tune tiers.

---

## 5. Config / Process Changes (If We Implement)

- **OpenClaw config:**  
  - Option A: No config change; skill is instructional only (agent suggests `/model …` or we rely on fallback order).  
  - Option B: Set `heartbeat.model` to the Tier 1 model explicitly so heartbeat always runs on the cheapest model.  
  - Option C: Add a second agent or cron job profile that uses a cheaper primary for “routine-only” runs (more invasive).
- **Allowlist:** If we add a new OpenRouter model for Tier 1 (e.g. DeepSeek or **GLM 5**), add it to `agents.defaults.model.fallbacks` or as primary for heartbeat. For GLM 5, use the canonical OpenRouter ID (e.g. `openrouter/z-ai/glm-5`; confirm on [OpenRouter Z.AI](https://openrouter.ai/z-ai)). **Kimi K2.5** is already in our config (`openrouter/moonshotai/kimi-k2.5`) and is a strong Tier 1/2 choice for both text and vision.
- **Deploy:** Skill file is under `openclaw-workspace/ganjamon/skills/`; deploy workspace to Chromebook as we do today; no change to `run.py` or HAL.

---

## 6. Risks / Open Questions

- **Token budget:** More “which model?” reasoning could add tokens; keep the skill concise and the decision algorithm short.
- **Wrong tier:** Misclassifying a task (e.g. routine → moderate) could waste cost or hurt quality; we can add domain examples and review with `model-usage` and session logs.
- **Provider limits:** OpenRouter and xAI/Gemini have their own rate limits and cooldowns; tier switching shouldn’t exacerbate 429s (e.g. don’t put all routine on one provider if that provider is already near limit).
- **ClawHub:** Upstream isn’t necessarily on ClawHub; we’re planning a **local** copy under our workspace with our adaptations, not `clawhub install model-hierarchy`.
- **GLM 5 vision:** The skill must explicitly branch on “does this task need image input or vision?” and route those to a vision-capable model (Gemini, Grok, or OpenRouter vision models). Otherwise the agent may pick GLM 5 for a turn that later invokes nano-banana-pro or image analysis and fail or confuse the user.

---

## 7. Implementation Order (When We Do Code)

1. Add `openclaw-workspace/ganjamon/skills/model-hierarchy/SKILL.md` with:
   - Our tier definitions and model names (or “use primary / use fallback” if we keep a single chain).
   - GanjaMon-specific task table (grow, trading, social, A2A, heartbeat, cron).
   - Same decision algorithm and behavioral rules, tuned to our stack.
2. Optionally clone upstream into `cloned-repos/model-hierarchy-skill/` for reference and tests.
3. (Optional) Set `heartbeat.model` in config to Tier 1 model.
4. (Optional) Add one cheaper OpenRouter model to config for Tier 1 if we want real cost split.
5. Document in `docs/OPENCLAW_INTEGRATION.md` or `docs/OPENCLAW_GUIDE.md`: that we use model-hierarchy, where the skill lives, and how we map tiers to our models.

---

## 8. Summary

| Item | Plan |
|------|------|
| **Source** | [zscole/model-hierarchy-skill](https://github.com/zscole/model-hierarchy-skill) |
| **Location** | `openclaw-workspace/ganjamon/skills/model-hierarchy/SKILL.md` |
| **Adaptation** | Tier mapping: **Kimi K2.5** (Tier 1/2 or Tier 3 in a 4-tier scheme), **GLM 5** (Tier 1/2, text-only), **Kimi K2 Thinking** (Tier 3), **Opus 4.6** (Tier 4 frontier if we use 4 tiers); optional **4-tier** split (frontier > open-weight > classic mid > cheap); GanjaMon domains; heartbeat/cron = Tier 1 |
| **Config** | No code change yet; later optional: `heartbeat.model` = Tier 1, or add Tier 1 model to fallbacks |
| **Deploy** | Same as rest of workspace; no run.py or HAL change |
| **Docs** | This plan; later one short section in OPENCLAW_INTEGRATION or OPENCLAW_GUIDE |

No code or config has been changed; this is planning only.
