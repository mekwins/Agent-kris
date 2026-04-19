# Brain Project — Architecture Spec

> **Purpose**: Specification for Kris Mekwinski's personal AI-powered second brain system.
> Last updated: April 19, 2026 — reflects all decisions from the initial design session.

---

## 1. Concept Overview

A personal knowledge system where:

- Raw content (emails, URLs, notes, conversations) flows into **inbox/** or **sources/**
- A **compilation agent** (Anthropic API) reads raw sources and synthesizes a structured **wiki** of interconnected markdown pages
- A **Brain MCP server** exposes the vault to any Claude client or agent via 5 standardized tools
- **Hybrid search** (vector embeddings + keyword) enables both semantic and exact lookup
- A **trigger layer** (WhatsApp + webhook) allows remote invocation from any device
- **Live connectors** pull content from enterprise systems (email, Teams, Outlook) automatically

Inspired by Andrej Karpathy's "LLM Wiki" pattern:
> *"Obsidian is the IDE, the LLM is the programmer, the wiki is the codebase."*

**Key difference from the pattern**: no interactive Claude Code sessions or slash commands.
Everything is driven programmatically via the Agent SDK and trigger layer.

---

## 2. Architecture

### 2.1 Layer Model

```
┌──────────────────────────────────────────────────────────┐
│                    INTERFACES                            │
│  WhatsApp · Claude Desktop · Claude Mobile · Future     │
└──────┬───────────────────┬──────────────────────────────┘
       │ HTTP webhook       │ MCP protocol (stdio)
       ▼                    ▼
┌──────────────┐   ┌────────────────────────────────────┐
│ TRIGGER LAYER│   │         MCP SERVER                 │
│ FastAPI +    │   │  brain_search · brain_recall       │
│ Twilio/Meta  │   │  brain_write · brain_context       │
│ WhatsApp     │   │  brain_relate                      │
└──────┬───────┘   └──────────────────┬─────────────────┘
       │                              │
       ▼                              │
┌──────────────────────┐              │
│   AGENT SDK LAYER    │              │
│  anthropic Python    │              │
│  SDK + tool use      │              │
│                      │              │
│  compile agent       │              │
│  query agent         │              │
│  connector agent     │              │
└──────────┬───────────┘              │
           │                          │
           ▼                          ▼
┌──────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                         │
│                                                          │
│  vault/ (local filesystem — markdown + frontmatter)      │
│    ├── inbox/     ← landing zone (brain_write / agent)   │
│    ├── wiki/      ← compiled knowledge (agent writes)    │
│    │   ├── index.md   (master TOC)                       │
│    │   ├── log.md     (activity log)                     │
│    │   ├── concepts/                                     │
│    │   ├── people/                                       │
│    │   ├── projects/                                     │
│    │   └── areas/                                        │
│    └── sources/   ← raw imports (connectors write here)  │
│        ├── work/  (email, Teams, Outlook, Nexteer)       │
│        └── personal/                                     │
│                                                          │
│  vault/.vectors.json  ← local JSON vector store          │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Vault Folder Structure

```
vault/
├── CLAUDE.md                 # Schema, rules, tag taxonomy (agent reads this)
├── inbox/                    # Landing zone — new content arrives here
│   └── YYYY-MM-DD-slug.md
├── wiki/                     # Agent-compiled knowledge — structured + wikilinked
│   ├── index.md              # Master table of contents (agent-maintained)
│   ├── log.md                # Chronological activity log (agent-maintained)
│   ├── concepts/             # One page per concept/topic
│   ├── people/               # One page per named person
│   ├── projects/             # Project-specific pages
│   └── areas/                # Ongoing areas of interest
└── sources/                  # Immutable raw inputs — agent reads, never edits
    ├── work/
    │   ├── email/
    │   ├── teams/
    │   ├── ai-strategy/
    │   ├── enterprise-architecture/
    │   └── nexteer/
    ├── personal/
    │   ├── health/
    │   ├── language-learning/
    │   └── interests/
    ├── books/
    └── podcasts/
```

### 2.3 Data Flows

**Ingest path — manual (WhatsApp or Claude chat)**
```
User sends message to WhatsApp
  → Trigger layer receives webhook
  → Intent detected: "remember X" / "add to brain"
  → brain_write() called → file written to inbox/ + auto-embedded
  → WhatsApp reply: "Added to brain: [domain] / [title]"
```

**Ingest path — live connector**
```
Connector runs on schedule (or triggered via WhatsApp "sync email")
  → Fetches new emails / Teams messages via IMAP / API
  → Writes markdown files to sources/work/email/ or sources/work/teams/
  → Triggers compile agent
```

**Compile path — agent**
```
Agent triggered ("compile inbox" via WhatsApp or direct call)
  → Lists inbox/ files with status: inbox
  → For each: classifies domain, extracts concepts + people
  → Creates/updates wiki/concepts/*.md and wiki/people/*.md with [[wikilinks]]
  → Updates wiki/index.md (TOC) and wiki/log.md (activity)
  → Marks inbox files: status: inbox → processed
  → Re-embeds new/updated wiki pages via brain_write
```

**Query path — read**
```
User asks question via WhatsApp or Claude
  → brain_search(query) → hybrid search (semantic + keyword)
  → Top chunks + pages returned
  → If via WhatsApp: query agent synthesizes cited answer → WhatsApp reply
  → If via Claude Desktop/Mobile: MCP tools return raw results to Claude
```

---

## 3. MCP Server Specification

### 3.1 Platform

**Python + FastMCP** — local stdio transport, runs on the same machine as the vault.

- Transport: stdio (registered in Claude Desktop / Claude Code settings)
- No cloud hosting required for local-first phase
- Provider-agnostic: embeddings via any OpenAI-compatible HTTP endpoint

### 3.2 Tool Definitions

```python
# Hybrid search across all vault content (semantic + keyword, merged)
brain_search(
    query: str,
    scope: Literal["work", "personal", "learning", "all"] = "all",
    limit: int = 10,
    mode: Literal["hybrid", "semantic", "keyword"] = "hybrid"
) -> dict  # { chunks: list[Chunk], pages: list[WikiPage] }

# Fetch a specific wiki page + its wikilinked neighbors
brain_recall(
    topic: str,              # Page slug or title (case-insensitive)
    depth: Literal[1, 2] = 1
) -> dict  # { page: WikiPage, related: list[WikiPage] }

# Write content to inbox/ and auto-index it
brain_write(
    content: str,
    tags: list[str],
    domain: Literal["work", "personal", "learning"],
    title: str | None = None,
    source_url: str | None = None
) -> dict  # { path: str, committed: bool, chunks_indexed: int }

# Top-10 recent pages filtered for a specific agent persona
brain_context(
    agent_type: Literal["work", "personal", "research"]
) -> dict  # { context: str, key_pages: list[WikiPage] }

# Connection path + shared tags between two wiki concepts
brain_relate(
    concept_a: str,
    concept_b: str
) -> dict  # { path: list[str], shared_tags: list[str], direct_link: bool }
```

### 3.3 Response Types

```python
class WikiPage(TypedDict):
    slug: str
    title: str
    domain: str           # work | personal | learning
    tags: list[str]
    content: str          # Full markdown body
    wikilinks: list[str]  # Outbound [[links]]
    updated_at: str

class Chunk(TypedDict):
    page_slug: str
    content: str
    score: float          # Cosine similarity (semantic) or 1.0 (keyword)
    match_type: str       # "semantic" | "keyword"
    tags: list[str]
    domain: str
```

### 3.4 Project Structure

```
Agent-kris/
├── src/
│   ├── server.py          # FastMCP entry point — registers 5 MCP tools
│   ├── config.py          # Env var loading (EMBEDDING_ENDPOINT, VAULT_PATH, etc.)
│   ├── vault.py           # Markdown read/write with python-frontmatter
│   ├── embed.py           # HTTP POST to any OpenAI-compatible endpoint (httpx)
│   ├── vector_store.py    # Local JSON vector store + numpy cosine similarity
│   ├── search.py          # Hybrid/semantic/keyword search orchestration
│   ├── agent.py           # Anthropic API agentic loop (compile, query, lint)
│   └── tools/
│       ├── brain_search.py
│       ├── brain_recall.py
│       ├── brain_write.py
│       ├── brain_context.py
│       └── brain_relate.py
├── connectors/
│   ├── base.py            # Abstract base connector
│   └── email.py           # IMAP connector (Outlook / Gmail)
├── trigger/
│   ├── app.py             # FastAPI webhook server
│   └── whatsapp.py        # WhatsApp message parsing + routing
├── scripts/
│   └── index_vault.py     # Rebuild full vector index from vault
├── vault/
│   ├── CLAUDE.md
│   ├── inbox/
│   ├── wiki/
│   │   ├── index.md
│   │   ├── log.md
│   │   ├── concepts/
│   │   ├── people/
│   │   ├── projects/
│   │   └── areas/
│   └── sources/
├── .env
├── .env.example
├── .gitignore
└── pyproject.toml
```

---

## 4. Agent SDK Layer

### 4.1 Compile Agent

The compile agent replaces interactive Claude Code slash commands with a programmatic agentic loop.

**Trigger**: called with a task string — from WhatsApp, a webhook, or directly in Python.

**Tools available to the agent**:

```python
list_vault_files(directory: str) -> list[str]
read_vault_file(path: str) -> str
write_vault_file(path: str, content: str) -> bool
mark_processed(path: str) -> bool           # sets status: processed in frontmatter
brain_search(query: str, ...) -> dict       # calls MCP tool logic directly
```

**System prompt summary**:
- You are a knowledge compiler. Read inbox/ and sources/ files.
- Extract concepts → write wiki/concepts/. Extract people → write wiki/people/.
- Use [[wikilinks]] to link related pages. Never invent facts.
- Update wiki/index.md (TOC) and wiki/log.md (activity) after each compile run.
- Mark processed inbox files. Re-embed new/updated wiki pages.

### 4.2 Supported Agent Tasks

| Task string | What the agent does |
|-------------|-------------------|
| `"compile inbox"` | Full ingest loop — all unprocessed inbox files |
| `"compile inbox limit=N"` | Batch compile, max N files |
| `"compile sources"` | Re-compile from sources/ (after connector sync) |
| `"search: <question>"` | Read relevant wiki pages, synthesize cited answer |
| `"lint"` | Check broken wikilinks, orphan pages, missing frontmatter |

---

## 5. Trigger Layer

### 5.1 WhatsApp Interface

Primary user interface for interacting with the brain remotely.

**Stack**: FastAPI + Twilio WhatsApp Business API (or Meta Cloud API)

**Intent routing**:

| Message pattern | Action |
|----------------|--------|
| "remember...", "add to brain...", "save..." | `brain_write` → inbox |
| "compile", "ingest", "process inbox" | `agent.run("compile inbox")` |
| "sync email", "fetch email" | email connector → compile |
| "what do I know about X", "search X" | `brain_search` → agent synthesis → reply |
| "recall X", "tell me about X" | `brain_recall` → formatted reply |

### 5.2 Running Both Servers

```bash
# MCP server (for Claude Desktop / Claude Code)
uv run python -m src.server

# Trigger / webhook server (for WhatsApp)
uv run python -m trigger.app

# Expose trigger server via ngrok for WhatsApp webhook registration
ngrok http 8000
```

---

## 6. Embedding & Vector Store

### 6.1 Embedding

- Model: `text-embedding-3-small` (1536 dimensions)
- Provider: Any OpenAI-compatible endpoint — currently Azure OpenAI
- Auth: `api-key` header (Azure) — switchable via `.env` only, no code change needed
- Implementation: raw `httpx` POST, no SDK dependency

```python
# .env
EMBEDDING_ENDPOINT=https://<resource>.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-05-15
EMBEDDING_API_KEY=<key>
```

### 6.2 Vector Store

- Local JSON file at `vault/.vectors.json` (gitignored)
- Cosine similarity via numpy — no external vector DB needed for personal scale
- Rebuilt with `python scripts/index_vault.py` after bulk content changes
- Auto-updated on every `brain_write` call

### 6.3 Chunking Strategy

```
For each markdown file:
  1. Split on H2 headings → sections
  2. If section > 400 words → split on paragraphs
  3. Each chunk stores: { page_slug, content, section, tags, domain, embedding }
```

### 6.4 Search Modes

| Mode | Method | Best for |
|------|--------|----------|
| `hybrid` (default) | Semantic first, keyword additions | General use |
| `semantic` | Cosine similarity on embeddings | Conceptual queries |
| `keyword` | Regex full-text scan across vault | Exact names/terms |

---

## 7. Live Connectors

### 7.1 Email Connector

```python
# connectors/email.py
class EmailConnector(BaseConnector):
    async def sync(self) -> list[str]:
        # IMAP fetch → filter → write to sources/work/email/
        # Returns list of new file paths
```

Fetches unread/flagged emails, converts to markdown with frontmatter, writes to `sources/work/email/`. After sync, calls compile agent.

### 7.2 Future Connectors

| Source | Path |
|--------|------|
| Microsoft Teams | `sources/work/teams/` |
| Outlook Calendar | `sources/work/calendar/` |
| SharePoint / OneDrive | `sources/work/sharepoint/` |
| Slack | `sources/work/slack/` |

---

## 8. Vault Governance (CLAUDE.md Schema)

The file at `vault/CLAUDE.md` governs how the compile agent maintains the wiki.

### Frontmatter template
```yaml
---
title: ""
date: YYYY-MM-DD
domain: work | personal | learning
tags: []
source_url: ""
status: inbox | processed
---
```

### Tag taxonomy

**Work**: `nexteer` `enterprise-architecture` `ai-strategy` `vibe-coding` `governance` `agents` `mcp` `coolify` `claude-enterprise`

**Personal**: `health` `language-learning` `polish` `spanish` `travel` `pixel` `birdy`

**Learning**: `book` `podcast` `article` `course` `ai-research` `engineering`

### Wiki page rules
- Every page: `title`, `domain`, `tags`, 2-3 sentence summary, `[[wikilinks]]`
- One concept per page — split pages covering multiple concepts
- Never delete — mark outdated content with tag `archived`
- People pages: one per named person, link to their ideas and quotes

### Domain routing
- Nexteer / EA / AI CoE / IT → `domain: work`
- Health / family / hobbies / Pixel / Birdy → `domain: personal`
- Books / courses / research / general AI → `domain: learning`

---

## 9. External Conversation Import

**One-off**: Paste a ChatGPT share URL into WhatsApp → trigger layer fetches + calls `brain_write`.

**Bulk**: Export from ChatGPT (Settings → Data Controls → Export) → run `scripts/import_chatgpt.py`:
1. Reads `conversations.json`
2. Filters by date or keyword
3. Writes each as an inbox markdown file
4. Triggers compile agent

---

## 10. Technology Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| MCP server | Python + FastMCP (stdio) | ✅ Done |
| Vector store | Local JSON + numpy cosine similarity | ✅ Done |
| Embedding model | `text-embedding-3-small` via generic HTTP | ✅ Done |
| Embedding provider | Azure OpenAI (switchable via `.env`) | ✅ Done |
| Search | Hybrid: semantic + keyword | ✅ Done |
| Vault filesystem | Local markdown + python-frontmatter | ✅ Done |
| Compilation agent | Python + Anthropic API (`claude-sonnet-4-6`) | 🔲 Phase 2 |
| Trigger server | FastAPI + Twilio WhatsApp | 🔲 Phase 3 |
| Email connector | Python IMAP (aioimaplib) | 🔲 Phase 4 |
| Teams connector | Microsoft Graph API | 🔲 Phase 4 |
| Wiki structural files | `wiki/index.md` + `wiki/log.md` | 🔲 Phase 5 |

---

## 11. Implementation Phases

```
Phase 1 — MCP Server ✅ COMPLETE
  [x] FastMCP server with 5 tools (brain_search, brain_recall, brain_write,
      brain_context, brain_relate)
  [x] Hybrid search (semantic + keyword)
  [x] Local JSON vector store + numpy cosine similarity
  [x] Azure OpenAI embeddings via httpx (provider-agnostic)
  [x] Vault folder structure + vault/CLAUDE.md
  [x] scripts/index_vault.py

Phase 2 — Agent SDK: Compilation Loop
  [ ] src/agent.py — Anthropic API agentic loop with file tools
  [ ] System prompt: compile inbox → wiki pages + wikilinks
  [ ] Agent tasks: compile, search/synthesize, lint
  [ ] vault/wiki/index.md + vault/wiki/log.md structural files
  [ ] End-to-end test: inbox file → compile → wiki page → search

Phase 3 — Trigger Layer
  [ ] trigger/app.py — FastAPI webhook server
  [ ] trigger/whatsapp.py — intent parsing + routing
  [ ] Twilio WhatsApp sandbox setup
  [ ] Intent → action routing table
  [ ] End-to-end test: WhatsApp message → brain_write → reply

Phase 4 — Live Connectors
  [ ] connectors/base.py — abstract base connector
  [ ] connectors/email.py — IMAP connector (Outlook / Gmail)
  [ ] Scheduled sync (cron or WhatsApp-triggered)
  [ ] Teams connector (Microsoft Graph API)

Phase 5 — Seed + Validate
  [ ] Drop first real content into sources/ (email export, articles)
  [ ] Run compile agent end-to-end
  [ ] Run index_vault.py to embed all wiki pages
  [ ] Test full flow: WhatsApp question → search → cited answer
  [ ] scripts/import_chatgpt.py for bulk ChatGPT export
```

---

## 12. Open Decisions

| Decision | Current choice | Notes |
|----------|---------------|-------|
| Embedding provider | Azure OpenAI | Switchable via `.env` — no code change needed |
| Vector store | Local JSON | Sufficient for personal scale; can upgrade to pgvector later |
| WhatsApp API | Twilio (sandbox) | Meta Cloud API for production |
| Agent model | `claude-sonnet-4-6` | Best reasoning for compilation task |
| Connector auth | IMAP app password | MS Graph OAuth for Teams/Outlook |

---

*Architecture designed for personal use by Kris Mekwinski*
*Implementation language: Python — Anthropic API + FastMCP + FastAPI*
*Last updated: April 19, 2026*
