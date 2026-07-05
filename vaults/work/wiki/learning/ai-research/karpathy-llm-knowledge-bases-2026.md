---
title: "Karpathy — LLM Knowledge Bases (April 2026)"
date: 2026-04-19
domain: learning
tags: [ai-research, article, agents, mcp]
status: active
---

# Karpathy — LLM Knowledge Bases (April 2026)

Article / thread notes from [[Andrej Karpathy]]'s viral X thread posted April 2–3, 2026, describing his workflow for using LLMs to build personal knowledge bases. Source: https://x.com/karpathy/status/2039805659525644595

## Core Argument

Karpathy has shifted a large fraction of his LLM token usage from **code manipulation** to **knowledge manipulation** — treating the LLM as a compiler that reads raw sources and incrementally produces a structured, interlinked Markdown wiki.

> "raw data from a given number of sources is collected, then compiled by an LLM into a .md wiki, then operated on by various CLIs by the LLM to do Q&A and to incrementally enhance the wiki, and all of it viewable in Obsidian. You rarely ever write or edit the wiki manually, it's the domain of the LLM."

## Why Not RAG?

At ~100 articles / ~400K words, a well-maintained `index.md` + LLM context window is sufficient for retrieval. No embeddings or vector DB required. The LLM auto-maintains index files and brief summaries, then reads the relevant data directly.

## Key Insights from the Thread

- **Process is not fully autonomous** — Karpathy adds sources manually one by one; after a while the LLM "gets the pattern" and the marginal document becomes much easier to file.
- **Queries always add up** — outputs from Q&A sessions are filed back into the wiki, creating a compounding flywheel.
- **Vibe-coded tooling** — a small, naive search engine was built to serve both a web UI and a CLI tool handed off to the LLM for larger queries.
- **Future: synthetic fine-tuning** — use the KB to generate synthetic data and fine-tune an LLM to know it in weights, not just context.

## Notable Replies

- **Lex Fridman** — uses a similar setup; generates dynamic HTML with JS for interactive visualisations; creates temporary "mini knowledge bases" for topic-focused voice-mode LLM sessions during runs.
- **Enterprise angle (Edra AI)** — same ingest–compile–lint–enhance loop applied at org scale (tickets, logs, emails); "the knowledge layer for AI agents is the next great system of record."
- **Scale warning** — at ~4M words the index-navigation approach likely breaks down; "no RAG needed" is scale-dependent.
- **Vault contamination concern** — one reply recommends keeping agent-created and personally-created content in separate Obsidian vaults to preserve signal-to-noise ratio.
- **Product opportunity** — multiple replies note potential for a cloud-hosted, multiplayer, API/MCP-accessible version (one reply noted the domain `secondbrain.com`).

## GitHub Gist

Karpathy published a replicable "idea file":
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Related Concepts
- [[LLM Knowledge Base Pattern]] — the settled concept page distilled from this article
- [[Andrej Karpathy]] — author
