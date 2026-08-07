# Jaden Green — GreenAI Solutions

**I build systems that ship with their own evidence.**

Retrieval engines, agent orchestration, and developer tooling. I design and specify the systems,
direct AI coding agents to write them, and — the part that actually decides whether any of it is
worth anything — verify the result against something external.

Most AI-built software is unfalsifiable: it measures itself on a corpus it invented and reports that
it did well. The two repositories below are pinned because they are the opposite. Each makes a
specific numeric promise, and each is set up so a stranger can prove me wrong in one command.

---

## 🔬 [STRATA](https://github.com/GreenAiSolution/greenai-strata) — hybrid retrieval, built to be measured

Semantic search, hybrid lexical+dense scoring, an ANN index, and an LLM re-ranker — every layer
written from scratch on numpy, every layer swappable, and an evaluation harness that reports what
each layer is actually worth on your corpus.

```
documents → chunk → ┌─ BM25 (inverted index) ─┐
                    │                          ├─ fusion (RRF | weighted α) → re-rank → trace
                    └─ dense vectors → HNSW ───┘
```

The architecture is not the interesting part — everyone's diagram looks like that. The interesting
part is that it reproduces on public data:

| Reproduction | Reference | Mean abs. deviation |
|---|---|---|
| Hand-rolled **BM25** — own tokeniser, own inverted index, own Porter stemmer, no Lucene anywhere | Anserini / BEIR published nDCG@10, 5 datasets | **0.0066** (worst: 0.0102) |
| **Dense leg** driving `bge-base-en-v1.5` | BAAI's own published model-index | **0.0004** (SciFact agrees to 4 d.p.) |

Two independent reproductions, against references from different authors using different toolkits.
A pipeline with a bug in the shared parts — loader, qrels handling, ranking, metric — could not hit
both. The metrics themselves are differentially tested against NIST's `trec_eval`.

**205 tests. One runtime dependency (numpy). No GPU, no API keys.** The BEIR suite runs in ~4 minutes
on a laptop, and [BEIR.md](https://github.com/GreenAiSolution/greenai-strata/blob/main/BEIR.md)
publishes the unflattering results too — where the ANN index is slower than brute force, where the
re-ranker makes things worse, and the recall ceiling retrieval imposes on everything downstream.

## 🧭 [schemadrift](https://github.com/GreenAiSolution/schemadrift) — "breaking" depends on who you are

Infers a JSON schema from real payloads, then diffs two captures to tell you *who* a change breaks.

The design bet: **breaking is not a property of a change, it's a property of a change plus your
role.** Adding `null` to a response field breaks every consumer that reads it and costs the producer
nothing. Adding a required request field is the exact mirror. Tools that ignore this either cry wolf
on every diff or stay silent through a real outage.

So every change kind carries two severities, and the same two files return opposite verdicts:

```console
$ schemadrift diff orders-v1.ndjson orders-v2.ndjson              # 3 breaking, 1 additive
$ schemadrift diff orders-v1.ndjson orders-v2.ndjson --role producer   # 1 breaking, 3 additive
```

The severity table is deliberately antisymmetric, and a test asserts the exact set of change kinds
allowed to be symmetric — so the idea can't quietly rot into a normal differ. Inference from samples
is a guess, so every finding also carries a confidence and low-confidence findings are reported but
don't fail your build.

**60 tests, CI on Python 3.9/3.11/3.13, zero dependencies.**

---

## How I actually work

I'm a founder who directs AI coding agents rather than a developer who types every line, and I'd
rather say that plainly than have you infer it from my commit history.

What that makes me good at is the part the models are worst at:

- **Specification** — deciding what the system must be true about before any code exists.
- **Verification** — doer ≠ checker. The agent that builds a thing never grades it. Most of my
  infrastructure exists to make claims falsifiable, which is why STRATA leads with a baseline
  reproduction instead of a benchmark win.
- **Knowing when a number is worthless.** A result measured on a corpus you built yourself is
  development feedback, not evidence. That distinction drives most of my architecture decisions.

The product repos below each ship an **MCP server** — a working `mcp-server/` exposing that
project's data and workflows as tools, so an AI assistant can operate the project directly. Clone,
`claude mcp add`, go. (The two pinned libraries above are plain CLIs; they're meant to be run in
CI, not driven by an agent.)

---

## Also public

| Project | What it is |
|---|---|
| [Addtophxgrowth](https://github.com/GreenAiSolution/Addtophxgrowth) | Multi-tenant Next.js 14 client platform — Prisma/Neon **pgvector**, Stripe, NextAuth, scheduled jobs, guardrail tests, dual MCP servers. Live on Vercel. |
| [choreless](https://github.com/GreenAiSolution/choreless) | Omniagent — WhatsApp AI agents for real businesses: multimodal RAG over n8n workflows, with memory and CONFIRM-gated actions. |
| [greengeniusai](https://github.com/GreenAiSolution/greengeniusai) | AI trading platform — Claude analyses equities & crypto and explains every trade, executed through Alpaca. |
| [greenai-aether](https://github.com/GreenAiSolution/greenai-aether) | Scroll-cinematic WebGL metropolis for an autonomous agent service. **No framework, no build step.** |
| [nexus-studio](https://github.com/GreenAiSolution/nexus-studio) | Immersive 3D storefront for designing and buying an AI workforce (Three.js). |
| [Pixel-Pilot-](https://github.com/GreenAiSolution/Pixel-Pilot-) | Autonomous media-buyer platform presented as an immersive 3D Next.js experience. |
| [greenai-solutions-group](https://github.com/GreenAiSolution/greenai-solutions-group) | [greenaidigital.com](https://greenaidigital.com) — static site + Cloudflare Worker AI backend. |

## Private, available on request

**LATTICE** — enterprise RAG with ACL-aware citations and an eval suite · **ANVIL** — AST-based code
review and real refactor diffs · **CONDUCTOR** — agent orchestrator with a tool registry, DAG
executor and doer≠checker gates · **GRAVITY** — trained two-tower recommender with live re-ranking ·
**SENTINEL** — predictive maintenance and edge IoT, pure-stdlib DSP/ML.

*(Numbers on these are self-measured on my own corpora — useful for development, not evidence.
STRATA and schemadrift are pinned precisely because they aren't.)*

---

## Stack

`Python` · `numpy` · `TypeScript` · `React` · `Next.js` · `Three.js` · `Postgres / pgvector` ·
`Prisma` · `Vercel` · `MCP (Model Context Protocol)` · `Claude API & agent pipelines`

📫 **jadengreen808@gmail.com** · 📍 Gilbert, AZ
