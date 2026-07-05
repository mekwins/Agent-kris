# Worked example — a real compile run

This is an **actual, executed** trace (not a mock-up), captured on 2026-07-05, showing
how one sentence becomes structured, cross-linked wiki pages. It pairs with
`diagrams/example-flow.drawio`.

The scenario deliberately mixes a **new** person (Kristina — unknown to the vault)
and an **existing** person (Ravi Ganda — already had a page from an earlier
compile) to demonstrate resolve-or-create-then-link.

---

## ① The input (captured to the `work` vault)

Written via `brain_write(wiki="work", domain="tasks", title="Send EA onboarding pack to Kristina")`:

```
Task from Kris: send the enterprise architecture onboarding pack to Kristina by next Friday.
Also follow up with Ravi Ganda about the Kafka sourcing for Pod 1 — he owes an update.
```

Result:

```json
{ "wiki": "work",
  "path": "inbox/2026-07-05-send-ea-onboarding-pack-to-kristina.md",
  "committed": true, "chunks_indexed": 1 }
```

## ② The compile run

`brain_compile(wiki="work", task="compile inbox")` — the agent's own summary:

```
Source: 1 inbox file → send-ea-onboarding-pack-to-kristina.md
The note contained two tasks and three named people. Everything was cross-linked.

Pages created (4)
  [[Send EA Onboarding Pack to Kristina]]      Task   assignee: Kris Mekwinski, due: 2026-07-11
  [[Follow Up with Ravi Ganda on Kafka Pod 1]] Task   assignee: Ravi Ganda
  [[Kristina]]                                 Person stub — no surname known
  [[Kris Mekwinski]]                           Person — referenced but had no page in this vault

Pages updated (2)
  [[Ravi Ganda]]  — added "## Assigned Tasks" back-link (existing page reused, NOT duplicated)
  [[Wiki Index]]  — added Tasks section

Vault 'work' changes committed to git.
```

## ③ What actually landed on disk

### `work/wiki/tasks/send-ea-onboarding-pack-to-kristina.md`

```markdown
---
title: "Send EA Onboarding Pack to Kristina"
date: 2026-07-05
domain: tasks
status: open
assignee: "Kris Mekwinski"
due: 2026-07-11
related: [IT 2.0 Modern Technical Architecture, Nexteer AI Strategy]
tags: [nexteer, enterprise-architecture, task]
---

# Send EA Onboarding Pack to Kristina

Send the enterprise architecture onboarding pack to [[Kristina]]. Task requested
by [[Kris Mekwinski]] with a deadline of next Friday (2026-07-11).
...
## Related
- [[IT 2.0 Modern Technical Architecture]] — the EA initiative Kristina is being onboarded to
```

### `work/wiki/people/kristina.md` (newly created stub — no invented facts)

```markdown
---
title: "Kristina"
role: Unknown — referenced as EA onboarding recipient
---

# Kristina

Referenced as the recipient of the enterprise architecture onboarding pack. No
additional details known — page created as a stub from a task note.

## Assigned Tasks
- [[Send EA Onboarding Pack to Kristina]]
```

### `work/wiki/people/ravi-ganda.md` (existing page — only appended to)

The original page (dated `2026-04-19`) was left intact; the agent added:

```markdown
## Assigned Tasks
- [[Follow Up with Ravi Ganda on Kafka Pod 1]] — owes a sourcing update on Kafka / Pod 1
```

## ④ Why this matters

- **Entity resolution:** unknown people become stubs; known people are reused —
  the graph never grows duplicate person pages.
- **Bidirectional links:** task → person *and* person → task, so `brain_recall`
  and Obsidian's backlinks panel both surface the relationship.
- **Structure from prose:** a free-text sentence produced typed frontmatter
  (`status`, `assignee`, `due`) driven purely by the vault's `.brain/` profile —
  no code change was needed to add the `task` type.
