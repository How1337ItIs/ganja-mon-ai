# ERC-8004 Builders Chat — Full Summary & Context

**Scope:** Full Telegram export of the **8004 Builders** (ERC-8004 Builders) group from **3 September 2025** through **9 February 2026**, with section-by-section synopsis, web-research context, and reference to the raw transcript.

**Source:** `C:\Users\natha\sol-cannabis\ChatExport_2026-02-09` (messages.html … messages6.html).  
**Extracted transcript:** `ChatExport_2026-02-09/transcript.txt` (~3,490 message entries).

**Session roadmap:** This doc is built in multiple passes. Sessions 1–3: extraction, topic index, Sept 2025–Feb 2026 deep-dives. Session 4: topic expansion + Key quotes (§6). Optional: transcript line ranges for key dates.

---

## Table of contents

| Section | Content |
|--------|--------|
| 1 | Executive summary (full chat) |
| 2 | Section-by-section synopsis (with deep-dives for Sept–Oct) |
| 2.1 | September 2025 (deep: weeks 3–9, 10–16, 17–23, 24–30) |
| 2.2 | October 2025 (deep: pre-v1, v1 launch, post-v1) |
| 2.3–2.6 | November 2025 – February 2026 (summary; deep in later sessions) |
| 3 | Background & research context (web) |
| 4 | Raw transcript (path + format) |
| 5 | Themes (cross-cutting) |
| 6 | Key quotes (by theme) |
| 7 | Sample of raw format |
| 8 | Topic index & session plan (multi-session roadmap) |

---

## Topic index (find by theme)

| Topic | Where in doc / transcript |
|-------|---------------------------|
| **ERC-8004 spec / EIP** | §2.1 (Sept), §2.2 (v1 Oct 9), §3.1; EIP link in Sept 4 Marco message |
| **TEE (Phala, Oasis, Talos, attestation)** | §2.1 (Sept 4–11), first community call Sept 23; Wyatt Benno zkML; Tim Williams TEE debate; Phala response to SGX |
| **x402 / agent payments** | §2.1 (Loaf, Unwallet, 4Mica, Pinata); §2.2 (b402 scam, NYC meetup Oct 21); MetaMask x402 Sept 17 |
| **Validation Registry / dispute / reputation** | §2.1 (cottenio dispute proposal, sybil threat model); §2.5 (validation tiers); recursive.so kirsten |
| **ChaosChain (reference impl, Genesis Studio, SDK)** | §2.1 (Sept 4–5, 9, 17, 21, 24–27); §2.2 (v1 Oct 9); trustless-agents-erc-ri, chaoschain-genesis-studio |
| **First community call (Sept 23)** | §2.1.3; Jess slides/recording; cottenio dispute simulator; Wyatt zkML; Praxis, bond.credit, Sparsity, Phala demos |
| **ERC-8004 v1 live (Oct 9)** | §2.2; Marco thread + press release; ChaosChain v1 RI; LXDAO co-learning + hackathon |
| **8004scan / Agentscan / explorers** | §2.3 (v2 Nov), §3.6; YQ, Will, Alias |
| **Devconnect Buenos Aires (Nov 17–22)** | §2.3; Agentic Zero (Pili); Marco DePIN Day, TEE.salon, Agents Unleashed |
| **Mainnet / multi-chain** | §2.4–2.6; Base, Optimism, MegaETH, Monad |
| **Virtuals ACP / Agentokratia / OpenClaw** | §2.5, §2.6; Celeste, Panche, Moltbook, clawnews |
| **Scams & safety** | §2.2 (fake b402); §2.5 (angel/phishing); Robin neutrality |
| **Privacy (stealth, privacy pools)** | §2.1 (Unwallet, Binji/wilwixq); §2.2 (mitchuski) |
| **Builder program / grants** | Sept 18 (Isha, builder program); Oct 6 (Devconnect Builder Program, $157k Thirdweb, etc.) |
| **Agentic Trust / Rich Pedersen** | §2.1 (Sept 5 MetaMask hackathon), §2.3 (Agentic Trust + ENS/DIDs), §2.5 (ontology, mandates) |
| **Alias / StarCard / Agentscan** | §2.3 (StarCard→ERC-8004 NFT), §2.5–2.6 (Agentscan, Transaction Analytics) |
| **WachAI / Hardik / Mandates** | §2.5 (Verification Protocol whitepaper), §2.6 (WachClaw, Mandates Clawhub skill) |
| **MONTREAL AI / AGI Alpha / AGIJobs** | §2.5 (AGIJobManager deck), §2.6 (enforcement, replayable proof, GhØsT_PilØT_MD) |
| **create-8004-agent / Vitto** | §2.4 (npx create-8004-agent), §2.5 (Vitto joined team, ecosystem form, Base Sepolia) |
| **ClawLoan / Francesco** | §2.6 (live Base mainnet, 8004 reputation testing) |
| **ElizaTown / Robin** | §2.6 (OpenClaw + ERC-8004, Agent Town) |
| **OyaChat / John Shutt / Commitments** | §2.5 (plain-language onchain, Safe + UMA OG, agent allowlist) |
| **XMTP / Fabri** | §2.5 (e2ee agent messaging layer for 8004) |
| **ETHCC 2026 Cannes** | §2.6 (side-events recruitment Feb 9); §3.8 |

---

## 1. Executive summary (full chat)

- **Origins:** Marco De Rossi and Davide Crapis welcomed the community in Sept 2025; the EIP was still a draft. Focus: decentralized AI on Ethereum, permissionless innovation, and trustless agent identity/reputation.
- **Milestones:** ERC-8004 **v1 went live** (Oct 2025); spec moved draft → review; **8004scan.io v2** launched at Devconnect (Nov 2025); **mainnet** preparation and multi-chain deployment (Base, Optimism, MegaETH, etc.) through early 2026; **Genesis month** (Feb 2026) and protocol phase transition on Base post-mint.
- **Ecosystem:** ChaosChain reference implementation, TEE-based agents (Phala/Oasis/Talos), x402 payment rails, Virtuals ACP, OpenClaw/Moltbook, Agentokratia, Agentic Trust, Alias/Agentscan, 8004scan, Agent0 SDK, and many builders (Vistara, bond.credit, WachAI, Montreal AI, etc.). Validation Registry remains unstable; discussion on validation tiers (receipt vs. proof vs. quality) and TEE/attestation.
- **Events:** Community calls, NYC x402 meetup, **Devconnect 2025 Buenos Aires** (Nov 17–22), LXDAO co-learning & Casual Hackathon, Patchwork “Syncing on AI Standards,” BUIDL Europe/Lisbon, ETHCC 2026 Cannes side-events recruitment.
- **Themes:** Identity + reputation + validation; agent-to-agent (A2A) + x402 + 8004 stack; discovery and explorer tools; scams/fake projects (e.g. fake b402); privacy (stealth, privacy pools); mainnet timeline and ecosystem mapping.

---

## 2. Section-by-section synopsis

### 2.1 September 2025 (deep)

**2.1.1 Week of Sept 3–9**

- **Welcome (Sept 3):** Marco De Rossi & Davide Crapis pinned the welcome: *"The spec is still a draft—definitely not perfect—but your energy makes one thing crystal clear: we all see the risks of centralized AI, and we're determined to build an AI stack on Ethereum rails where—just like in DeFi—anyone can innovate permissionlessly."* Invite to share who you are, what sparked interest, or where you might apply 8004.
- **Intros (Sept 3–5):** Christopher | Defi.app (@bigironchris, awareness); validator.eth Kev (ENS subnames for agents); Mike Anderson (ThinkAgents.ai, independentai.institute, reviewing release); Yash Agarwal (asked for draft link); Trev (GM buildoors); **Loaf** (x402 inference/service, router.daydreams.systems, *"non kyc, onchain way to pay for web2 services"*); leonprou (agentic marketplace, integrating x402); **Abhishek | 0xabhii** (Unwallet: x402 + ERC-5564 stealth addresses, *"private revenue streams (<$0.01 on L2s)"*, A2A demos); Praise (DeFi strategy execution with agents); **Sumeet | ChaosChain** (first reference impl: https://github.com/ChaosChain/trustless-agents-erc-ri, deployed Ethereum, Base, Optimism Sepolia; mint passport: chaoschain.github.io/trustless-agents-erc-ri); **cap | namespace** (ENS Subname infra, universal AI agent registry prototype); Viraj Patva (SSI, secure auth for agentic flow); **Andrei | Warden** (300k+ DAU, identity & discovery for agent ecosystem); Fra Mosterts (Chainbound); Shawn Cheng (Brooklyn); **Marko | Oasis** (Talos TEE, treasury agent on Arbitrum, TIP-0005, github.com/talos-agent); **Marco** shared EIP draft: https://eips.ethereum.org/EIPS/eip-8004; **Matt | Pinata** (IPFS for agent state, interest from AI agents); leonprou (IPFS + subgraph: goldsky ensemble-subgraph); **Marco** (first TEE-based 8004 impl: github.com/HashWarlock/erc-8004-ex-phala, Phala tee_base/server/validator_agent, credit @yozkyo @h4x3rotab); Marko (Talos TIP-0005, DEPLOYMENT.md); Cameron Dennis (NEAR AI, AITP, confidential ML); Johnny Empyreal (Talos in TEE, Oasis ROFL, *"fun to do something socially integrated"*); Sumeet (use ChaosChain contracts, more hardened; IPFS for agents, x402 for storage); **M3ch@n1st** (Praxis, scalable infra for decentralized AI agents); **Akash | 4Mica** (payment infra for agents, x402-based); **Mayur | Z | Vistara** (earnings loop, ~2k apps, Zara AI Factory, Fire Alarm + Ship-2-Earn demo); Spencer Graham (Hats Protocol, onchain roles/permissions for agents); **Marco** (top 10 use cases: X summary, Medium deep-dive); wilwixq (Oasis, TEE call interest); Mike Anderson (Spencer legit on agent governance); Frank (Heurist AI); Bernardo (replicats.ai, quant + LLM + chain portfolios); Joshua (bonfires.ai, Bonfire for coordination); Binji (storytelling); **Sumeet** (Genesis Studio Base Sepolia: agents get wallets, on-chain IDs, verifiable work on IPFS, USDC payment, Story Protocol royalties; thread + repo chaoschain-genesis-studio).
- **Rich Pedersen (Sept 5):** MetaMask Hackathon entry — ERC-8004 Agent Identity Explorer & Manager, no user wallet (Web3Auth, MetaMask Delegation, AA); Linux Foundation A2A + ChaosChain contracts. Davide cc Sumeet; Marco cc MetaMask folks; Sumeet (explore integration with Genesis Studio).
- **Weekend (Sept 7–8):** Marco (Phala erc-8004.com "Trustless AI Code Review"; interactive explorer link); **Matteo** (digital twin vs memory layer, TEE, control plane vs data plane — long technical post); Rich (ENS domain name in Agent Identity Service, eais repo); **Marco** (Binji thread); **Marco** (ERC-8004 on Olas Agents Unleashed podcast: *"Reality check: we throw agent around a lot. Most of what ships are smarter interfaces. Truly autonomous, goal-seeking agents are rare."* 8004 tackles distribution, open market, portable/discoverable/trustable); **Jay Prakash | Silence Laboratories** (private/verifiable A2A, 8004 backbone, DeCompute Singapore Sept 30); Ash Eth (cortensor, ETH-aligned AI); **Binji** (privacy categories — people, developers, institutions, society); wilwixq (For AI: *"Privacy ensures AI can act on behalf of users without exposing sensitive inputs, outputs, or keys"*; Talos example); Abhishek (Unwallet framing: agents shouldn’t leak ownership, revenue, strategies).
- **Sept 9:** Ash Eth (ERC-8004 infestation tweet); Sumeet (65+ agents on 8004 contracts, *"Let's get to 100"*); Mayur (demo); **cottenio | Tim @ Scrypted** (genai/creative with privacy/payments); **Marco** (memory/superpower take: cross-app and cross-user memory, crypto-enabled primitives, *"No need to choose between great AI UX and privacy"*); Matt | Pinata (receiving payment for delivering x — who fits?); pinky [mrdn]; Mayur (decentralized task protocol, 8004 + x402, deliver X → get paid, Fire Alarm demo, autonomous task marketplace); Marco (which 8004 trust model? reputation + x402 proof?); Mayur (reputation first, x402 proof, Irys + EAS attestation, stake-secured for higher stakes).

**2.1.2 Week of Sept 10–16**

- **Sept 10:** Marco (8004 on Google Blog — developers.googleblog.com A2A extensions); Joshua (offer ERC-8004 a Bonfire for coordination); **Marco** (stack-ranked spec priorities, Magician discussion ethereum-magicians.org/t/erc-8004-trustless-agents/250983, **structured builders program** in the works, TEE call 8:45 AM PT / MCP 9:30 AM PT, use cases post Medium); Angela (best place to learn for newbie); **Billy** (agent-rank, EigenTrust-inspired); Marco (EigenTrust paper, distributed reputation); **Tim Williams** (TEE/SEV vulnerabilities, LinkedIn post); Johnny Empyreal (lone TEE issue; what’s the alternative?); Jay Prakash (Silence Labs ++); Tim (why prioritise MCP and TEE when fragile?); Jay (*"Specs should not champion a technology. Should suggest expectations of trust and behaviour."*); Johnny (8004 tech agnostic); Mike Anderson (what problems do we assume TEE solves?); Johnny (local/consensus); Mike (going local, private, open source, agentic browser .exe/.dmg soon); h4x3rotab (TEE way to secure agents, no better replacement; later: article assumes only TEE — other solutions don’t conflict); Tim (don’t ONLY trust TEEs; TEE + blockchain verification); h4x3rotab (that’s what 8004 is proposing); wilwixq (Oasis ROFL off-chain TEE attests to chain).
- **Sept 11:** **Marko | Oasis** (as user, trust = execution integrity, key management, reproducibility, upgradability transparency, multi-sig); **Marco** (housekeeping: 200+ people, high-signal; 30+ notifications on TEE — *"skim EIP-8004. Answer: 8004 defines a validation registry. It's not TEE-specific."* Condense shares, no shilling); Tim Williams (use case distinction resolved); Rich (LinkedIn); Zcash Daily News.
- **Sept 12:** Marco (Forbes: "The Table Stakes For Crypto x AI: Discoverability And Interoperability"); Rich (did:web + ERC-8004 agent address for counterparty verification, ERC-1271); Ash Eth; Johnny (ERC-1271); **//allen.day** (A2A registries, a2a-registry.dev, protobuf3-solidity).
- **Sept 13–14:** Tim (1271 multi-sig); //allen.day (8004 method signatures → proto rpc for polyglot?); Rich (MCP Agent demo, did:agent, Veramo, ERC-8004 anchor — github.com/RichCanvas3/did-agent); Davide (welcome Morris & Wilson, TensorBlock); Miratisu (Virtuals Protocol); Loaf.
- **Sept 15:** cottenio (hi Loaf, Miratisu); **Swayam Karle** (A2A vs MCP + EIP-8004 + x402 — X thread); cottenio (Jan 2024 autonomous virtual beings, sequel around ERC-8004); **Marco** (*"Official: from today Ethereum Foundation has an AI team. First focus: advancing ERC-8004."* Davide announcement); Tim Williams (repost); cottenio (8004 + x402 link X).
- **Sept 16:** Matt | Pinata (validation requests: one big file scalability?); **Marco** (Save the date — **ERC-8004 Community Call #1**, Tue Sep 23, 17:00 CEST / 08:00 PDT); Marko (KBW next week); Hassan (excited); Esme (3 tweets: Google AP2+x402, Coinbase AP2+x402 demo, Phala Blackbox TEE+AI); **ISEKOS | Moshi** (long intro: decentralized A2A platform, ISEK, 100% local agents, MCP server, monetization + quality; ERC-8004 for identity + validation + reputation; Story, NFT wallets, x402, blockchain).

**2.1.3 Week of Sept 17–23 (first community call)**

- **Sept 17:** Sumeet (ChaosChain + Google AP2 = "Triple-Verified Stack" — Intent, Process Integrity, Outcome Adjudication; thread); Marco (shared with Google); Tim Williams (production AP2 payments?); Ale Machado @ MetaMask (Szabo social scalability); Joshua (where are trust relationships codified?); cottenio (list of 8004-aligned investors?); **madvinuova** (erc-8004 sim on newOS, code "8004" for waitlist); **Marco** (*"MetaMask just announced its support for x402. We're at the dawn of the era of agents — self-custody, payments (x402), trust (ERC-8004)."* metamask.io news); cottenio, Shawn Cheng (x402 and A2P same week); Sam Polypoll (agent escrow project); Mayur (Zara agents + x402 escrow, explore together).
- **Sept 18:** Sumeet (Genesis Studio: JWT, W3C Payment Request, multi-payment, merchant tokens — github chaoschain-genesis-studio); Tim Williams (protocol wars thoughts); **Marco** (community call Tue, demos — reach out to @jessyioi); Mayur (Google security label, app.vistara.dev); **Davide** (ERC-8004 Team: **Jess** — Coordinator & Ecosystem, **Isha** — Agentic Apps, **Leonard** — Engineering); Isha (first thing for builders); Mayur (submitted); Ceehacks (early?).
- **Sept 19:** Joshua (reply on list?); **Robert Brighton** (Praxis Agent Explorer: on-chain identity ↔ off-chain agent card, .well-known/agent-card.json, signature + agentId verified badge, discovery — demo link); pinky, **Lambert** (karum.ai: global registry, orchestration, trust graph, escrow/settlement; MVP with Virtuals ACP, x402 bazaar, Bittensor); **Nick Sanschagrin | Blockaid** (Sindri Labs: ZK proving, Sindri Encrypted AI, Deck AI); **Jess** (first Trustless Agents Community Call, Sept 23 8am PT, Luma signup, agenda: team, Builder Program, spec updates, demo + Q&A).
- **Sept 20–22:** Trev (hey Lambert); Sumeet (ChaosChain SDK on PyPI — "Triple-Verified Stack" Base Sepolia, AP2 + x402 + verifiable execution + ERC-8004; docs, GitHub, Medium); 0xraph, Akshat (Polygon), pinky, Vdel; **Marco** (spec contributions on Magician, wrapping new possibly final version; *"8004 is already this year's #2 most popular discussion"*); Francesco (Singapore unsocial meetup); Ash Eth, Rickey (ame.network, ERC-8004 integrations); Marco (300 members); Joshua (Q4’s most important group); **Pili** (Cambrian, Buenos Aires, organizing **Agentic Zero** at Devconnect); ISEKOS (missed call — recap?); Pili (call is tomorrow Tue Sept 23); Binji (RT); cottenio (feedback data structure, rating spam / bad actors); cottenio (threat model: sybil attack on reputation — malicious clients pay nominal then lie to harm); Davide (reminder signup CC); Francesco (organize SG).
- **Sept 23 — Community Call day:** Bulletin HT (signed up, eager); **cottenio** (reputation attack simulator + Dispute registry proposal — eip-8004-dispute-proposal-tcotten-scrypted.replit.app); Leonard Tan (call starting, Luma join link); Wyatt Benno (ICME, JOLT/zkML, *"Ethproofs adapted for 8004 Validation Registry. MLproofs!"* blog.icme.io/trustless-agents-with-zkml); Ez (recording?); Davide (will publish on Ethereum YouTube); Joshua (Phala speaker contact); Wyatt (chart % Validation Registry tech? TEE vs crypto vs ZKP); Robert, Bernardo (thanks, recording @jessyioi); Glenn (examples/projects?); cottenio (simulator link); Robert (Praxis X); Mike Anderson (ThinkAgents multiagent in Chromium browser, on-chain agent auth; independentai.institute); Marco (cyberpunk closing); Bulletin HT (slides?); **Med Amine** (bond.credit, credit score layer for agentic economy); Justin Bebis; **Wyatt Benno** (zkML not in diagram — Giza, ICME; use cases: trading prediction, article classification, PII/KYC; ChatGPT inference not yet); Zadok; **Justin SparsityLabs** (Sparsity.ai, trustless agents at scale); Marco (@yozkyo, still early); **Dylan Kawalec** (Phala, dstack/TEE, blog on deployment); Marco (zkML DM to learn); Niels (bond.credit post, Devconnect + Virtuals hackathon); SECRETIVE (memes); madvinuova (SDK route); Justin Bebis (company financing compute for AI?).
- **Sept 23–24:** Jess (slides, recording coming, builder group t.me/ERC8004, builder program bit.ly/8004builderprogram, 8004.org); Vid (call recorded?); Axo (yes, in few days); Calc (router, no accounts, onchain); Bren Cere (decentralized GPU credits); **Marco** (recording + thanks cottenio Easter egg, blockzealous recap); Joshua (transcript?); Mayur (live, build apps 8004); Jess (YouTube recording live); h4x3rotab; Chiali (NEAR project?); Med Amine (aleph.cloud grant); Sumeet (use deployed contracts Base Sepolia, Ethereum Sepolia, Optimism Sepolia; trustless-agents-erc-ri, chaoschain-genesis-studio demo).

**2.1.4 Week of Sept 24–30**

- **Sept 25–26:** James Ross (Mode, trading agents 8004); **Shamir Ozery** (Ensemble.codes w/ leonprou, louthing — Agent Hub Marketplace, Web3 agents); Sumeet (pip install chaoschain-sdk, docs.chaoscha.in); Francesco (who in SG?); Justin SparsityLabs, Justin Bebis, Med Amine (Sunday); h4x3rotab, Ernesto García; **DaoChemist** (Automata AVS, EigenLayer + AI agent verification); h4x3rotab (Automata dcap, lego); **Marco** (400 members); Shadow, Chenzo; Pili (8004 builders Buenos Aires?); Wyatt (zkTLS in EIP?); Leonard (Singapore, chat 8004); Rickey (ChaosChain impl helpful); Premm (Cloudflare code-mode); Sumeet (SDK = 8004 + x402 + AP2 out of box).
- **Sept 27–28:** Med Amine (EigenLayer incoming, intro Automata); DaoChemist (get Automata in group); **Jay Prakash** (DeCompute panel A2A security/privacy + 8004, Sept 30 Singapore — andreolf, lentan, diadrien, EigenLayer, Avail); Justin SparsityLabs (signed up); **Deli Gong | Automata** (thanks DaoChemist); ISEKOS (directory of open-source A2A agents: awesome-a2a-agents); Aniketh (eth online hacking?); **Sofia | EF** (ERC-8004 Knowledge GPT — EIP + Magicians + call transcript as Tier 1, articles Tier 2; link); Marco (Singapore events thread for 8004); Bibi (Linea?); //allen.day (SG? landed); Francesco (just landed); Bruce (link accessible only to you); //allen.day (self.xyz 5pm); Francesco (MetaMask until 8pm); Esme (404 on GPT); **ISEKOS** (ERC-8004 QA Bot GPT Store, reference list EIP, Marco, Google A2A, Coinbase x402, etc.; expand with community projects).
- **Sept 29–30:** Sofia (registered); Joshua (collab?); 大智若愚 (early-stage projects to watch); Marco; ISEKOS (web search on); **Sparkss** (host/register top A2A agents on 8004); Viraj (tweet); **Pili** (Agentic Zero tickets live — agenticzero.xyz, Devconnect Buenos Aires, La Rural); DaoChemist (Bankless x402 + ERC-8004); Francesco (dacc/govtech, agent risk & capability framework); Justin Bebis (super cool).

---

### 2.2 October 2025 (deep)

**2.2.1 Oct 1–6 (pre–v1)**

- **Oct 1:** Aniketh (serious question eth devs); Jess (tweet); Marko, Bench, Hassan, Bruce, Esme (congrats); **Austin Griffith** welcomed (gm from Bruce, Loaf, Swayam); Robert (Praxis P2P trust demo: DID doc, agent card signing, verification, no central server); cottenio (Leonard at Deep Int).
- **Oct 2:** Gary (beginner 8004 tutorial?); Marco (Sumeet, Nader 8004-friends); **Pili** (Agentic Zero speaker applications, panel ERC-8004); Esme (@austingriffith AI BUIDL); Joshua (BuidlGuidl Kevin Jones automation); **Mayur** (Agent Arena demo livestream); **Samuele Marro** (Oxford/Stanford Institute for Decentralized AI, 5 funded visitor slots, deadline Oct 8); cottenio (omg this is me); **denver** (Reputation Registry only via AgentCard? non-agent user feedback — need own AgentCard?).
- **Oct 3:** Francesco (8004 for bond.credit); Nathan (cooking); **Akash | 4Mica** (bond.credit: how credit scores, disputes?); Francesco (bond in next community call); **Sumeet** (trustless agents revolution, autonomous future, verifiability); validator.eth (GoDaddy agent name service); Marco (AltcoinGordon); **Med Amine** (first score with Giza, phase 2, reputation provider design); **Marco** (*"Next community call probably week of Oct 13 or following. Next week will be epic. We will release the new spec (8004 v1) and start rolling out tutorials, SDKs."*); Francesco (tiagovil); Nathan (credit engine design, EigenCloud AVS testnet, automated credit line); Akash (call to discuss); Robert (Praxis: decentralized trading desk of agents); **Mayur** (Agent Arena SDK launch); Tim Williams (GoDaddy won’t do blockchain, DNS+Merkle); Marco (thick skin, state reasons again); Tim (architectural/security gaps); Jess; h4x3rotab (TEE verification demo); **Georgios Piliouras** (Google DeepMind game theory, hiring).
- **Oct 4:** Matt White (name clash — Agent Arena already LMSys/Gorilla agent-arena.com); Mayur (Forge or Actio for SDK; coding agents, bounties, 8004 IDs); DaoChemist (welcome James).
- **Oct 5:** **Dylan Kawalec** (each agent self-verifying smart contract, verifiable runtime, domain; enclave git commit); Johnny (TEE fud response?); **h4x3rotab** (Phala response: phala.com/posts/response-to-wiretap-sgx-deprecation); Johnny (vulnerabilities patched).
- **Oct 6:** cottenio (tweet); Joshua; **Mayur** (Arena SDK, Zara Yield Agent, receipts + trustless settlement); **cottenio** (Scrypted: micro-service + P&L + micro-agent shards; Margin Improvement Notes (MINs); *"ERC-8004 provides the reputation registry for our entire network of micro-agents. Boom. Machine economy."*); Mayur (awesome, DM); Swayam; **Marco** (*"Guys, this is *the* week"*); **Robert** (Praxis 0.2.2: AutoTLS, DID↔Peer, one-click 8004 identity, encrypted KV); **Isha** (8004 Devconnect Builder Program — $157k Thirdweb, L2 grants, Phala/Oasis cloud, Nethermind/Trail of Bits audit, Eliza mentorship, VCs; apply efdn.notion.site); Harpalsinh (Trustless Agents Day link?); Justin Bebis, Christopher (8004 tease); DaoChemist (Graph-of-Thoughts ELI5?); madvinuova (newOS keynote, 8004 for sims); **Sudeep** (awesome repo erc-8004 resources from call + public); Joshua; Justin (multiple reasoning pathways); **Zadok Seven** (AWS Nitro enclaves?); h4x3rotab (@justinzhang Nitro); Zadok (VSOCK proxy, TLS in enclave, POC soon).
- **Oct 6 (evening):** Bibi (inspiring, join next call @marcoderossi); Suzie (Linea, intro Automata?); **king** (learn 8004 via demo, GitHub?); **Mayur** (agent-arena-v1: 8004 + A2A + ChaosChain, receipt on-chain, payment on verification; Sudeep awesome repo — our impl not in it yet); king (thanks); Sudeep (adding Mayur, missed from call).

**2.2.2 Oct 7–9 (v1 launch)**

- **Oct 7:** Marco (👏🤖); **kirsten | recursive.so** (Validation Registry: staking, TEE attestations; IEEE standards background); **Swayam Karle** (single SDK: verifiability, privacy, smart accounts, multi-chain — X); **cottenio** (financial primitive with Mayur, 8004); **Daniel** (AP2, ACP, ATXP, NET, x402 — missing any?); Mayur (demo); cottenio (loan side, bond.credit); Nathan (bond.credit synergies, call); cottenio (tweet 8004); cottenio (testnet impl new registry?); **Justin Bebis** (eliza, agentkit, crossmint, moon); h4x3rotab (contracts?); **Ricky | Cambrian** (subgraph 8004 + ChaosChain contracts, query guide, UI + TEE execution verification); Swayam (no privacy, no 7579 smart accounts).
- **Oct 8:** **ISEKOS | Moshi** (4000+ A2A agents directory, each with ERC-8004 Agent ID); Chenzo; **denver** (*"spec moved draft → review"* https://github.com/ethereum/ERCs/pull/1244); **Marco** (🎮 game among agents, 8004-based, cooperation + fun, game engine help @cakocurek); Chenzo (down to help, DM); Kevin, Christopher, Marco (Nice); P4R; **Sean Brennan** (x402 meetup NYC Oct 21); Bench (time/where); Sean (link); ISEKOS (world first ERC8004-based A2A directory 1000+ agents).
- **Oct 9 — v1 live:** **Marco** (*"🔥🚨 ERC-8004 v1 is LIVE NOW"* — Twitter thread, full spec eips.ethereum.org/EIPS/eip-8004, joint press release, LinkedIn personal); **Sumeet** (v1 reference impl: github.com/ChaosChain/trustless-agents-erc-ri, X post); Bruce (LXDAO "Let's Build Trustless Agents"); **Bruce** (Phase 1 Co-Learning Oct 15–29 intensivecolearn.ing, Phase 2 Casual Hackathon Oct 30–Nov 5 github.com/CasualHackathon/TrustlessAgents, Phase 3 mini-grants ~$500 HappyPods); Bench, Christopher (smoothbrain QT), Mayur, Robert (congrats); Ryan McPeck (ERCs PR 1248 housekeeping).

**2.2.3 Oct 10–25 (post–v1, LXDAO, b402 scam, privacy)**

- **Oct 10+:** LXDAO co-learning and hackathon promotion; **Jay Cool** (Hedera stream, ERC-8004 agent kit, built in stream; anyone else built AI Agent Kit for 8004?); **Ash Eth** (site using Vistara b402?); Mayur (not aware); Ash (current site not b402? like ping x402?); Mayur (frontend not fully updated, b402 in arena CLI github vistara-apps/agent-arena-v1); Ash (Bn402_ai "powered by vistara"); Mayur (checked — **fake**); Ash (lost a little $, drop b402 when ready); Mayur (sorry, will post when ready, contributors welcome).
- **0x Ultravioleta** (bidirectional ERC-8004: github 0xultravioleta/erc-8004-example branch bidirectional, STORY.v2.md).
- **mitchuski | privacymage** (privacy pool for x402 + ERC-8004 identity, e.g. Zk registry ERC-7812); Tim (cool, share when deployed, scenarios?); Loaf (yes def).
- **Vdel | LXDAO** (Phase 1 co-learning daily plan, Casual Hackathon register, TrustlessAgents repo, TG Trustless_Agents_ERC_8004_CH); king (GitHub demo links); Mayur (agent-arena-v1, Sudeep awesome repo); Sudeep (adding Vistara).

---

### 2.3 November 2025 (deep)

**2.3.1 Nov 15–18** — Akash landed BA "normal"; YQ 8004scan v2 Monday; Marco "So fast!"; Nov 17: v2 launched (metadata, feedback, validation, stats); cottenio game theory; Erica BUIDL Europe; Zadok Claude sandbox; Advanced 8004.net public goods; Rich "Incredible day... 8004 community is alive"; Agentic Trust + ENS/DIDs; 0xAthena StarCard→ERC-8004 NFT; Nov 18: indexing/Cloudflare; Marco DePIN Day, TEE.salon, Agents Unleashed; Alias Boost Nov 18–25; Dawid agent0-py.

**2.3.2 Nov 19–22** — DCAP v1.1; Marco first ERC-8004 game; Kantorcodes Hashnet MCP; Pili Agentic Zero panel; Rich 3,687 agents; Loaf lucid-agents; Niels Vitalik surprise; YQ feedback feature; Marco Vitalik M2; Yellowdish Base Sepolia 0x8004AA63...; Nader in.

**2.3.3 Nov 23–30** — Sudeep ERC-8004 in Move/Sui; Khorus BSC; Wyatt Kinic zkTAM; Green Pill 5k ChaosChain SDK; Vitto A2A shared contract; Angelica MaximizeAI 3D. Dec 1: Alias BSC.

---

### 2.4 December 2025 (deep)

**2.4.1 Dec 1–5** — Mayur (Validation Registry for ZK wallet outflow?); Sumeet (within scope, generic request/response); Ben awesome-8004 PR; Vitto USDC sound waves POC; Marco Dawe00 semantic search Agent0; Nicola (agent auth? wallet?); Marco (owner verified, agentWallet optional); h4x3rotab (TEE attested TLS); Peter Qin x402 SF Dec 10; Joe Ran trust graph 8004agents.ai; Ndeto ENSIP-25.

**2.4.2 Dec 6–12** — YQ 8004scan validation live (request/respond); Vitto create-8004-agent tutorial; Marco Solana early next year; Rich Agent Trust Graphs article; Hardik WachAI Mandates; Austin x402 hackathon; Loaf Lucid docs; **Joe Ran 8004 news portal** 8004agents.ai/news; mitchuski podcast; **Kantorcodes Patchwork** Marco ERC-8004; AiMo beta; Jess L2Beat for DeFi agents; Niels bond.credit; **Pili mainnet?** Jess "after New Year"; **Vitto npx create-8004-agent** (Solana Devnet, x402 v2, A2A streaming); MonteCrypto 8004-solana npm; Samuele SafetyBench/AISI.

**2.4.3 Dec 15+** — Sumeet ChaosChain hiring; Bernardo Replicat report.

---

### 2.4 December 2025 (legacy bullets)

- **News & portals:** Joe Ran opened 8004 news portal (8004agents.ai/news); Ash Eth and Rich Pedersen positive. Davide asked for quotes/takes on 8004/x402; Vitto RT’d. Marco engaged on mitchuski’s sovereign/privacy dual agent protocol (podcast/Spotify).
- **Events & talks:** Kantorcodes: Patchwork “Syncing on AI Standards” with Marco on ERC-8004 (Crowdcast). AiMo Network early beta (decentralized AI marketplace, Solana/Base); seeking A2A/MCP partners. Jess: L2Beat for DeFi agents (risk/reward); Niels (bond.credit) aligned. Vivek (x402refunds): next 8004 community call? Robin pointed to Joe Ran; Jess said mainnet/ecosystem after New Year.
- **Mainnet:** Pili asked about mainnet; Robin pointed to Joe Ran; Jess said similarly after New Year when ecosystem returns from holiday.
- **Tooling:** Vitto released **npx create-trustless-agent** (scaffold 8004 + x402 + A2A, all 8004 chains). MonteCrypto: 8004 agent creation tool on Solana + npm 8004-solana; Solana 8004 TG. Rich Pedersen: daily/cumulative trends (AgenticTrust.io). YQ/8004scan: Polygon Amoy support question. Samuele Marro: SafetyBench and AISI security benchmark for agents. Kirill: dashboards for x402/8004 usage; Rich suggested 8004scan.io.
- **Use cases:** Haensen Mcfly (algo trading): technical indicator agent (50 pairs, timeframes, paid indicators, sentiment); S0Crypto suggested x402 for data API; Haensen agreed. Tdub, Rusty AI giveaways/NFT mint (Jess asked to keep non-product posts out).

---

### 2.5 January 2026 (deep)

**2.5.1 Jan 5–9** — **Validation & tiers:** RandomBlock (KyneSys) and Vitto: two levels—(1) receipt/delivery proof (stake-based) vs (2) ZK/TLS for high-sensitivity; Vitto *"wouldn't accept staking as validation for high-sensitivity financial actions."* **Virtuals ACP:** Celeste Ang (evaluation + escrow, ~17k users, ~980k A2A jobs); RandomBlock asked adoption. **Agentokratia:** Panche marketplace x402 + ERC-8004, Base Sepolia, *"high frequency a2a without signing every time."* **Mainnet prep:** Vitto *"Preparing for mainnet"*; Cryptodino mainnet?; Kristjan TypeScript SDK; Xeift agent0lab/agent0-ts. **Marco PROGRESS:** SpecsJan26Update, Sepolia contracts, subgraph, *"Beginning of the 8004 Genesis Month!"*; YQ v1.0 (Identity ERC-721 Native, Reputation crypto auth, Validation URI+Tags); Joe Ran 8004agents.ai; **Vitto joined 8004 team** (Telegram, X, tools); create-8004-agent updated; ecosystem form (Fillout); Mali/Kantorcodes Base Sepolia; Sumeet ChaosChain PR (feedbackIndexes, getValidationStatus); Zeneca newsletter; jenniekusu Agentbeat 8004+x402 submit.

**2.5.2 Jan 10–18** — 8004scan v1 spec live (YQ); Base Sepolia deployed (Vitto, addresses in README); Meerkat Town (Mali) v1.1; Rich 8004scan agent checks docs; John Shutt OyaChat **Commitments** (plain-language onchain, Safe + UMA OG); Kantorcodes $100 Pitch ERC-8004; jenniekusu AMA mainnet; **mainnet Jan 16** (im) then **Vitto delay** *"next week"* (audits/feedback); MonteCrypto 8004 builders space; R402 xprtlai register (agent card NFT, mcp.xprtlai.com); Rich ValidationRegistry not in doc; Premm ERC-7930/8127 (human-readable agent IDs); **Marco** Google UCP Bankless; **Sumeet** ChaosChain multi-dimensional reputation *"Proof of Agency"* (5 dimensions, causal attribution, 8004scan sepolia/450); **MONTREAL AI** AGIJobManager + AGIJobs, deck; JW heurist Ask Heurist ERC-8004; **Scam warnings** Tony, Himu, Kantorcodes (fake angel investors, phishing/malware); Jason 8004tokens.xyz on ecosystem map; MONTREAL AI form.

**2.5.3 Jan 19–31** — Vitto ecosystem map; Jason 8004tokens.xyz missed; MONTREAL AI *"Where is MONTREAL.AI on that map?"*; form; **mainnet** *"tomorrow"* / hope before **ETH Hack Feb 10**; Gilberts repo source of truth (Marco: erc-8004/erc-8004-contracts); Hardik WachAI Verification Protocol whitepaper, Mandates; Rich ontology + mandates; heisenberg 8004 Builder's Jam X Spaces; Kantorcodes HOL x AI; Sabeen plgenesis hackathon 8004 bounties; **Fabri XMTP** agent messaging layer for 8004 (e2ee, MLS); Bobby Digital Ethos Vibeathon finalists, Marco judge; **Mainnet ETA** Vitto *"early next week"* (Jan 22); **Marco** *"ERC-8004 is now frozen"* — value/valueDecimals for feedback, tag1 examples, services rename, best practices Registration + Reputation; **midweek ~Thu 9 AM ET** mainnet; Jason score→value question; keyur ERC-8004 ecosystem Base; Hardik Mandates in ChaosChain SDK; validator.eth ENS blog ERC-8004; Marco Nethermind/Cyfrin/EF audit thanks; Robin burning tokens/Binance neutrality; BJ Pakt agents launch L1s, Avalanche timeline; Mayur private funding 8004 agents.

---

### 2.5 January 2026 (legacy bullets)

- **Validation & tiers:** RandomBlock (KyneSys Labs) and Vitto discussed validation: per-request by default; two levels—(1) receipt/delivery proof (low-cost, stake-based) vs (2) high-cost/compliance (prove what was computed, ZK/TLS). Vitto: wouldn’t accept staking as validation for high-sensitivity financial actions. RandomBlock to share more in coming weeks.
- **Virtuals ACP:** Celeste Ang: Virtuals solves evaluation/escrow via **ACP** (evaluation + escrow); shared architecture overview and SDK docs; ~17k active users, ~980k agent-to-agent jobs; not exclusive to Virtuals agents. RandomBlock asked about adoption; Celeste gave stats.
- **Agentokratia:** Panche: agent marketplace with x402 monetization and ERC-8004 on-chain identity and reviews; high-frequency A2A without constant wallet signing; Base Sepolia, awaiting mainnet to go live on other chains.
- **Mainnet prep & ecosystem:** Vitto: “Preparing for mainnet.” Cryptodino asked if 8004 is mainnet or testnet and where to register; found answer in tweets. Kristjan: which 8004 SDK for TypeScript (viem); Xeift: agent0lab/agent0-ts. Vitto compiled “current state of the ecosystem”; Jason: 8004tokens.xyz missed; MONTREAL AI asked to be on map; form for ecosystem map. Mainnet release date “tomorrow”; hope before ETH Hack (Feb 10). Gilberts: repo source of truth for contract addresses; Marco confirmed erc-8004/erc-8004-contracts.
- **Projects & research:** Agentic Trust ontology & knowledge base (Rich Pedersen); WachAI Verification Protocol whitepaper (Hardik)—mandates, verification protocol for 8004 validation registry; Rich connected mandates to ontology. Eliza Labs (Kenk): shift from responsive to autonomous agents; 8004 & x402 central. Agentbeat (jenniekusu): submit 8004+x402 agents for indexing. BUIDL Europe/Lisbon and HOL x AI (Kantorcodes). Scam warnings (Tony, Himu Globin, Kantorcodes): fake “angel investors,” phishing/malware. heisenberg: 8004 Builder’s Jam X Spaces; jenniekusu: AMA with 8004 builders.
- **Misc:** Marco: MetaMask AI Trading user research (Rizvi booking). Pranay K: validation for coding agents = evaluation problem (test suite in container; consensus via multiple nodes). NFT/8004 (gutslabs, Lowes): bullish on 8004 for NFT utility.

---

### 2.6 February 2026 (deep)

**2.6.1 Feb 1–2** — **Marco** *"Welcome to February - the GENESIS MONTH"*; **ClawLoan** live Base mainnet (Francesco, contributors, 8004 reputation testing); Robin **ElizaTown** OpenClaw + ERC-8004; Vitto OpenClaw+8004 projects to publish; Harpalsinh *"Sign in with Moltbook"* guide; Lowes **clawmaster.ai** open-source UI for claw agents on Moltbook; Hooftly **Position agent** (ERC-6900 modules, ERC-6551 TBA, TBA registers 8004, holds 8004 NFT); YQ 8004 agents aggregated into **clawnews.io**; Shamim which 8004 token (redirect; Jon Stokes *"clawn.ch if you want to gamble"*); Onno VeriPura hiring; Haythem 8004scan other chains; YQ *"better for 8004 team to handle"*; **Vitto** *"talking to Monad to get this deployed asap next week"*; **GhØsT_PilØT_MD** (AGI Alpha/AGIJobs) identity→replayable proof→adversarial validation→escrowed settlement; AGIJobManager, AGIJobsv0; Mesut Moltbook identity-token/MOLTBOOK_APP_KEY; ensgiant IPFS URI not reflecting 8004scan; **Sumeet** ChaosChain skill for OpenClaw (*clawhub install chaoschain*); Hardik WachAI Mandates Clawhub skill; YQ sponsor 100 agents clawnews/register; **Marco** *"first 3 days of Mainnet beyond our wildest expectations, over 30 agents"*; vanity mints *"very Web3-coded"*; collabs L2s *"almost every day"*; **Polygon** 8004 live (Vitto); Harpalsinh Monad hackathon; clawon8004 (bc0x gavin); Agentscan Transaction Analytics 22,813 agents.

**2.6.2 Feb 3–9** — EF AI security guide OpenClaw (Vitto); Marco tweet; Ioannis register agents guidance; Mesut create-8004-agent; bc0x gavin clawon8004 OpenClaw→8004; Pranay Base mainnet?; Will Agentscan analytics; **Monad hackathon** (Harpalsinh) OpenClaw; Konrad clawork.world; Vitto *"on it"* Base; **Polygon mainnet + Amoy** official (Vitto); Marco Polygon subgraph Agent0, SDK next; Hardik Mandates primitives read; Alexis own Identity/Reputation contracts 8004-compatible; Franklin 8004market.io Polygon; Carlos clawdvine x402+8004; Justin Bebis Moltbook article; GhØsT_PilØT_MD AGI Alpha list; Kaloh agent got 8004, posted Clanker; Anna 8004scan star bug; Robin Agent Town openclaw+8004; Joe Ran 8004agents.ai Polygon; Hardik WachClaw Moltbook, WachAI demo; Stephanie Advaita multi-agent consensus paper; MonteCrypto 8004-mcp v0.2.3 one-shot Eth mainnet; Jiawei builder-agent Clawd. **ETHCC 2026** Cannes side-events recruitment (speakers, sponsors) in Feb 9 chat.

---

### 2.6 February 2026 (legacy bullets)

- **Genesis month & mainnet:** Marco: “Welcome to February - the GENESIS MONTH.” Vitto: OpenClaw projects with 8004 to be published. Francesco: ClawLoan live on Base mainnet; wants contributors and more 8004 reputation testing. Robin: ElizaTown (OpenClaw + ERC-8004). YQ: 8004 agents aggregated into clawnews.io. Monad: Vitto “talking to Monad to get this deployed asap next week”; Haythem asked about 8004scan and other chains; YQ said better for 8004 team to handle for consistency.
- **OpenClaw / Moltbook:** Lowes: open-source UI clawmaster.ai for managing claw agents on agent-only social (Moltbook). Robin: only Matt can integrate 8004 into Moltbook (Lowes thought that sounded centralized). Harpalsinh: “Sign in with Moltbook” guide. Hooftly: Moltbook “exposes everyone’s secret API keys” / “MD files and cron jobs”; Cryptographic: still interesting experiment; scale of coordination; 8004/x402 will unlock useful use cases. Tim 🔮: OpenServ agent SDK, registers on OpenServ, x402 link for monetization, can register on 8004; “gpt 5” on backend.
- **Position agents & DeFi:** Hooftly: integrating OpenClaw as Position agent; ERC-6900 modules; user mints position NFT, activates position agent mode → ERC-6551 TBA, registers with ERC-8004, TBA holds 8004 NFT; transfer PNFT and identity follows; asked for feedback (EqualFi repo + PDF).
- **Enforcement & validation:** GhØsT_PilØT_MD (AGI Alpha / AGIJobs): identity → bounded execution → replayable proof → adversarial validation → escrowed settlement; payment tied to replayable proof; pointed to AGIJobManager and AGIJobs protocol repos. Mesut: Moltbook identity-token and verification (MOLTBOOK_APP_KEY) issues. ensgiant: IPFS URI update not reflecting on 8004scan (agent ethereum/22605).
- **Community & housekeeping:** Shamim asked which 8004 token/NFT to buy; group redirected (wrong group / learn first). Jon Stokes: “clawn.ch if you want to gamble.” Onno (VeriPura): intro, hiring Senior Blockchain QA. Kantorcodes: anyone with working A2A endpoint to feature. Sumeet: “8004 reputation will soon become a high value asset.” John Shutt: asking for Sepolia USDC for UMA testnet bond (400 USDC). Robin clarified burning tokens / neutrality (Binance Angel, ethereum.org mod). BJ (Pakt): agents launching/managing L1s; Avalanche timeline. Mayur: private funding for 8004 agents.

---

## 3. Background & research context (web)

*External context for terms, projects, and events referenced in the chat. Links are to official or canonical sources where available. **Multi-session web research:** see `docs/ERC8004_RESEARCH_ROADMAP.md`; Batches 1–8 complete (§3.19–3.29).*

### 3.1 ERC-8004 standard

**ERC-8004** is an Ethereum Improvement Proposal for *Trustless Agents*: discovery, identification, and trust among autonomous agents across organizational boundaries without pre-existing relationships. **Three registries** (per-chain):

| Registry | Status | Purpose |
|----------|--------|---------|
| **Identity** | Stable | ERC-721; portable agent IDs; tokenURI → JSON (profile, services, metadata). |
| **Reputation** | Stable | Post/fetch feedback (0–100, tags); on-chain + off-chain. |
| **Validation** | Unstable (v1.1-preview) | Request/record validator attestations (stake, zkML, TEE); format in flux. |

- **EIP:** [eips.ethereum.org/EIPS/eip-8004](https://eips.ethereum.org/EIPS/eip-8004)  
- **Best practices:** [best-practices.8004scan.io](https://best-practices.8004scan.io/docs/01-agent-metadata-standard.html) (metadata); [Validation Data Profile](https://best-practices.8004scan.io/docs/03-validation-standard.html) (pending).  
- **Deployments:** Ethereum, Base, Polygon, Arbitrum, Celo, Gnosis, Scroll; testnets Sepolia, Base Sepolia, Polygon Amoy, Arbitrum Sepolia. Co-authors/backing: MetaMask, Ethereum Foundation, Google, Coinbase.

### 3.2 x402 (agent payments)

**x402** uses **HTTP 402 Payment Required** for micropayments: server returns 402 + payment details; client pays on-chain (e.g. USDC on Base/Solana) and retries with proof. No accounts or API keys. **Cloudflare** and **Coinbase** launched the **x402 Foundation** to standardize AI-driven machine-to-machine payments; billions of 402 responses go unanswered daily due to lack of standardization. **Google** supports x402 in agentic commerce (Python A2A x402 extension). Flow: agent requests restricted content → server returns payment instructions → agent pays → facilitator settles → server delivers. Cloudflare offers deferred batch settlement and x402 in Agents SDK / MCP.  
- [x402.org](https://www.x402.org/) · [x402 GitBook](https://x402.gitbook.io/x402) · [Cloudflare x402](https://developers.cloudflare.com/agents/x402/) · [Google a2a-x402](https://github.com/google-agentic-commerce/a2a-x402)

### 3.3 Virtuals & ACP

**Virtuals** (Base): create, own, monetize AI agents; **Agent Commerce Protocol (ACP)** for agent-to-agent commerce. Four phases: Request → Negotiation (Proof of Agreement) → **Transaction (escrow)** → **Evaluation**. Optional evaluation for reputation.  
- [virtuals.io](https://www.virtuals.io/) · [ACP whitepaper](https://whitepaper.virtuals.io/about-virtuals/agent-commerce-protocol)

### 3.4 Devconnect 2025

**Devconnect 2025** (“Ethereum World’s Fair”): **November 17–22, 2025**, Buenos Aires (La Rural, Palermo). 14k+ attendees, 130+ countries, 80+ exhibitors, 500+ side events.  
- [devconnect.org](https://devconnect.org/)

### 3.5 OpenClaw / Moltbook

**OpenClaw** evolved from Clawdbot/Moltbot; open-source AI agent platform with CLI (agents, config, messaging, etc.). **Moltbook** is an agent-only social surface; “Sign in with Moltbook” and 8004 integration discussed in chat.  
- [docs.molt.bot](https://docs.molt.bot/cli/agents) · [CNBC Feb 2026](https://cnbc.com/2026/02/02/openclaw-open-source-ai-agent-rise-controversy-clawdbot-moltbot-moltbook.html)

### 3.6 8004scan.io & Agentscan

- **8004scan.io:** Explorer (agents by chain, services, endpoint test for health).  
- **Agentscan.info** (Alias Labs): Explorer + leaderboard with data-driven scoring.  
- [8004scan.io](https://8004scan.io/agents) · [agentscan.info](http://agentscan.info/)

### 3.7 ChaosChain (Nethermind)

Experimental L2 with **AI agents as validators** (personalities, discussion, voting). Reference implementation of ERC-8004: [ChaosChain/trustless-agents-erc-ri](https://github.com/ChaosChain/trustless-agents-erc-ri).  
- [ChaosChain GitHub](https://github.com/ChaosChain)

### 3.8 ETHCC 2026

**March 30 – April 2, 2026**, **Cannes, France**. Side-events recruitment (speakers, sponsors, hackathon organizers, etc.) mentioned in Feb 9 chat.  
- [ETHCC 2026](https://events.coinpedia.org/ethereum-community-conference-2026-7885/)

### 3.9 Other references (from chat)

- **Agent0 SDK:** sdk.ag0.xyz; Cooking Call for roadmap and features.  
- **TEE attestation:** IETF RATS; 8004 Validation Registry will define how attestations map to the registry.  
- **Contract addresses:** [github.com/erc-8004/erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts) as source of truth (Marco, Jan 2026).

### 3.10 Phala Network (TEE + ERC-8004)

**Phala Network** combines TEE with Confidential VMs to run ERC-8004–compliant agents with verifiable execution: deterministic key material, remote attestation, onchain discovery. **Phala Cloud** offers VibeVM templates for one-click TEE deployment, Sepolia registry workflow, optional GPU TEE inference. Repo: [Phala-Network/erc-8004-tee-agent](https://github.com/Phala-Network/erc-8004-tee-agent). Addresses the gap where agents only prove key possession (signatures) not execution context or provenance.  
- [docs.phala.com](https://docs.phala.com/phala-cloud/getting-started/explore-templates/deploy-erc-8004-agent) · [phala.com/learn](https://phala.com/learn/How-TEE-Verification-Works)

### 3.11 bond.credit

**bond.credit** builds the "credit layer for the agentic economy." **Agentic Alpha** deploys real capital to onchain agents, records every trade and vault update onchain to create a credit engine for low-risk DeFi and programmable credit. Agents that outperform earn credibility, higher credit limits, and capital routing. Ties into on-chain credit scores and undercollateralized lending.  
- [bond.credit](https://bond.credit/)

### 3.12 Agentic Zero

**Agentic Zero** was a one-day AI and Web3 summit on **November 20, 2025**, at La Rural, Buenos Aires, during Devconnect. Focus: open, permissionless agentic systems; decentralized crypto infra for AI; autonomous systems on Web3; ethical and verifiable AI. Organized by a16z crypto; speakers included Aztec, Eigen Labs, Uniswap Foundation, Allora, Cambrian, Giza. Backed by Allora, Giza, Recall, Zyfai, AdEx.  
- [agenticzero.xyz](https://agenticzero.xyz/) · [Devconnect Agents Day](https://yellow.com/news/devconnect-agents-day-draws-450-in-buenos-aires-to-explore-agentic-ai-future)

### 3.13 LXDAO

**LXDAO** is an R&D-driven DAO ("LX" = conscience / 良心) sustaining open-source and Web3 public goods. Operates with 16k+ Twitter/Telegram, $220k+ treasury, Snapshot governance. Supports projects like GCLX, MyFirstNFT, Donate3. Associated with **8004.org** (Trustless Agents) and ERC-8004 co-learning / hackathon (Oct 2025).  
- [lxdao.io](https://lxdao.io/) · [8004.org](https://8004.org/)

### 3.14 UMA Optimistic Governor

**UMA Optimistic Governor** integrates UMA's Optimistic Oracle with **Gnosis Safe**: proposals (with explanation) are approved after a liveness period unless disputed; proposers post bond. Used by **OyaChat (John Shutt)** for **Commitments**—plain-language onchain rules (e.g. "Any agent may return deposits plus 10% fee") attached to a Safe; UMA oracle verifies and executes. Enables agent allowlists and 8004 reputation in commitment flows.  
- [contracts.docs.umaproject.org](https://contracts.docs.umaproject.org/contracts/zodiac/OptimisticGovernor) · [docs.uma.xyz](https://docs.umaproject.org/)

### 3.15 Oasis & Talos

**Talos** is an AI-managed autonomous treasury protocol on **Arbitrum** (Arbitrum Foundation / Offchain Labs Onchain Labs). Combines TEE-based inference, off-chain training (RLHF, time-series), and community governance. Monitors onchain data and sentiment to optimize yield across ERC-4626 vaults; can rebalance lending, liquidity, derivatives. **Oasis** (Marko) contributes Talos TEE stack; **TIP-0005** and DEPLOYMENT.md referenced in chat.  
- [blog.arbitrum.io (Talos)](https://blog.arbitrum.io/how-talos-is-using-arbitrum-to-build-the-first-fully-autonomous-treasury/) · [oasis.net (Talos)](https://oasis.net/blog/talos-rofl-onchain-intelligence)

### 3.16 WachAI & Mandates

**WachAI** builds a **Verification Protocol** on ERC-8004 and x402 for verifiable agent-to-agent commerce. **Mandates** are deterministic agreement objects between client and server agents (signed, executable). Primitives are typed task bodies. Goal: "exchange an intent, turn it into a signed agreement, execute a task, and later prove what happened." Integrates with **OpenClaw** (WachClaw skill on Moltbook). TypeScript and Python SDKs.  
- [wach.ai](https://wach.ai/) · [docs.wach.ai](https://docs.wach.ai/SDKs/typescript/mandates-core)

### 3.17 Veramo (DID / agent identity)

**Veramo** is a JavaScript/TypeScript framework for DIDs and verifiable credentials; used by **Agentic Trust (Rich Pedersen)** with 8004 and ENS. **Veramo Agent** handles identifiers, credential issuance/revocation/exchange, secret management. Supports **did:ethr** (Ethereum address as identity via ethr-did-registry). Plugin-based; runs on Node, browser, React Native.  
- [veramo.io](https://veramo.io/) · [Veramo Agent](https://veramo.io/docs/veramo_agent/introduction)

### 3.18 Research roadmap (multi-session)

A **web research roadmap** lists every mentioned project, standard, and event for systematic coverage. **Batches 1–8 complete** (§3.10–3.29).  
- **Roadmap:** `docs/ERC8004_RESEARCH_ROADMAP.md`

### 3.19 Identity, payments & infra (Batch 2)

- **ENS:** Subnames give agents human-readable, verifiable identities (e.g. agent123.ai.eth). ENS blog: identity for agentic commerce; portable, open, composable, human-readable. Namespace.ninja offers subname issuance for agents. [ens.domains/blog (ENS AI agent ERC8004)](https://ens.domains/blog/post/ens-ai-agent-erc8004)
- **ERC-5564:** Stealth addresses; non-interactive, one-time recipient addresses; scan keys (detect incoming) + spend keys (claim). Singleton at 0x5564...; works with ERC-6538 (Stealth Meta-Address Registry). Used by Unwallet for private agent revenue. [eips.ethereum.org/EIPS/eip-5564](https://eips.ethereum.org/EIPS/eip-5564)
- **ERC-6551:** Token-bound accounts; each NFT gets a wallet (ERC-1167 clone); can own assets, sign, interact. Used by Hooftly Position agents (PNFT → TBA → 8004). [tokenbound.org](https://tokenbound.org/) · [eips.ethereum.org/EIPS/eip-6551](https://eips.ethereum.org/EIPS/eip-6551)
- **ERC-6900:** Modular smart contract accounts; pluggable validation/permission modules (session keys, spending limits, multisig). ERC-4337 compatible. [erc6900.io](https://erc6900.io/) · [eips.ethereum.org/EIPS/eip-6900](https://eips.ethereum.org/EIPS/eip-6900)
- **ERC-7930:** Binary interoperable address format for cross-chain; compact, machine-optimized. ERC-8127 (Premm): human-readable alias + opaque registry location for agent IDs. [ethereum-magicians.org (ERC-7930)](https://ethereum-magicians.org/t/erc-7930-interoperable-addresses/23365)
- **Google AP2:** Agent Payments Protocol (Google + Coinbase Sept 2025): A2A messaging + x402 settlement. Agents negotiate and pay without human intervention; Lowe's demo (end-to-end shopping). [Coinbase AP2](https://www.coinbase.com/developer-platform/discover/launches/google_x402) · [github.com/google-agentic-commerce/AP2](https://github.com/google-agentic-commerce/AP2)
- **IETF RATS:** Remote ATtestation procedureS (RFC 9334); Attester → Verifier → Relying Party. Framework for TEE/attestation evidence; 8004 Validation Registry can map attestations. [datatracker.ietf.org/wg/rats](https://datatracker.ietf.org/wg/rats/about/)
- **MetaMask Delegation:** Part of Smart Accounts Kit (ERC-7710); delegator grants delegate permission to execute on behalf; caveats for limits. Used by Rich Pedersen Agent Identity Explorer (no user wallet; Web3Auth, Delegation, AA). [docs.metamask.io/delegation-toolkit](https://docs.metamask.io/delegation-toolkit/concepts/delegation/)

### 3.20 Builders & products (Batch 3)

- **Agentic Trust (agentictrust.com):** Secure infra for building/deploying AI agents; SSO, LLM routing, observability; 50+ integrations. ERC-8004 + Veramo + ENS in chat (Rich Pedersen).  
- **Alias Labs / Agentscan:** agentscan.info is ERC-8004 AI Agent Explorer; leaderboard, transaction analytics (22k+ agents in chat). StarCard → ERC-8004 compliant Agent NFT (Sepolia).  
- **Agent0 / create-8004-agent:** `npx create-8004-agent` scaffolds registration.json, agent.ts, register.ts, A2A/MCP, .well-known/agent-card.json; wizard for chain (EVM/Solana), x402, trust model. agent0lab repos: subgraph, agent0-ts.  
- **ChaosChain (deepen):** Nethermind-led; (1) experimental L2 with AI validators (“chaotic consensus”); (2) accountability protocol: Proof of Agency (PoA), 5-dim reputation, DKG, ERC-8004. Genesis Studio: wallets, on-chain IDs, USDC, Story Protocol. [docs.chaoscha.in](https://docs.chaoscha.in/)  
- **Virtuals ACP (deepen):** Four phases—Request, Negotiation (PoA), Transaction (escrow), Evaluation. Evaluator agents assess completion; SDKs Python/Node. ~17k users, ~980k A2A jobs (Celeste in chat). [whitepaper.virtuals.io (ACP)](https://whitepaper.virtuals.io/about-virtuals/agent-commerce-protocol)  
- **Agentokratia:** Agent marketplace with x402 + ERC-8004; on-chain identity and reviews; high-frequency A2A without constant signing. Base Sepolia (Panche).  
- **ClawCredit / ClawLoan:** ClawCredit (t54 Labs) is autonomous credit for AI agents (computing, x402, goods); Solana live, Base “coming soon.” Chat referenced ClawLoan (Francesco) on Base mainnet for 8004 reputation testing—may be related or clawloan.com. [claw.credit](https://claw.credit/)  
- **DayDreams:** router.daydreams.systems — unified API for multiple AI models; x402 or API key auth; Lucid Agents SDK (x402 + A2A + 8004). [docs.daydreams.systems](https://docs.daydreams.systems/) · [github.com/daydreamsai/lucid-agents](https://github.com/daydreamsai/lucid-agents)

### 3.21 Validation & attestation (Batch 4)

- **DCAP / Automata:** Automata + Cantina implement verifiable AI agents for ERC-8004 using DCAP (Intel Data Center Attestation Primacy). TEE-attested agents; open-source DCAP quote verification, on-chain PCCS. [blog.ata.network (ERC-8004)](https://blog.ata.network/how-automata-and-cantina-enable-verifiable-ai-agents-for-erc-8004-c8722617f772)  
- **Silence Laboratories:** MPC and privacy-preserving tech; Silent Shard (TSS), Silent Compute (compute on encrypted data), Multimodal Proofs. Jay Prakash (chat): private/verifiable A2A, 8004 backbone, DeCompute Singapore. [silencelaboratories.com](https://www.silencelaboratories.com/)

### 3.22 Protocols (Batch 6)

- **MCP (Model Context Protocol):** Open standard connecting AI apps to external systems (tools, resources, workflows); JSON-RPC 2.0. 8004 adds discovery and trust across org boundaries; MCP advertises capabilities, 8004 registers identity/reputation/validation. [modelcontextprotocol.io](https://modelcontextprotocol.io/)  
- **A2A (Agent-to-Agent):** Google-led; discovery, negotiation, tasks, secure exchange. HTTP, JSON-RPC 2.0, SSE. Agent Cards describe capabilities. Linux Foundation–associated; 21k+ GitHub stars. Complementary to MCP (agent-to-agent vs agent-to-tools). [google.github.io/A2A](https://google.github.io/A2A/specification/) · [github.com/google/A2A](https://github.com/google/A2A)

### 3.23 Events (Batch 5)

- **BUIDL Europe 2026:** Jan 7–8, Lisbon (Red Cross Portugal); Web3 conference (KryptoPlanet). **BUIDL AI Hackathon 2026:** Jan 9–11, Lisbon (The Nest); Erica Kang, June Kim, Hackbox Co; AI agents and real-world use cases; hybrid, Devpost. [buidleurope.com](https://www.buidleurope.com/) · [Luma BUIDL AI](https://luma.com/yxrbeoyd)

### 3.24 Validation, zkML & security (Batch 4 rest)

- **zkML / JOLT / ICME:** **JOLT** (a16z research) enables fast ZK proofs; **ICME** built zkML-JOLT (Atlas) for neural-network inference (3–7× faster). blog.icme.io: trustless agents with zkML; validation models = reputation, crypto-economic (stake + re-execute), or TEE. Wyatt Benno (chat): Ethproofs adapted for 8004 Validation Registry; “MLproofs!” [blog.icme.io (zkML)](https://blog.icme.io/trustless-agents-with-zkml/)
- **Nethermind:** Major Ethereum execution client; **Nethermind Security** does smart-contract audits (public reports on GitHub). Marco thanked Nethermind (with Cyfrin and EF security) for free auditing of 8004 contracts pre-mainnet. ChaosChain is a Nethermind-led experiment. [nethermind.io/audits](https://www.nethermind.io/smart-contract-audits)
- **Cyfrin:** Smart-contract security audits, Aderyn (static analysis), CodeHawks, Solodit; Ethereum and multi-chain. Marco thanked Cyfrin for free 8004 contract audits. [cyfrin.io](https://www.cyfrin.io/)
- **SafetyBench / Agent-SafetyBench:** **SafeBench** (ML Safety): robustness, monitoring, alignment benchmarks. **Agent-SafetyBench** (OpenReview): 349 environments, 2k test cases, 8 safety risk categories; 16 LLM agents under 60% safety. **Agent Security Bench (ASB)** (ICLR 2025): attacks/defenses for LLM agents. Samuele Marro (chat) referenced SafetyBench and AISI for agent security. [mlsafety.org/safebench](https://www.mlsafety.org/safebench) · [OpenReview Agent-SafetyBench](https://openreview.net/forum?id=yYFNnX1RM3)
- **Praxis / agent-card:** **Robert Brighton** (chat): Praxis Agent Explorer — on-chain identity ↔ off-chain agent card, `.well-known/agent-card.json`, signature + agentId verified. A2A Agent Card (e.g. x4ai.org/agent-card): identity, capabilities, endpoints (A2A, MCP), monetization. [x4ai.org/agent-card](https://x4ai.org/agent-card)

### 3.25 Events & programs (Batch 5 rest)

- **Patchwork:** Onchain data protocol; ERC-721–based “Fragments” bound to tokens/contracts. **Kantorcodes** (chat): Patchwork “Syncing on AI Standards” with Marco on ERC-8004 (Crowdcast). [patchwork.dev](https://patchwork.dev/)
- **HOL x AI (Hashgraph Online):** Hedera x AI events; YC-style pitch competition (e.g. May 2025, $30k pool). Chat: HOL x AI $100 Pitch “Best ERC-8004 Agent,” 12PM ET; Kantorcodes invited 8004 builders. [hashgraphonline.com/hederaai](https://hashgraphonline.com/hederaai)
- **Ethos Network / Vibeathon:** Ethos = onchain reputation (review, vouch, slash). **Bobby Digital** (chat): Ethos Vibeathon, Base, Claude + $75 credits, $40k prize pool; Marco as finalist judge; “reputation-powered products on Ethos.” [ethos.network](https://ethos.network/)
- **Moltiverse hackathon:** **Monad** + OpenClaw/agent ecosystem. Chat: Harpalsinh hosting hackathon for OpenClaw builders; Moltiverse in New Delhi Feb 12, 2026 (per Monad search). Monad mainnet live; 8004 deployment discussed (Vitto “talking to Monad next week”).
- **ETHCC 2026:** **March 30 – April 2, 2026**, Cannes, France (Palais des Festivals). Europe’s largest Ethereum conference; 400+ speakers, EthVC track, side-events. Chat: side-events recruitment (speakers, sponsors) Feb 9. [events.coinpedia.org (ETHCC 2026)](https://events.coinpedia.org/ethereum-community-conference-2026-7885/)
- **8004 Builder Program:** Chat: Jess coordinator, Isha (Agentic Apps), Leonard (Engineering); bit.ly/8004builderprogram; builder group t.me/ERC8004. Structured program for teams building on ERC-8004.

### 3.26 Protocols & data (Batch 6 rest)

- **W3C Payment Request:** Standard browser API for payments. ChaosChain Genesis Studio used W3C Payment Request in agent payment flow (chat).
- **Story Protocol:** EVM L1 for IP on-chain; Proof-of-Creativity, IP Royalty Vault, derivative licensing. ChaosChain Genesis Studio integrated Story Protocol royalties (chat). [docs.story.foundation](https://docs.story.foundation/concepts/royalty-module/overview)
- **Irys:** Programmable data chain; data with logic, IrysVM (EVM-compatible). **EAS (Ethereum Attestation Service):** Permissionless attestations (identity, credentials, reputation); 8.7M+ attestations. Mayur (chat) referenced Irys + EAS for attestation/stake-secured validation. [irys.xyz](https://irys.xyz/core-features) · [attest.org](https://attest.org/)
- **Privacy pools / Unwallet:** **Privacy Pools** (e.g. 0xbow): compliant anonymous transactions with blocking lists. **Unwallet:** x402 + stealth addresses (ERC-5564–style); one-time addresses per payment, scan/spend keys; private revenue for agents. mitchuski (chat): sovereign/privacy dual agent protocol. [docs.unwallet.io](https://docs.unwallet.io/) · [ethereum.org/apps/privacy-pools](https://ethereum.org/apps/privacy-pools/)

### 3.27 More projects & chains (Batch 7–8)

- **XMTP:** E2EE messaging (MLS protocol); **agent SDK** (`@xmtp/agent-sdk`) for agents in secure conversations. **Fabri** (chat): agent-to-user and multi-agent messaging for 8004; self-custodial agents in TEEs avoid centralized messaging. [docs.xmtp.org/agents](https://docs.xmtp.org/agents/get-started/build-an-agent)
- **MONTREAL AI / AGI Alpha / AGIJobs:** **AGIJobManager** (minimal execution/settlement on Ethereum), **AGIJobsv0** (escrow, validation, settlement). **AGI Alpha** (Vincent Boucher): meta-agentic jobs marketplace (Solana); decentralized job routing, $AGIALPHA. **GhØsT_PilØT_MD** (chat): identity → replayable proof → adversarial validation → escrowed settlement. [github.com/MontrealAI/AGIJobManager](https://github.com/MontrealAI/AGIJobManager) · [montrealai.github.io/agijobsv0](https://montrealai.github.io/agijobsv0.html)
- **Pinata:** IPFS pinning and API for NFTs and apps; dedicated gateways, x402 monetization. **Matt** (chat): IPFS for agent state, interest from AI agents. [docs.pinata.cloud](https://docs.pinata.cloud/)
- **Monad:** High-performance EVM (parallel execution, ~10k TPS, sub-second finality). Mainnet live; 8004 deployment in progress (Vitto chat). Moltiverse hackathon Feb 12, 2026 New Delhi. [monad.xyz](https://monad.xyz/) · [docs.monad.xyz](https://docs.monad.xyz/monad-arch/execution/parallel-execution)

### 3.28 Additional builders & misc (Batch 7–8 rest)

- **Vistara / Mayur (Z | Vistara):** From chat: app.vistara.dev, Zara AI Factory, Fire Alarm + Ship-2-Earn demo, ~2k apps, earnings loop; decentralized task protocol with 8004 + x402; Bankless mention (ZyfAI, DayDreams, Vistara).
- **Khorus:** Platform to deploy on-chain A2A agents; ERC-8004 identity, x402 payments, 1,000+ agent APIs; “Agent Offices,” tokenization/marketplace. Live on BNB Chain; public beta Nov 2024, $10M Series A. Chat: Mehmet, docs.khorus.io. [khorus.io](https://www.khorus.io/)
- **ZyfAI:** Early ERC-8004 adopter; cross-chain yield optimization agent (~$10.5M deposits); ERC-4337 Smart Account (Safe), session keys, auto rebalance. Gauthier/Neutize in chat; ZyfAI skill for OpenClaw, X Spaces. [docs.zyf.ai](https://docs.zyf.ai/)
- **clawon8004:** From chat (bc0x gavin): OpenClaw-native skill; agent registers as ERC-8004 Agent Card, links AGENTS, IDENTITY, SOUL, MEMORY; first live example on agentscan.info. `clawhub install`-style.
- **8004market.io:** From chat (Franklin): marketplace for 8004 agents; “live on our marketplace,” chain=polygon; trading coming soon.
- **EqualFi / Position agents:** From chat (Hooftly): Position NFT → ERC-6551 TBA → TBA registers 8004, holds 8004 NFT; ERC-6900 modules; EqualFiLabs repo, Position_Agents_Sovereign_Finance.pdf.
- **SparsityLabs (Sparsity.ai):** a16z-backed, MIT-founded; trustless agents, verifiable computing (ZK, TEE, MPC, FHE). Core contributor to ERC-8004 TEE stack; workshops (Luma) for building 8004 trustless agents; agents.sparsity.ai demo. Justin (SparsityLabs) in chat: trustless agents at scale. [Luma Sparsity Workshop](https://luma.com/6sz82hm7)
- **Recursive.so:** Recursive Studios (Kirsten Pomales, Pranav); crypto-native products, TalentLayer. Chat: recursive.so / kirsten in validation context. [recursive.so](https://www.recursive.so/)
- **Sindri Labs:** ZK proving platform; simplifies ZK proof generation. Nick Sanschagrin (chat) mentioned Blockaid + Sindri; DeCompute panel A2A security/privacy + 8004 (Sept 30 Singapore). [sindri.app](https://sindri.app/)
- **Blockaid:** Security platform (fraud/scam prevention). Nick Sanschagrin | Blockaid in chat.
- **ETHDenver 2026:** Feb 17–21, 2026 (National Western Center); #BUIDLathon, BUIDLWeek from Feb 15. Lucas (chat): who’s visiting EthDenver. [ethdenver.com](https://ethdenver.com/home/)

### 3.29 Final batch (EigenLayer, UCP, Luma, Zeneca, chains)

- **EigenLayer & Automata:** **EigenLayer** enables restaking of ETH to secure AVS (Actively Validated Services). **Automata Network** runs a Multi-Prover AVS on EigenLayer using TEE + DCAP attestation; DCAP v1.0 for rollups and AI agents (adopted by Scroll, Taiko, Flashbots, Espresso). DaoChemist (chat): Automata AVS, EigenLayer, got Deli Gong | Automata in group; dcap for 8004 validation. [blog.ata.network (AVS)](https://blog.ata.network/automata-building-multi-prover-avs-on-eigenlayer-489df5d45a42) · [blog.ata.network (DCAP)](https://blog.ata.network/automatas-dcap-attestation-v1-0-0-building-for-rollups-and-ai-agents-2508221be0b8)
- **Bankless & UCP:** **Bankless** ran “How Google’s UCP Fits Into the Agent Economy” (Marco shared in chat). **UCP** (Universal Commerce Protocol) is Google’s standard for AI agent commerce via Gemini; **AP2** (Agent Payments Protocol, Google + Coinbase) is the trust layer (VDCs, signed checkout). [bankless.com/read/googles-ucp-ai-agent-economy](http://www.bankless.com/read/googles-ucp-ai-agent-economy) · [agentpaymentsprotocol.info](https://agentpaymentsprotocol.info/)
- **Luma:** Luma hosts 8004 and x402 community events: 8004 Community Call #3, x402 Happy Hour (SF), Cloudflare x402 Meetup, “Trustless agents on Ethereum” meetups. David Minarsch (chat): Luma event with x402 and 8004; Francesco “builder night on 8004.” [luma.com (8004 Call)](https://luma.com/2kvxberc)
- **Zeneca:** “Letters from a Zeneca” (zeneca.xyz) — NFT/crypto newsletter. Vitto (chat): “Zeneca newsletter talks about 8004 this week.”
- **MegaETH:** High-performance L2; mainnet Feb 9, 2026; targets 100k+ TPS, sub-ms latency; $450M raise, Vitalik backing. Chat: ecosystem/chains list included MegaETH. [coindesk.com (MegaETH)](https://www.coindesk.com/tech/2026/02/09/megaeth-debuts-mainnet-as-ethereum-scaling-debate-heats-up)
- **Chains (8004):** Per summary/doc: **Ethereum** mainnet live Jan 2026; **Base**, **Polygon** (mainnet + Amoy), **Monad** in progress; **Optimism**, **Scroll**, **Celo**, **Gnosis**, **Arbitrum** with testnets (Sepolia, Base Sepolia, Polygon Amoy, Arbitrum Sepolia). Contract addresses: [github.com/erc-8004/erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts).

---

## 4. Raw transcript

The full transcript is in **plain text** at:

**`C:\Users\natha\sol-cannabis\ChatExport_2026-02-09\transcript.txt`**

- **Format:** Date dividers as `--- DD Month YYYY ---`; each message as `From Name, [DD.MM.YYYY HH:MM:SS TZ]` followed by the message body.  
- **Count:** ~3,490 entries (user messages + date markers) extracted from messages.html through messages6.html.  
- **Chronology:** Oldest (Sept 2025) at the top; newest (Feb 2026) at the bottom.

To regenerate the transcript from the HTML export:

```bash
cd ChatExport_2026-02-09
python extract_chat.py
```

---

## 5. Themes (cross-cutting)

1. **Three registries:** Identity and Reputation stable; Validation still in progress (TEE/attestation, missing-record semantics, failure handling).  
2. **Stack:** 8004 + A2A + x402 (+ MCP, smart accounts) as the default combo; Virtuals ACP and OpenClaw/Moltbook as ecosystems.  
3. **Discovery & tooling:** 8004scan, Agentscan, subgraphs, Agentic Trust, ecosystem maps, news portals, create-trustless-agent.  
4. **Validation tiers:** Receipt/delivery (cheap) vs. proof/compliance (ZK/TLS) vs. quality evaluation; per-request vs. enforced.  
5. **Mainnet & chains:** Base (post-mint phase), Optimism, MegaETH, Monad (in progress); testnets Sepolia, Base Sepolia, Polygon Amoy.  
6. **Trust & safety:** Scams (fake b402, angel/phishing); neutrality (Robin/burned tokens); “don’t share links without context.”  
7. **Privacy:** Stealth addresses (Unwallet), privacy pools (mitchuski), sovereign/dual ledger discussions.  
8. **Events:** Community calls, Devconnect BA, LXDAO hackathon, Patchwork, BUIDL, ETHCC 2026, builder jams and AMAs.

---

## 6. Key quotes (by theme)

*Attributed quotes from the chat; see transcript for exact context.*

**Vision & mandate**  
- Marco & Davide (Sept 3): *"The spec is still a draft—definitely not perfect—but your energy makes one thing crystal clear: we all see the risks of centralized AI, and we're determined to build an AI stack on Ethereum rails where—just like in DeFi—anyone can innovate permissionlessly."*  
- Marco (Olas podcast, Sept 7): *"Reality check: we throw agent around a lot. Most of what ships are smarter interfaces. Truly autonomous, goal-seeking agents are rare."* 8004 tackles distribution, open market, portable/discoverable/trustable.  
- Jay Prakash (Sept 10): *"Specs should not champion a technology. Should suggest expectations of trust and behaviour."*

**Validation & trust**  
- Vitto (Jan 5): *"I definitely wouldn't accept 'staking' as a validation for high sensitivity financial actions."*  
- RandomBlock (Jan 6): Simple = proof of delivery (stake); high risk/compliance = TLS or ZK-TLS; quality evaluation = physical check.  
- GhØsT_PilØT_MD (Feb 1): *"Where things still break down is not discovery or programmability, but enforcement... identity → bounded execution → replayable proof → adversarial validation → escrowed settlement."*

**Mainnet & timeline**  
- Vitto (Jan 7): *"Preparing for mainnet."*  
- Marco (Jan 25): *"ERC-8004 is now frozen... We will go to Mainnet midweek, probably around Thursday 9 AM ET."*  
- Marco (Feb 1): *"Welcome to February - the GENESIS MONTH."*  
- Marco (Feb 2): *"The first 3 days of Mainnet have been beyond our wildest expectations, over 30 agents... The fact that there are so many vanity registrations to mint early 8004 numbers is... very Web3-coded."*

**Ecosystem & builders**  
- Rich Pedersen (Devconnect, Nov 17): *"Incredible day at devconnect. I met all my hero's at metamask. The 8004 community is alive."*  
- Sumeet (Jan 31): *"8004 reputation will soon become a high value asset."*  
- Marco (Feb 2): *"just calling register() 🙈 But please, build cool agents, not batch-minting scripts 😂"*

**Scams & safety**  
- Tony (Jan 18): Fake "angel investors" ask for deck, then demand you download their "software" — phishing/malware.  
- Kantorcodes (Jan 18): *"Very few real VCs or angels will come into a telegram chat and ask for decks."*

**Privacy & UX**  
- Loaf (Sept 3): *"non kyc, onchain way to pay for web2 services"*  
- wilwixq (Sept 7): *"Privacy ensures AI can act on behalf of users without exposing sensitive inputs, outputs, or keys."*

---

## 7. Sample of raw transcript format

Below is a short sample of how messages appear in `transcript.txt` (oldest and most recent):

```
--- 3 September 2025 ---

Marco De Rossi, [03.09.2025 14:32:50 UTC-08:00]
Welcome to the 8004 community!

Over the last few weeks, the Ethereum community's response to 8004 has blown us away...

--- 9 February 2026 ---

Marco De Rossi, [01.02.2026 02:24:07 UTC-08:00]
Gm gm and … Welcome to February - the GENESIS MONTH 🔥🔥🐣🐣🤖🤖
```

Full content: see `ChatExport_2026-02-09/transcript.txt`.

---

## 8. Topic index & session plan (multi-session roadmap)

**How to use this doc across sessions**

- **Topic index** (above, after TOC): Use it to jump to themes (TEE, x402, Validation, ChaosChain, community call, v1, Devconnect, mainnet, etc.) in the synopsis or transcript.
- **Transcript:** `ChatExport_2026-02-09/transcript.txt`. Search by name, keyword, or date. Regenerate with `python extract_chat.py` in the export folder.
- **Extraction:** Parser captures reply context (reply_to message id). Messages with no text body are skipped; media-only messages are not in the transcript.

**Session 1 (this pass)**  
- Extraction verified; reply_to handling added.  
- Topic index and TOC added.  
- **September 2025** deep-dive: weekly subsections (Sept 3–9, 10–16, 17–23, 24–30) with names, quotes, links, first community call, TEE debate, EF AI team, MetaMask x402, Genesis Studio, LXDAO/Agentic Zero.  
- **October 2025** deep-dive: pre–v1 (Oct 1–6), v1 launch (Oct 7–9), post–v1 (b402 scam, bidirectional 8004, privacy pools, LXDAO).

**Session 2 (done)**  
- **November 2025** deep-dive: §2.3.1–2.3.3 (Devconnect BA, 8004scan v2, Alias/Agentscan, 8004.net, DCAP, ChaosChain 5k, Vitalik, etc.).  
- **December 2025** deep-dive: §2.4.1–2.4.3 (Validation scope, awesome-8004, 8004scan validation live, create-8004-agent, news portal, Patchwork, mainnet after New Year).

**Session 3 (done)**  
- **January 2026** deep-dive: §2.5.1–2.5.3 (validation tiers, Virtuals ACP, Agentokratia, mainnet prep/freeze, WachAI Mandates, XMTP, scam warnings, Marco frozen spec, midweek mainnet).  
- **February 2026** deep-dive: §2.6.1–2.6.2 (Genesis month, ClawLoan, ElizaTown, clawmaster/clawnews, Monad/Polygon, Position agents, AGI Alpha/AGIJobs, ChaosChain/Hardik skills, ETHCC 2026).

**Session 4 (done)**  
- Topic index expanded with per-project anchors (Agentic Trust, Alias/Agentscan, WachAI, MONTREAL AI, create-8004-agent, ClawLoan, ElizaTown, OyaChat, XMTP, ETHCC 2026).  
- §6 Key quotes appendix by theme (vision, validation, mainnet, ecosystem, scams, privacy).

---

*Document built from ChatExport_2026-02-09 and web research. Sessions 1–4: extraction, topic index, Sept 2025–Feb 2026 deep-dives, Key quotes. Summary and context as of Feb 9, 2026.*
