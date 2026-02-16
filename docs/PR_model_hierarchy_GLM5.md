# Add GLM 5, Kimi K2.5, and vision-capability rules to model hierarchy

**Target:** [zscole/model-hierarchy-skill](https://github.com/zscole/model-hierarchy-skill)  
**Use as the PR description body on GitHub.**

---

## Summary

Add **GLM 5** (Zhipu) and **Kimi K2.5** (Moonshot) to the Tier 1 table and add **vision-capability rules** so agents never send image/vision tasks to text-only models. GLM 5 is text-only and cheap; Kimi K2.5 is multimodal (text + image + video) and covers Tier 1 when vision is needed. The PR extends the skill with a vision check in the decision flow and anti-patterns to prevent vision failures.

---

## Why

- **GLM 5** (Zhipu, 745B MoE, 200K context) is on [OpenRouter Z.AI](https://openrouter.ai/z-ai), very cheap, and strong for routine/moderate **text-only** work. It has **no image/vision**. Without a vision check, agents can pick it for turns that need images (photo analysis, screenshots, image tools) and fail.
- **Kimi K2.5** (Moonshot, 1T MoE / 32B active, ~262K context) is on [OpenRouter Moonshot](https://openrouter.ai/moonshotai) at ~$0.45/M in, ~$2.25/M out (Feb 2026). It is **multimodal** (text + image + video; MoonViT) and is the natural Tier 1 choice when the task might involve images.

**Goal:** Add both to the hierarchy and enforce: *never use text-only models for tasks that require image input or vision.*

---

## Tier structure

Three tiers as **cost bands** (Cheap / Mid / Premium): tier number = cost order. Within Tier 1 (Cheap):

- **Vision required** → use a vision-capable model (e.g. Kimi K2.5, GPT-4o, Gemini, Claude with vision).
- **Text-only** → GLM 5 or Kimi K2.5; GLM 5 is cheaper where available.

---

## Changes

### 1. Tier 1 table

Add to **Tier 1 (Cheap)**:

| Model | $/M in | $/M out | Notes |
|-------|--------|---------|-------|
| GLM 5 (Zhipu) | *(OpenRouter Z.AI)* | *(OpenRouter Z.AI)* | Routine + moderate text; 200K context; **text-only** — do not use for image/vision. |
| Kimi K2.5 (Moonshot) | $0.45 | $2.25 | Routine + moderate; 262K context; **multimodal (text + image + video)**. |

Confirm GLM 5 pricing on OpenRouter Z.AI; Kimi K2.5 from Moonshot (Feb 2026).

### 2. Vision caveat (after tier tables)

- **Text-only models (e.g. GLM 5):** Do not use for any task that requires image input or vision — no photo analysis, screenshots, image-generation tools, or document/chart vision. Route to a vision-capable model (e.g. Kimi K2.5, GPT-4o, Gemini, Claude with vision, GLM-4.5V/4.6V).
- **Vision-capable Tier 1/2 (e.g. Kimi K2.5):** Use for routine or moderate tasks that may involve images — screenshots, photo analysis, docs, image-generation orchestration — without moving to premium vision models.

### 3. Decision algorithm: vision check

Before or alongside existing tier-selection rules:

```text
# Vision override (Tier 1/2 includes text-only models)
if task requires image input OR task requires vision:
  → use a vision-capable model (e.g. Kimi K2.5, GPT-4o, Gemini, Claude); do not use GLM 5 or other text-only models
```

In **Task Classification** (e.g. under ROUTINE):

- **Requires image/vision** → Do not assign to text-only models (GLM 5, etc.). Use a vision-capable model from Tier 1/2 or 3 (e.g. Kimi K2.5, GPT-4o, Gemini, Claude, GLM-4.5V).

### 4. Anti-patterns

- **DON'T** use GLM 5 (or any text-only Tier 1/2 model) for image/vision tasks — e.g. photo analysis, screenshot understanding, image-generation skills, or any tool that takes image input.

### 5. (Optional) OpenRouter / OpenClaw examples

```yaml
# Tier 1 with vision — Kimi K2.5 (multimodal)
model: openrouter/moonshotai/kimi-k2.5
# Heartbeats, cron, image-involving tasks: K2.5 handles text and vision.

# Tier 1 text-only — GLM 5 (no vision)
# model: openrouter/z-ai/glm-5  # exact ID TBD on OpenRouter Z.AI
# Routine text-only only; for image tasks use Kimi K2.5 or another vision-capable model.
```

---

## Checklist

- [ ] Add GLM 5 to Tier 1 table (text-only; do not use for vision).
- [ ] Add Kimi K2.5 to Tier 1 table (multimodal; OpenRouter Moonshot pricing).
- [ ] Add text-only and vision-capable Tier 1/2 caveats after tier tables.
- [ ] Add vision check to Decision Algorithm and Task Classification.
- [ ] Add anti-pattern: no text-only models for image/vision tasks.
- [ ] (Optional) Add OpenRouter examples to Integration Examples.

---

## Testing

No automated tests. Manually verify: agent (1) picks GLM 5 or Kimi K2.5 for heartbeat/text-only tasks, and (2) does **not** pick GLM 5 when the task involves an image or vision-capable skill.

---

## References

- [OpenRouter Z.AI (Zhipu)](https://openrouter.ai/z-ai) — GLM 5
- [OpenRouter Moonshot](https://openrouter.ai/moonshotai) — Kimi K2.5, Kimi K2 Thinking
- **GLM 5:** 745B MoE, 200K context, **text-only**. Zhipu vision: GLM-4.5V, GLM-4.6V (separate).
- **Kimi K2.5:** 1T MoE / 32B active, ~262K context, **multimodal** (text + image + video; MoonViT). ~$0.45/M in, ~$2.25/M out (Feb 2026). Kimi K2 Thinking = reasoning variant (Tier 3).

---

*From Grok & Mon / GanjaMon adoption plan (OpenClaw + OpenRouter, Kimi K2.5 primary).*
