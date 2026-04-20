Personal AI second brain integration via the brain MCP server. Use this skill IMMEDIATELY and AUTOMATICALLY whenever the user types /brain or anything resembling it — including "/brain", "/ brain", "/Brain", "brain/" or just the word "brain" as a standalone command. Also triggers on phrases like "save to my brain", "search my brain", "recall from brain", "brain context", "compile my inbox", "what do I know about X", "prime my session", "capture this to brain", "brainstorm save", "save this note", or any request to read/write/search the vault. Do NOT wait for clarification — execute immediately.

# Brain Skill — Personal AI Second Brain

## What this skill does

Integrates Claude with the brain MCP server (localhost:8765) — a personal markdown vault with hybrid semantic+keyword search, a compile agent, and wikilinked knowledge pages.

The 6 MCP tools available (Claude calls them automatically — user never calls them directly):

| Tool | Purpose | Key params |
|------|---------|-----------|
| `brain_search` | Hybrid search across wiki + sources | `query`, `scope`: all\|work\|personal\|learning, `mode`: hybrid\|semantic\|keyword |
| `brain_recall` | Fetch a wiki page + wikilinked neighbors | `topic`, `depth`: 1\|2 |
| `brain_write` | Capture content to inbox/ | `content`, `tags`, `domain`: work\|personal\|learning, `title` |
| `brain_clip` | Clip a web URL to inbox/ (fetches page + downloads images) | `url`, `domain`, `tags` |
| `brain_compile` | Run the compile agent (inbox → wiki) | `task`: compile inbox\|lint\|search, `limit`, `query` |
| `brain_context` | Load recent pages for session priming | `agent_type`: work\|personal\|research |
| `brain_relate` | Find connection between two concepts | `concept_a`, `concept_b` |

---

## /brain slash command — decision logic

When user types /brain (with or without arguments), follow this decision tree:

```
/brain                    → RETRIEVE: call brain_context(agent_type="work") to prime session
/brain save [content]     → WRITE: call brain_write with the content
/brain search [query]     → SEARCH: call brain_search with the query
/brain recall [topic]     → RECALL: call brain_recall with the topic
/brain compile            → COMPILE: call brain_compile(task="compile inbox")
/brain lint               → LINT: call brain_compile(task="lint")
/brain relate [a] [b]     → RELATE: call brain_relate(concept_a, concept_b)
/brain [anything else]    → INFER intent from the content and pick the right tool
```

No arguments = prime the session. Load work context and summarize what's in the brain relevant to the current conversation.

---

## Behavioral rules

### On /brain with no args — Session Prime
1. Call `brain_context(agent_type="work")`
2. Summarize the top pages surfaced — what's active, what's relevant to the current conversation
3. Offer to search for anything specific

### On /brain clip [url] or "clip this article" / "save this URL"
1. Call `brain_clip(url=..., domain=..., tags=[...])`
2. Infer domain and tags from the URL and any context the user gave
3. Confirm: "Clipped '[title]' to inbox · [N] words · [N] images downloaded"
4. Offer: "Run /brain compile to process it into the wiki"

### On /brain save ... or "save to my brain"
1. Extract: title, content body, domain, tags from context
2. Infer domain using routing rules below
3. Call `brain_write` with these **separate parameters** — do NOT embed frontmatter in content:
   - `content`: plain markdown body text only (no YAML, no frontmatter — the tool adds it automatically)
   - `title`: page title as a string
   - `domain`: "work" | "personal" | "learning"
   - `tags`: list of strings from the taxonomy below
   - `source_url`: optional, if content came from a URL
4. Confirm: "Saved to inbox as [title] · tags: [tags] · domain: [domain]"
5. Optionally offer: "Run /brain compile to process it into the wiki"

### On /brain search ... or "what do I know about..."
1. Call `brain_search(query=..., mode="hybrid")`
2. Synthesize results into a concise answer — don't dump raw output
3. Cite the wiki pages that surfaced the answer
4. If nothing found: say so clearly, offer to save the topic

### On /brain recall [topic]
1. Call `brain_recall(topic=..., depth=1)`
2. Present the page content + linked neighbors
3. Offer to go deeper: depth=2 or brain_relate to another concept

### On /brain compile
1. Call `brain_compile(task="compile inbox")`
2. Report what was processed: how many files, what pages were created
3. If compile fails or returns empty: suggest checking inbox, offer lint

### On "search my brain: [question]" — Synthesis mode
Use `brain_compile(task="search", query=...)` for agent-synthesized answers, not raw search results. This is the power mode — full cited synthesis from the vault.

---

## Domain routing (for brain_write)

| Content about | domain |
|--------------|--------|
| Nexteer, EA, AI CoE, IT, vibe coding, Coolify, Claude Enterprise, governance | work |
| Health, family, hobbies, Pixel, Birdy, travel, Polish/Spanish learning | personal |
| Books, courses, research, AI papers, engineering learning | learning |

## Tag taxonomy — pick from these:

- **Work**: nexteer, enterprise-architecture, ai-strategy, vibe-coding, governance, agents, mcp, coolify, claude-enterprise
- **Personal**: health, language-learning, polish, spanish, travel, pixel, birdy
- **Learning**: book, podcast, article, course, ai-research, engineering, programming
- **Brainstorm**: startup-idea, innovation, brainstorm, creative, experiment, concept-draft

---

## Vault structure reference

```
vault/
├── inbox/          ← brain_write lands here (uncompiled)
├── processed/      ← moved here after compile
├── wiki/
│   ├── concepts/   ← settled factual knowledge
│   ├── people/     ← one page per person
│   ├── projects/   ← active/past projects
│   ├── areas/      ← ongoing responsibilities
│   └── brainstorm/ ← speculative ideas (prefix: "Idea: ")
└── sources/        ← raw imports
```

---

## Example interactions

```
/brain
→ Loads work context, summarizes active projects and recent pages

/brain save
The SBRF concept uses self-describing Markdown+JSON messages with AI-powered consumer interpretation.
→ Calls brain_write(content="The SBRF concept...", title="SBRF", domain="work", tags=["enterprise-architecture", "ai-strategy", "mcp"])

/brain search vibe coding governance
→ Searches wiki, returns synthesized answer with page citations

/brain recall SBRF
→ Fetches the SBRF wiki page + linked neighbors

/brain compile
→ Runs compile agent on inbox → wiki pages

/brain relate vibe-coding governance
→ Shows shared tags and wikilink path between the two concepts

/brain lint
→ Checks for broken wikilinks and bad frontmatter

search my brain: what do I know about AI governance?
→ Calls brain_compile(task="search", query="AI governance") for full cited synthesis
```

---

## Troubleshooting

If brain tools are unavailable or calls fail:

1. MCP server may be down: `curl -o /dev/null -w "%{http_code}" http://127.0.0.1:8765/sse --max-time 2` → expect 200
2. Restart: `launchctl stop com.kris.brain-mcp && launchctl start com.kris.brain-mcp`
3. Logs: `tail -f ~/Library/Logs/brain-mcp.log`
4. Rebuild vector index: `uv run python scripts/index_vault.py`

Tell the user the server appears to be down and provide the restart command. Do not retry indefinitely.
