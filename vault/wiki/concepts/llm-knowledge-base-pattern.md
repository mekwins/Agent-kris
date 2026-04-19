---
title: "LLM Knowledge Base Pattern"
date: 2026-04-19
domain: learning
tags: [ai-research, agents, mcp]
status: active
---

# LLM Knowledge Base Pattern

A workflow in which an LLM acts as a **compiler** — reading raw source documents and incrementally producing a structured, interlinked Markdown wiki — rather than as a query engine over a vector database. Popularised by [[Andrej Karpathy]] in April 2026 and validated by the architecture of this vault.

## Key Points

- **Ingest → Compile → View → Ask → Create → Maintain** is the core loop: raw sources go into a `raw/` folder, the LLM writes wiki pages with summaries, backlinks, and cross-references, and Obsidian (or equivalent) serves as the IDE/viewer.
- **No RAG needed at small-medium scale** — at ~100 articles / ~400K words, an auto-maintained `index.md` + LLM context window is sufficient for retrieval. No embeddings or vector DB required.
- **Queries always add up** — every Q&A session produces outputs that are filed back into the wiki, making it denser and more valuable over time (compounding knowledge flywheel).
- **LLM health checks (linting)** — the LLM can run periodic checks to find contradictions, impute missing data, identify broken links, and suggest new article candidates.
- **Scale caveat** — the "no RAG" conclusion is scale-dependent. At ~4M words the index-navigation approach likely breaks down and vector search becomes necessary.
- **Vibe-coded tooling** — supplementary CLI scripts and search tools are added as needed and handed to the LLM as tools for larger queries.

## Workflow Stages

| Stage | Description |
|-------|-------------|
| **Collect** | Drop raw articles, papers, repos, images into `raw/` |
| **Compile** | LLM reads sources and writes wiki pages with summaries, concepts, backlinks |
| **View** | Browse wiki in Obsidian (graph view, backlinks, Marp plugin) |
| **Ask** | Query the LLM; it reads `index.md` first, then drills into relevant pages |
| **Create** | LLM outputs slides (Marp), charts (Matplotlib), new notes — filed back into wiki |
| **Maintain** | LLM health checks: contradictions, missing data, broken links, gap analysis |

## Tooling

- **Obsidian** — local-first Markdown viewer; graph view, backlinks, Marp plugin for slides
- **Marp** — Markdown → slide decks (PDF/PPTX export)
- **Matplotlib** — LLM-generated charts, filed back into wiki
- **Claude Code / OpenAI Codex** — agent that reads/writes the local vault
- **Custom CLI scripts** — vibe-coded Python bridges between LLM and filesystem

## Relationship to This Vault

This vault implements the same pattern. Key architectural differences vs. Karpathy's setup:
- Uses an MCP server for tool integration (vs. CLI scripts)
- Uses hybrid semantic + keyword search (vs. pure `index.md` navigation)
- Both use incremental compilation and `[[wikilinks]]`

## Future Direction

Karpathy flagged the natural next step: use the knowledge base to generate **synthetic training data** and fine-tune an LLM so it "knows" the KB in its weights rather than only through context window.

## Community Reception

- Lex Fridman confirmed a similar setup, adding dynamic HTML visualisations and ephemeral "mini knowledge bases" loaded into voice-mode LLM for interactive learning on runs.
- GitHub Gist forked widely; multiple tutorials and products spawned within days.
- VentureBeat framed it as "second brain" architecture that is self-healing, auditable, and human-readable.
- Enterprise angle noted: same ingest–compile–lint–enhance loop applied to org-scale tickets, logs, and emails (Edra AI).

## Related Concepts
- [[Andrej Karpathy]] — originator of the April 2026 viral thread describing this pattern
- [[Vibe Coding]] — adjacent concept; vibe-coded tooling is used to build the supporting CLI scripts

## Sources
- [[Karpathy — LLM Knowledge Bases (April 2026)]]
