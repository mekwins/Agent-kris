# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal AI second brain system for Kris Mekwinski. Two active layers:
1. **MCP Server** (`src/`) — 6 tools exposing the vault to Claude Desktop (primary interface)
2. **Agent SDK** (`src/agent.py`) — Anthropic API agent that compiles inbox/sources → wiki, triggered via `brain_compile` MCP tool

## Commands

```bash
# Install / update dependencies
uv sync

# Run MCP server (stdio — registers with Claude Desktop / Claude Code)
uv run python -m src.server

# Run trigger/webhook server (WhatsApp interface)
uv run python -m trigger.app

# Rebuild full vector index from vault/wiki/ and vault/sources/
uv run python scripts/index_vault.py
```

## Registering the MCP server with Claude Code

Add to `.claude/settings.json` or `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "brain": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/Users/krzysztofmekwinski/Desktop/Agent-kris"
    }
  }
}
```

## Architecture

```
src/
├── server.py        — FastMCP (stdio). Registers all 5 MCP tools.
├── config.py        — Env vars: EMBEDDING_ENDPOINT, EMBEDDING_API_KEY, VAULT_PATH
├── vault.py         — Read/write markdown with YAML frontmatter. keyword_search().
├── embed.py         — httpx POST to any OpenAI-compatible embedding endpoint (no SDK)
├── vector_store.py  — JSON vector store at vault/.vectors.json. Cosine sim via numpy.
├── search.py        — Hybrid / semantic / keyword orchestration.
├── agent.py         — Anthropic API agentic loop: compile, query, lint tasks.
└── tools/           — One module per MCP tool (thin wrappers over core modules).

trigger/
├── app.py           — FastAPI webhook server (WhatsApp entry point).
└── whatsapp.py      — Intent parsing → routes to brain_write / agent / brain_search.

connectors/
├── base.py          — Abstract base connector.
└── email.py         — IMAP connector → writes to sources/work/email/.
```

## MCP Tools

| Tool | Key params | Purpose |
|------|-----------|---------|
| `brain_search` | `query`, `scope`, `mode` (hybrid/semantic/keyword) | Search vault |
| `brain_recall` | `topic`, `depth` (1 or 2) | Fetch page + wikilinked neighbors |
| `brain_write` | `content`, `tags`, `domain`, `title?`, `source_url?` | Write to inbox + auto-embed |
| `brain_clip` | `url`, `domain?`, `tags?` | Fetch URL → markdown + download images to vault/assets/ |
| `brain_context` | `agent_type` (work/personal/research) | Top-10 recent pages for a persona |
| `brain_relate` | `concept_a`, `concept_b` | Shared tags + graph path between concepts |
| `brain_compile` | `task`, `limit?`, `query?` | Run compilation agent (compile inbox/sources, lint, search) |

## Vault structure

```
vault/
├── CLAUDE.md        — Vault schema, tag taxonomy, compile rules (agent reads this)
├── FOLDERS.md       — Extensible folder registry (agent reads at compile start; add new folders here)
├── inbox/           — New notes land here via brain_write
├── wiki/            — Agent-compiled knowledge with [[wikilinks]]
│   ├── index.md     — Master TOC (agent-maintained)
│   ├── log.md       — Activity log (agent-maintained)
│   ├── concepts/    — Settled, general factual knowledge (not course-specific)
│   ├── people/      — One page per named person
│   ├── projects/    — Active/past projects with goals
│   ├── areas/       — Ongoing areas of responsibility
│   ├── brainstorm/  — Speculative ideas, startup concepts, creative explorations
│   └── learning/    — Course notes, book notes, exercise banks, grammar references
│       └── spanish/ — Spanish learning content
└── sources/         — Immutable raw inputs (connectors write here, agent reads)
    ├── work/
    └── personal/
```

Folder routing: agent reads `vault/FOLDERS.md` at the start of every compile run. To add a new folder, edit FOLDERS.md and create the directory — no code changes needed.

Key distinctions:
- `learning/` vs `concepts/`: course/book/practice material → `learning/`; general settled knowledge → `concepts/`
- `areas/` vs `learning/`: ongoing responsibility → `areas/`; personal learning progress → `learning/`
- `brainstorm/` only for speculative/unvalidated ideas — not exercises, notes, or assessments

## Implementation status

- ✅ Phase 1: MCP server + hybrid search + local vector store + Azure embeddings
- ✅ Phase 2: Agent SDK compilation loop (`src/agent.py`) + `brain_compile` MCP tool — tested end-to-end
- ✅ Vault restructured: `wiki/learning/` added; folder routing moved to `vault/FOLDERS.md` (extensible without code changes)
- 🔲 Phase 3: Live connectors — email, Teams (`connectors/`)
- 🔲 Phase 4: Continuous use and vault growth

## Key conventions

- Frontmatter fields: `title`, `date`, `domain` (work/personal/learning), `tags`, `status` (inbox/processed)
- Wikilinks: `[[Page Title]]` — always link to existing pages
- `vault/.vectors.json` is gitignored — rebuild with `index_vault.py` after bulk changes
- Embeddings are provider-agnostic: only `.env` changes when switching from Azure to OpenAI
- The agent uses `claude-sonnet-4-6` for compilation tasks
- `vault/CLAUDE.md` (not this file) governs wiki compilation rules and tag taxonomy
