This vault is **project- and people-centric**. Its job is to give you fast, rich
context for work tasks: what a project is about, who is involved, and which
concepts/decisions matter.

## Priorities when compiling
1. **Projects are first-class.** Any note about work almost always belongs to a
   project. Create/maintain a page in `wiki/projects/` and link the note to it.
2. **Extract people aggressively.** Whenever a named person appears, ensure they
   have a page in `wiki/people/` and add a `[[wikilink]]` from the project and
   from their page back to the project(s) they touch.
3. **Concepts stay reusable.** Domain-agnostic knowledge (MCP, agents,
   architecture patterns, governance) goes to `wiki/concepts/` and is linked
   from the projects/areas that use it — never buried inside a project page.
4. **Areas vs projects:** an ongoing responsibility with no fixed end (e.g.
   "Nexteer AI Strategy") is an `area`; something with a defined goal/outcome is
   a `project`.

## Tag taxonomy
`nexteer` `enterprise-architecture` `ai-strategy` `vibe-coding` `governance`
`agents` `mcp` `coolify` `claude-enterprise`

## Frontmatter
Use `domain:` to record the note type where useful: `projects`, `people`,
`concepts`, `areas`, or `brainstorm`. Always include `title`, `tags`, `status`.

When answering task-context questions, prefer pulling the relevant project page
plus its linked people and concepts.
