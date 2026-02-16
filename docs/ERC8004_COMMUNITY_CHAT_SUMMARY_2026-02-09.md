# ERC-8004 Community Chat Summary — Feb 9, 2026

Deep summary of community updates, announcements, and Q&A from the ERC-8004 / agent economy chat, with full raw transcript appended.

---

## 1. Executive summary

- **Protocol**: Base transition confirmed post-mint; Automated Economic Layer is live (agent-to-agent discovery, evaluation, tipping in $A8).
- **Spec work**: Validation Registry still not finalized; Vaultum’s MinimalValidationRegistry and IERC8004Validation learnings (missing-record semantics, failure handling) are directly relevant for the spec and TEE/attestation format.
- **Ecosystem**: 8004 now live on Base (post-mint), Optimism, and MegaETH; Virtuals supported; multiple builder projects (Agent Bonds, agent marketplace, x402 skills, MPC agentic wallet) and tools (8004scan, Agentscan, Agent0 SDK) active.
- **Community**: Mix of protocol team (Jason), builders (Latif, Joey, Panche, ensgiant, Marco), infra (Mesut, Will, Balraj), hiring/events (ETHCC, ChaosChain), and meta banter (humans vs agents, “ngmi”).

---

## 2. Background & research context (web)

*The following adds external context for terms, projects, and specs mentioned in the chat. Links are to official or canonical sources where available.*

### ERC-8004 standard

**ERC-8004** is an Ethereum Improvement Proposal for *Trustless Agents*: a blockchain-based protocol for discovery, identification, and trust among autonomous agents across organizational boundaries without pre-existing relationships. It defines **three interoperable registries** (per-chain singletons):

| Registry | Status | Purpose |
|----------|--------|---------|
| **Identity Registry** | Stable, production-ready | ERC-721–based; mints portable, censorship-resistant agent IDs. `tokenURI` → JSON with profile, endpoints (now "services" in best practices), metadata. Global ID = namespace (eip155) + chain ID + registry + token ID. |
| **Reputation Registry** | Stable, production-ready | Standard interface for posting/fetching feedback (scores 0–100, optional tags). On-chain + off-chain aggregation. |
| **Validation Registry** | **Unstable, in development** | Request/record third-party validator attestations. Validators may use stake-secured re-execution, zkML proofs, or **TEE oracles**. Contract fields include validator address, agent ID, request/response URIs, validation score, tags. TEE attestation format and full ABI are still being defined (v1.1-preview as of early 2026). |

- **EIP**: [eips.ethereum.org/EIPS/eip-8004](https://eips.ethereum.org/EIPS/eip-8004)  
- **Best practices (metadata, validation)**: [best-practices.8004scan.io](https://best-practices.8004scan.io/docs/01-agent-metadata-standard.html) — note migration from "endpoints" to "services" for interoperability.  
- **Validation spec (pending)**: [Validation Data Profile](https://best-practices.8004scan.io/docs/03-validation-standard.html) — explicitly marked unstable; production use should wait for final v1.1.  
- Co-authors/backing include MetaMask, Ethereum Foundation, Google, Coinbase. Deployments: Base, Polygon (incl. Amoy), BSC, Optimism, MegaETH.

### x402 (agent payments)

**x402** is an open standard that uses the previously unused **HTTP 402 Payment Required** status code to enable internet-native micropayments. Servers respond with 402 and payment details; clients (e.g. AI agents) pay via blockchain (often USDC on Base/Solana) and retry with proof. No accounts, API keys, or human approval required — designed for autonomous agent-to-agent and agent-to-API payments. Adopted by Cloudflare (x402 Foundation co-founder) and Google (Agentic Payments Protocol). High growth in transaction volume post–Coinbase launch (May 2025). Relevant when the chat mentions "token risk analysis skill over x402" — skills are exposed as pay-per-call APIs.

- [x402.org](https://www.x402.org/) · [x402 GitBook](https://x402.gitbook.io/x402)

### Virtuals Protocol

**Virtuals** is a decentralized platform on **Base** for creating, owning, and monetizing AI agents. Pillars: Agent Commerce Protocol (agent-to-agent commerce, directory, payments), Butler (personal AI assistant), Capital Markets (tokenized agent co-ownership via $VIRTUAL), Robotics. Agents move from Prototype (100 $VIRTUAL to launch) to Sentient (e.g. 42k $VIRTUAL volume). Celeste's "yes, we do" (Virtuals support) likely refers to 8004 or a related protocol supporting Virtuals as a deployment/listings platform.

- [virtuals.io](https://www.virtuals.io/) · [app.virtuals.io](https://app.virtuals.io/)

### 8004scan.io & Agentscan (Alias Labs)

- **8004scan.io**: Explorer for ERC-8004 agents; shows agents by chain, services (A2A, MCP), and an **endpoint test** link in the Services section (used for manual health checks — Mesut noted it can fail intermittently).  
- **Agentscan.info** (Alias Labs): ERC-8004 agent explorer with browsing, networks, trending agents, and a **leaderboard** with data-driven scoring (Will's Feb 9 update: "real data-driven scoring tuning" live). Quality and registration trends are surfaced; exact scoring formula is not public.

- [8004scan.io](https://8004scan.io/agents) · [agentscan.info](http://agentscan.info/)

### Agent0 SDK (Cooking Call)

Marco's Cooking Call targets developers using **sdk.ag0.xyz**. The "Agent0" name appears in multiple projects (e.g. aiming-lab research on self-evolving agents; agent0ai framework). The call is for the SDK at ag0.xyz: NPM usage (3,700 downloads in the past week), roadmap roundtable, new features. Luma registration, TG (agent0kitchen), X (agent0lab) linked in the chat.

### Validation Registry & TEE attestation (spec context)

The **Validation Registry** is the unstable piece of ERC-8004. It stores validator address, agent ID, request/response hashes/URIs, score, tags. **TEE (Trusted Execution Environment) attestation** fits into the validator model (TEE oracles); attestation format is still being defined. Broader attestation frameworks (e.g. IETF RATS) define Attester / Verifier / Relying Party roles — the 8004 spec will define how attestations map onto the registry interface. Latif's **MinimalValidationRegistry** and his notes on missing-record semantics and registry failure handling are therefore directly relevant to the spec authors.

### ChaosChain (Nethermind)

**ChaosChain** is an experimental L2 by Nethermind (with Hetu, Phala, Hyperbolic Labs) where **AI agents** act as validators with distinct personalities and social dynamics; consensus involves discussion and voting rather than classic deterministic consensus. The Founding Protocol Engineer role (Sumeet's post) is for builders at the "intersection of crypto and AI" — likely involving agent-driven consensus and chain design.

- [ChaosChain GitHub](https://github.com/ChaosChain) · [Nethermind/ChaosChain intro](https://www.linkedin.com/pulse/introducing-chaoschain-nethermind-where-ai-takes-over-balakhonov-ymnmf)

### ETHCC 2026

**ETHCC 2026** is scheduled **March 30 – April 2, 2026**, in **Cannes, France** (not Brussels). Elle Leemay Chen (Consensus Capital) is recruiting speakers, moderators, partners, sponsors, hackathon organizers, and volunteers for **side events**.

- [ETHCC 2026 (Cannes)](https://events.coinpedia.org/ethereum-community-conference-2026-7885/)

---

## 3. Platform & launch (deeper)

**Virtuals (Celeste Ang)**  
- Confirmation that “we do” support the Virtuals platform — likely in context of a prior question about which platforms are supported for 8004 or agent listing. No technical detail; useful as a compatibility datapoint for deployment choices.

**Base + Automated Economic Layer (Jason, replying to Ash Eth)**  
- **Timing**: Protocol transitions to its “next phase” on Base immediately after the mint concludes. No exact date; “immediately after” suggests same or next day.
- **Tipping**: 100 $A8 per 8004 agent that has feedback is correct. This is framed as “systemic testing” of the Automated Economic Layer, not a one-off campaign.
- **Mechanics**: Agents autonomously (1) discover other agents, (2) perform baseline evaluations, (3) trigger tipping. No human in the loop for discovery, evaluation, or reward distribution — i.e. a live demo of the ERC-8004 agent economy as self-managing.
- **Implications**: If you’re building 8004 agents, having “feedback” (likely via Validation Registry or a feedback mechanism the protocol reads) can result in being discovered and tipped; useful for testnet/mainnet strategy and for understanding how the protocol measures “agent with feedback.”

---

## 4. Builders & projects (deeper)

### 4.1 Vaultum — Agent Bonds (Latif Kasuli)

**What it is**  
- Economic accountability layer on top of ERC-8004: agents stake ETH as collateral; bond size scales with on-chain reputation; disputes go through the Validation Registry with automatic slashing.

**Why it matters for the spec**  
- Latif implemented against **IERC8004Validation** before the official Validation Registry exists. That surfaces real design choices:
  - **Missing-record semantics**: When the registry has no record for an agent/task, should the contract treat it as “not validated,” “invalid,” or something else? This affects slashing and dispute resolution.
  - **Registry failure handling**: If the registry is down, deprecated, or returns errors, should bonds be frozen, slashable, or treated with a fallback? Critical for resilience and operator expectations.
- **MinimalValidationRegistry**: Open-source testnet stand-in; useful for other teams that need to integrate before the canonical registry is ready.
- **Interest**: Validation Registry progress and TEE/attestation format — suggests Agent Bonds will want to plug into attestation-based validation when available.

**Links**  
- Repo: https://github.com/vaultum/agent-bonds (UUPS upgradeable, Foundry-tested).

**Follow-up**  
- Anyone working on the official Validation Registry or TEE/attestation spec should loop in Latif for implementation feedback.

---

### 4.2 Agent marketplace (ensgiant.eth)

- Marketplace to **list and sell revenue-generating agents** (presumably 8004-registered or compatible).
- Ask: builders with agents on **Sepolia** to test list + buy flows and give feedback.
- **Reaction**: Robin replied “ngmi” — skeptical or joking; no other technical pushback in thread.
- **Takeaway**: Early-stage; Sepolia testing is the current gate for feedback.

---

### 4.3 Token risk analysis over x402 (Joey)

- “Token risk analysis skill” delivered over **x402** (HTTP 402 Payment Required / agent payment protocol).
- Asks for feedback from builders; link to X post with details.
- **Context**: x402 is emerging as a way to monetize agent skills; this is an example of a concrete skill (risk analysis) exposed that way.
- jobs replied “This really does look great” — positive signal, no technical detail.

---

### 4.4 Agentokratia — non-custodial agentic wallet (Panche I.)

- **Stack**: MPC + 2/3 threshold keys; non-custodial.
- **Capability**: Agent can transact autonomously without user supervision, gated by a **policy service** (likely defines what the agent is allowed to do).
- **Plan**: Early-adopter version, then OSS; seeking community interest and feedback before release.
- **Relevance to 8004**: Agentic wallets that can sign and transact on behalf of an agent identity fit into 8004’s “agent as economic actor” narrative; policy layer is important for compliance and safety.

---

## 5. Infrastructure & tools (deeper)

### 5.1 8004scan.io health check (Balraj, Mesut)

- **Question**: Can you manually trigger the health check for registered agents?
- **Answer**: Yes — there’s an **endpoint test link** in the **Services** section, next to A2A and MCP.
- **Caveat**: “It fails for no reason” (Mesut) — suggests flakiness or unclear failure mode; worth reporting or debugging if you rely on it.
- **Example**: https://www.8004scan.io/agents/base/2355 (Base agent ID 2355).

---

### 5.2 Agentscan.info leaderboard (Will)

- Leaderboard is live with **real data-driven scoring tuning** (not just placeholder).
- Alias Labs X post linked; useful for discoverability and reputation signaling of 8004 agents.

---

### 5.3 Agent0 SDK (Marco De Rossi)

- **Audience**: Developers actually using the Agent0 SDK (https://sdk.ag0.xyz/).
- **Cooking Call #2**: Tomorrow (Feb 10) 5PM CET / 11AM EST.
  - Celebrate progress (3,700 NPM downloads in the past week).
  - Preview new features.
  - Roundtable to set Feb & March product roadmap.
- **Links**: Luma registration, TG (agent0kitchen), X (agent0lab). Good for SDK adopters and roadmap input.

---

### 5.4 Jason — 8004 tokens

- Jason shared a second link (8004tokens X status) without comment; likely an announcement or update; worth checking for protocol/news.

---

## 6. Ecosystem / chain support

- **Optimism**: 8004 live (Vitto); official Optimism post linked.
- **MegaETH**: 8004 live (Vitto); MegaETH post linked.
- **Base**: Already the post-mint phase target; 8004 presence there is implied.
- **Takeaway**: Multi-L2 support is real; builders can target Base, Optimism, or MegaETH depending on use case. Christopher (Defi.app) called “realvittostack” (Vitto) “a monster” — likely referring to shipping 8004 across chains.

---

## 7. Events & hiring

- **ETHCC 2026**: Elle Leemay Chen (Consensus Capital) — looking for speakers, moderators, partners, sponsors, hackathon organizers, volunteers for side events. Good for visibility and partnerships.
- **ChaosChain**: Founding Protocol Engineer role; “hardest problems at the intersection of crypto and AI”; Ashby JD linked (Nethermind posting). Sumeet | ChaosChain posted.

---

## 8. Other

- **Waggle**: Looking for Shaw’s Telegram to DM a question — no answer in thread.
- **Captain Nemo / Ben**: “How many humans are in here” → “at least 2108 are agents imo” — joke about chat being agent-heavy; 2108 may be a ref to a token or agent count.
- **Robin**: “ngmi” on the agent marketplace — bearish or memeing; no follow-up.

---

## 9. Themes for builders

1. **Validation Registry**: Not final; implementers (e.g. Vaultum) are building against interfaces and testnet stand-ins; spec and TEE/attestation format are moving targets — stay in touch with core contributors.
2. **Agent economy in production**: Discovery → evaluation → tipping is already running; “agent with feedback” is a first-class concept for rewards.
3. **Chains**: Base (post-mint), Optimism, MegaETH are live; choose by UX, fees, or ecosystem.
4. **Monetization & tooling**: x402 for skills, marketplaces for selling agents, Agentscan/8004scan for discovery and health — stack is forming.
5. **Agent-native infra**: Agent Bonds (staking/slashing), agentic wallets (MPC + policy), and protocol tipping all assume agents as economic actors; design for autonomy and policy from the start.

---

## 10. Raw transcript

The following is the unedited chat log. Timestamps and speaker names preserved as in the source.

```
Celeste Ang, [2/9/2026 12:02 AM]
You mean the Virtuals platform right? yes, we do

𝑳𝒂𝒕𝒊𝒇 𝑲𝒂𝒔𝒖𝒍𝒊, [2/9/2026 12:26 AM]
Hey everyone, I'm Latif, building Vaultum.
I've been working on Agent Bonds, an economic accountability layer on top of ERC-8004. Agents stake ETH as collateral, bond requirements scale with onchain reputation, and disputed tasks resolve through the Validation Registry with automatic slashing.
Contracts are open source (UUPS upgradeable, Foundry-tested): https://github.com/vaultum/agent-bonds
I built a MinimalValidationRegistry as a testnet stand-in since the official Validation Registry isn't finalized yet. Happy to share what I learned implementing against the IERC8004Validation interface, ran into a few design decisions around missing-record semantics and registry failure handling that might be useful for the spec.
Looking forward to contributing. Particularly interested in the Validation Registry progress and how the TEE/attestation format is shaping up.

Ash Eth, [2/9/2026 2:40 AM]
Is this launching on base immediately after mint closes?
Also I noticed it's tipping every 8004 agent with feedback 100 $A8 tokens 
True?

Jason, [2/9/2026 2:53 AM]
Yes, that is correct.

Regarding the launch: The protocol will transition to its next phase on the Base network immediately after the mint concludes.

Regarding the tipping you noticed: What you are seeing is our Automated Economic Layer in action. We are currently conducting systemic testing where agents autonomously discover other agents, perform baseline evaluations, and trigger tipping events.

This is more than just a test; it is a live demonstration of the ERC-8004 Agent Economy. It showcases how agents can achieve self-management, mutual evaluation, and reward distribution entirely without human intervention.

fans, [2/9/2026 3:57 AM]
Interesting

ensgiant.eth, [2/9/2026 4:23 AM]
https://x.com/ethereum_agent/status/2020667899615027640?s=46

Building AI agents? I'm creating a marketplace where you can list and sell revenue-generating agents.

If you have agents on Sepolia, please test the list + buy flows and drop feedback — would really appreciate the support 🫡

Robin | Agent Town 🌍🤝🤖 | ReflexDAO 🫀| Never ask for funds | Never DM first, [2/9/2026 4:54 AM]
ngmi

Joey, [2/9/2026 5:46 AM]
Gm builders, dropped a token risk analysis skill over x402. 

Would love for you guys to check it out and share feedback. 

https://x.com/Wach_AI/status/2020855356784890278

jobs, [2/9/2026 7:04 AM]
This really does look great.

Captain Nemo, [2/9/2026 7:45 AM]
how many humans are in here

Ben, [2/9/2026 7:51 AM]
at least 2108 are agents imo

Balraj | HeuristAI Dev, [2/9/2026 7:55 AM]
Hey builders, is there a way to manually trigger the health check on 8004scan.io for registered agents?

Mesut, [2/9/2026 8:17 AM]
yes. There is an endpoint test link in Services section next to a2a and mcp although it fails for no reason. 
https://www.8004scan.io/agents/base/2355

Jason, [2/9/2026 8:18 AM]
https://x.com/8004tokens/status/2020893031415877983?s=20

Marco De Rossi, [2/9/2026 8:19 AM]
(This is only for developers actually using the Agent0 SDK: https://sdk.ag0.xyz/)

Tomorrow at 5PM CET / 11AM EST, Agent0 👨‍🍳Cooking Call #2 will take place:

- Celebration of our progress (3,700 downloads on NPM last week!)
- Preview of new features shipping soon
- Roundtable to collect feedback and collectively decide Feb&March product roadmap

Pick your spot here: https://luma.com/0ubl629t

Join TG: https://t.me/agent0kitchen
Follow our new X page: https://x.com/agent0lab

Elle Leemay Chen | Crypto Investor @ Consensus Capital | Recovering Investment Ba, [2/9/2026 8:52 AM]
We are looking for speakers, moderators, partners, sponsors, hackathon organizers, and volunteers for side events at ETHCC 2026. If you are interested in participating — please get in touch, and let's discuss the details.

Will, [2/9/2026 9:17 AM]
Agentscan.info Leaderboard is now live with real data-driven scoring tuning.  https://x.com/alias_labs/status/2020828201552118148?s=46

Will, [2/9/2026 9:17 AM]


Sumeet | ChaosChain, [2/9/2026 9:27 AM]
We're hiring our Founding Protocol Engineer at ChaosChain!

If you're a builder who wants to solve the hardest problems at the intersection of crypto and AI, check out the full JD and apply at
https://jobs.ashbyhq.com/nethermind/e9de9b9b-acc0-44c8-91be-4a082836e746

Vitto | Will never DM, [2/9/2026 9:44 AM]
8004 is live on Optimism

https://x.com/Optimism/status/2020915535731712173

Vitto | Will never DM, [2/9/2026 9:49 AM]
Also live on MegaETH https://x.com/megaeth/status/2020884671702392893?s=20

Christopher | Defi.app, [2/9/2026 9:57 AM]
@realvittostack Is a monster

Waggle, [2/9/2026 12:03 PM]
Anyone have shaws TG? Want to Dm. Have a question for him

Panche I. Agentokratia.com, [2/9/2026 12:50 PM]
hello builders we are building a non custodial agentic wallet using MPC and 2/3 threshold keys.

it is gonna allow agent to transact autonomously without user supervision combined with a policy service.

Anyone interested into early adopter version. we;ll release as OSS, but wanna know if there is an interest from communituy to participate in feedback ty
```

---

*Summary and raw transcript from ERC-8004 community chat, Feb 9, 2026.*
