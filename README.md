# Brain MCP Server

A personal "second brain" system exposed as an MCP (Model Context Protocol) server.
It lets an LLM client — Claude Desktop, Claude Code, or anything else that speaks
MCP — read from and write to a markdown knowledge vault, search it with hybrid
(keyword + semantic) search, clip web pages into it, and run an agentic
compilation pass that turns raw notes into a linked wiki.

This repo is the **engine**. Your actual notes (the vault content) are expected
to live in a separate directory/repo — see [Multi-vault setup](#multi-vault-setup).

## What's in here

- **MCP server** (`src/server.py`) — exposes 7 tools over stdio or Streamable
  HTTP, so any MCP-compatible client can use it.
- **Compile agent** (`src/agent.py`) — an Anthropic-API agentic loop that reads
  `inbox/` and `sources/`, writes structured wiki pages with `[[wikilinks]]`,
  and can lint the vault or answer questions with citations.
- **Hybrid search** (`src/search.py`, `src/vector_store.py`, `src/embed.py`) —
  a JSON-file vector store plus keyword search, combined for retrieval. Works
  against any OpenAI-compatible embeddings endpoint.
- **Multi-vault support** (`src/vaults.py`, `wikis.toml`) — run several
  independent vaults (e.g. work / personal / a language-learning vault) from
  one server.
- **Git sync** (`src/gitsync.py`) — best-effort pull-before-compile /
  push-after-write so a vault can live in its own git repo and stay in sync
  across machines or a cloud deployment.
- **Trigger server** (`trigger/`) — a FastAPI webhook endpoint for a WhatsApp
  (Twilio) interface into the brain.
- **Connectors** (`connectors/`) — pull external sources (e.g. email via IMAP)
  into `sources/` for the compile agent to digest.
- **Deploy config** (`Dockerfile`, `fly.toml`, `docker-entrypoint.sh`) — ready
  to run on [Fly.io](https://fly.io) as a remote MCP endpoint.

## MCP tools

| Tool | Key params | Purpose |
|------|-----------|---------|
| `brain_list_wikis` | — | List configured vaults and their domains/note types |
| `brain_search` | `query`, `scope`, `mode` (hybrid/semantic/keyword) | Search a vault |
| `brain_recall` | `topic`, `depth` (1 or 2) | Fetch a page plus its wikilinked neighbors |
| `brain_write` | `content`, `tags`, `domain`, `title?`, `source_url?` | Write a new note to the inbox (auto-embedded) |
| `brain_clip` | `url`, `domain?`, `tags?` | Fetch a URL → clean markdown, download images |
| `brain_context` | `agent_type` | Top recent pages for a persona (work/personal/research) |
| `brain_relate` | `concept_a`, `concept_b` | Shared tags + graph path between two concepts |
| `brain_compile` | `task`, `limit?`, `query?` | Run the compile agent: `compile inbox`, `compile sources`, `lint`, or `search` |

## Vault structure

Each vault is a self-contained directory:

```
<vault>/
├── CLAUDE.md        # vault-specific schema, tag taxonomy, compile rules
├── FOLDERS.md        # extensible folder registry (compile agent reads this first)
├── inbox/            # new notes land here via brain_write / brain_clip
├── wiki/             # compiled knowledge with [[wikilinks]]
│   ├── index.md
│   ├── log.md
│   ├── concepts/
│   ├── people/
│   ├── projects/
│   ├── areas/
│   ├── brainstorm/
│   └── learning/
└── sources/          # immutable raw inputs (connectors write here)
```

To add a new folder category, edit that vault's `FOLDERS.md` and create the
directory — no code changes required.

## Getting started

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- An Anthropic API key (for the compile agent)
- An OpenAI-compatible embeddings endpoint (Azure OpenAI, OpenAI, or any
  compatible provider)

### Install

```bash
uv sync
```

### Configure

Copy the example env file and fill in your own values:

```bash
cp .env.example .env
```

```ini
# Embeddings (any OpenAI-compatible endpoint)
EMBEDDING_ENDPOINT=https://<your-resource>.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-05-15
EMBEDDING_API_KEY=<your-azure-key>

# Compile agent (Claude via Azure AI Foundry, or plug in ANTHROPIC_API_KEY directly)
LLM_BASE_URL=https://ai-gateway.nexteer.app
LLM_API_KEY=<gateway-service-key>
LLM_MODEL=deepseek-v4-flash
# LLM_PROFILE=<optional gateway AI Orchestration profile, sent as X-AI-Profile>
# Legacy fallback if LLM_* unset: ANTHROPIC_FOUNDRY_BASE_URL / ANTHROPIC_FOUNDRY_API_KEY

# Multi-vault
VAULTS_ROOT=./vaults
WIKIS_CONFIG=./wikis.toml
DEFAULT_WIKI=work

# MCP HTTP server (only needed for remote/non-stdio hosting)
MCP_API_KEY=<generate-a-long-random-string>
```

**Never commit `.env`.** It's already gitignored — keep it that way.

### Multi-vault setup

Vaults are registered in `wikis.toml`:

```toml
default = "work"

[wikis.work]
# path = "/absolute/path/to/some-other-vault"   # optional override

[wikis.personal]
[wikis.spanish]
```

Each vault directory needs a `.brain/profile.toml` self-description. By
default, vaults live under `VAULTS_ROOT` (`./vaults` locally) and are **not**
part of this repo — `/vaults/` is gitignored, since the whole point is to keep
your engine (public/shareable) separate from your actual notes (private).
Point `path` at a separately cloned private repo if you want your vault
content version-controlled too.

### Run the MCP server

**stdio** (for Claude Desktop / Claude Code):

```bash
uv run python -m src.server
```

Register it by adding to `.claude/settings.json` (or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "brain": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/absolute/path/to/this/repo"
    }
  }
}
```

**Streamable HTTP** (for remote hosting):

```bash
uv run python -m src.server --transport http
```

Serves on `http://$HOST:$PORT/mcp`. If `MCP_API_KEY` is set, non-localhost
requests must send it as the `x-api-key` header.

### Rebuild the vector index

After bulk edits to a vault (or before first use):

```bash
uv run python scripts/index_vault.py
```

### Run the WhatsApp trigger server (optional)

```bash
uv run python -m trigger.app
```

Routes inbound WhatsApp messages (via Twilio) to `brain_write`, the compile
agent, or `brain_search` based on simple intent parsing.

## Deploying (Fly.io)

The included `Dockerfile` / `fly.toml` / `docker-entrypoint.sh` run the server
over Streamable HTTP with `auto_stop_machines` for scale-to-zero. The
entrypoint clones/pulls a **vaults repo** from GitHub on boot (via
`VAULTS_REPO` + `GITHUB_TOKEN` secrets) onto a persistent volume, so vault
content stays in sync between your local machine and the deployed instance.

```bash
fly deploy
fly secrets set MCP_API_KEY=... GITHUB_TOKEN=... VAULTS_REPO=github.com/you/your-vaults.git
```

## Notes on what's public here

This repository is the **engine only**:

- No vault content (`vaults/`), vectors (`.vectors.json`), or `.env` secrets
  are tracked — see `.gitignore`.
- `.env.example` documents the required variables without real values.
- If you fork this to run your own brain, your personal notes should live in
  a separate private repo, referenced via `wikis.toml` `path` overrides or
  mounted at `VAULTS_ROOT`.

## License

No license file is currently included — all rights reserved by default. Add a
`LICENSE` file if you want to permit reuse.
