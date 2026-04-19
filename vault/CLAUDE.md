# Brain Schema

This file governs how Claude Code reads, compiles, and maintains the vault.

## Inbox frontmatter template

```yaml
---
title: ""
date: YYYY-MM-DD
domain: work | personal | learning
tags: []
source_url: ""
status: inbox
---
```

## Tag taxonomy

### Work tags
`nexteer` `enterprise-architecture` `ai-strategy` `vibe-coding`
`governance` `agents` `mcp` `coolify` `claude-enterprise`

### Personal tags
`health` `language-learning` `polish` `spanish` `travel` `pixel` `birdy`

### Learning tags
`book` `podcast` `article` `course` `ai-research` `engineering` `programming`

### Brainstorm tags
`startup-idea` `innovation` `brainstorm` `creative` `experiment` `concept-draft`

## Wiki page rules

- Every page must have: `title`, `domain`, `tags`, a 2-3 sentence summary, and `wikilinks`
- Wikilinks use `[[Page Title]]` syntax — always link to existing pages
- Never delete content — mark outdated content with tag `archived`
- One concept per page — split pages that cover multiple unrelated concepts
- People pages: one page per named person, link to their ideas and quotes

## Domain routing

- Nexteer / EA / AI CoE / IT → `domain: work`
- Health / family / hobbies / Pixel / Birdy → `domain: personal`
- Books / courses / research / general AI → `domain: learning`
- Brainstorm content inherits the domain closest to the idea (work startup → work, personal project → personal, research-adjacent → learning)

## Wiki folder routing

Folder routing rules live in `vault/FOLDERS.md` — read that file at the start of every compile run. It is the single source of truth. New folders can be added there without code changes.

Default folders:

| Folder | What goes here |
|--------|---------------|
| `wiki/concepts/` | Factual, settled knowledge — definitions, how things work, established patterns |
| `wiki/people/` | Named individuals — their ideas, quotes, background |
| `wiki/projects/` | Active or completed projects with goals and status |
| `wiki/areas/` | Ongoing areas of responsibility |
| `wiki/brainstorm/` | Speculative ideas, creative explorations, startup concepts (prefix title "Idea: ") |
| `wiki/learning/` | Structured learning: course notes, book notes, exercise banks, grammar references — use subfolders by subject (e.g. `learning/spanish/`, `learning/books/`) |

Key distinction: `learning/` is for course/book/practice material; `concepts/` is for general settled knowledge any reader would want.

## Brainstorm page format

```yaml
---
title: "Idea: Short Name"
date: YYYY-MM-DD
domain: work | personal | learning
tags: [brainstorm, startup-idea]   ← always include brainstorm tag
status: active | parked | archived
---
```

Brainstorm pages should include:
- **The spark**: what triggered this idea
- **Core concept**: what it is in 2-3 sentences
- **Open questions**: unresolved things to explore
- **Related Concepts**: `[[wikilinks]]` to relevant knowledge pages
- Prefix title with `"Idea: "` to distinguish from settled concepts

## Compile instructions

When processing `inbox/`:
1. Classify domain from content and tags
2. Detect content type:
   - Factual / reference knowledge → `wiki/concepts/`
   - Named person → `wiki/people/`
   - Project with goals/deliverables → `wiki/projects/`
   - Ongoing area of responsibility → `wiki/areas/`
   - Speculative, creative, startup idea, brainstorm session → `wiki/brainstorm/`
3. Add wikilinks between related pages across any folder
4. Call `mark_processed` on the inbox file — this moves it from `inbox/` to `processed/` and sets status: processed. The inbox must be empty after a full compile run.
5. Commit with message: `brain: compile [n] inbox items`

## Vault directory roles

| Directory | Purpose |
|-----------|---------|
| `inbox/`  | Uncompiled captures — only files with status: inbox live here |
| `processed/` | Archive of compiled raw notes — moved here by mark_processed |
| `wiki/`   | Compiled, interlinked knowledge base |
| `sources/` | Immutable raw imports (connectors write here) |
