# Vault Folder Registry

The compile agent reads this file at the start of every compile run to determine routing rules.
**To add a new wiki folder**: add a row to the table below and create the folder. No code changes needed.

## Available Folders

| Folder | Purpose | Route content here when... |
|--------|---------|---------------------------|
| `wiki/concepts/` | General, domain-agnostic settled knowledge | Factual or definitional — concepts any reader would want (MCP, Agents, AI concepts, etc.) |
| `wiki/people/` | One page per named person | Content is about a specific named individual |
| `wiki/projects/` | Active or past projects with clear goals and status | A project with defined scope, team, and outcome |
| `wiki/areas/` | Ongoing areas of responsibility | A recurring domain of life or work (e.g. Nexteer AI Strategy, family) |
| `wiki/brainstorm/` | Speculative ideas only — prefix title with "Idea: " | Unvalidated ideas, startup concepts, creative explorations, innovation sessions |
| `wiki/learning/` | Structured learning content | Course material, book notes, exercise banks, grammar references, research papers, podcast notes |

## Subfolder conventions

- `wiki/learning/<subject>/` — group learning content by subject
  - Examples: `learning/spanish/`, `learning/books/`, `learning/courses/`, `learning/ai-research/`
- `wiki/projects/<domain>/` — optional grouping if many projects exist

## Key distinctions

| Question | Answer |
|----------|--------|
| `concepts/` vs `learning/`? | Is this general knowledge anyone would want (→ concepts/) or material tied to a specific course, book, or practice session (→ learning/)? |
| `areas/` vs `learning/`? | Is this an ongoing responsibility or domain of life (→ areas/) or personal learning progress (→ learning/)? |
| `people/` vs `learning/`? | Personal learning profiles, assessments, and progress logs → `learning/<subject>/`, not `people/` |
| `brainstorm/` threshold? | Only for speculative/creative/unvalidated ideas. Exercises, notes, references, and assessments are NEVER brainstorm. |

## Examples

| Content type | Correct folder |
|-------------|---------------|
| Spanish grammar reference from a course | `wiki/learning/spanish/` |
| Spanish exercise bank | `wiki/learning/spanish/` |
| My Spanish progress + error patterns | `wiki/learning/spanish/` |
| Book notes: "The Innovator's Dilemma" | `wiki/learning/books/` |
| Podcast notes: Lex Fridman ep | `wiki/learning/` or `wiki/learning/ai-research/` |
| What is MCP? (factual definition) | `wiki/concepts/` |
| Nexteer AI Strategy | `wiki/areas/` |
| Coolify infrastructure project | `wiki/projects/` |
| Startup idea: AI-powered supply chain agent | `wiki/brainstorm/` (title: "Idea: ...") |
| Named person: Andy Wilson | `wiki/people/` |
