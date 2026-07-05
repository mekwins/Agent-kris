---
date: '2026-04-19'
domain: learning
source_url: https://x.com/karpathy/status/2039805659525644595
status: processed
tags:
- ai-research
- article
- agents
- mcp
title: Karpathy - LLM Knowledge Bases (April 2026)
---

## Summary

On April 2–3, 2026, Andrej Karpathy posted a viral thread titled **"LLM Knowledge Bases"** describing a shift in how he uses AI — from writing code to building personal knowledge bases (wikis) for research topics.

> "A large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge."

The tweet went viral. In response, Karpathy published a GitHub Gist "idea file" for others to replicate: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

---

## Core Pattern: LLM as Compiler

Instead of RAG (chunking → embeddings → vector search), Karpathy proposes treating the LLM as a **compiler** that reads raw sources and incrementally produces a structured, interlinked Markdown wiki.

### Workflow:
1. **Collect** — Drop raw articles, papers, repos, images into a `raw/` folder
2. **Compile** — LLM reads raw sources and writes wiki pages: summaries, concept articles, backlinks, cross-references
3. **View** — Use Obsidian to browse the wiki
4. **Ask** — Query the LLM against the wiki (it reads index.md first, then drills into relevant pages)
5. **Create** — LLM outputs slides (Marp), charts (Matplotlib), new notes — all filed back into the wiki
6. **Maintain** — LLM runs health checks: find contradictions, fill gaps, fix broken links

---

## Why Not RAG?

At personal knowledge base scale (~100 articles, ~400K words), a well-maintained `index.md` + LLM context window is sufficient for retrieval. No embeddings, no vector DB. The index file (a few thousand tokens) tells the LLM which pages to read directly.

Key insight: **"Explorations always add up"** — every query and answer gets filed back, making the wiki denser over time.

---

## Tooling Mentioned

- **Obsidian** — local-first Markdown viewer with graph view, backlinks, Marp plugin
- **Marp** — Markdown → slide decks (also exports PDF/PPTX)
- **Matplotlib** — LLM-generated charts filed back into wiki
- **Custom CLI scripts** — vibe-coded Python bridges between LLM and filesystem
- **Claude Code / OpenAI Codex** — agent that reads/writes the local markdown vault

---

## Future Direction (Karpathy's)

Use the wiki to generate **synthetic training data** and fine-tune an LLM so it "knows" the knowledge base in its weights — not just through context. Personal KB → personalized model.

---

## Relevance to Brain System

This is essentially what the [[Brain]] system implements — inbox → compile → wiki — built before seeing this tweet. Strong validation of the architecture. Key differences:
- Brain uses MCP server for tool integration vs. CLI scripts
- Brain uses hybrid semantic+keyword search vs. index.md navigation
- Both use incremental compilation and wikilinks

---

## Reception

- Lex Fridman confirmed using a similar setup, adding dynamic HTML visualizations and ephemeral "mini knowledge bases" for long runs
- GitHub Gist forked widely; multiple tutorials/products spawned within days
- VentureBeat coverage framed it as "second brain" architecture that's self-healing, auditable, human-readable