---
title: "Idea: SBRF (Semantic Business Record Format)"
date: 2026-04-19
domain: work
tags: [sbrf, integration-architecture, enterprise-architecture, ai, nexteer, innovation, startup-idea, concept-draft]
status: active
---

# Idea: SBRF (Semantic Business Record Format)

An original integration architecture concept developed by [[Kris Mekwinski]] at Nexteer Automotive. SBRF proposes replacing brittle hardcoded system adapters with self-describing, AI-interpreted messages — a semantic layer for enterprise integration. Presented to the EA/AI team as an R&D concept worth exploring.

## The Core Concept
Self-describing **Markdown + JSON messages** that AI-powered consumers interpret dynamically, eliminating the need for hardcoded adapters between systems. The message carries its own schema and semantic context; the consumer-side AI model determines intent and structure at runtime.

## Key Principles
- Messages carry their own schema and semantic context (self-describing)
- AI model on the consumer side interprets intent and structure dynamically
- No brittle point-to-point adapter contracts
- Aligns with event-driven / loosely-coupled enterprise architecture principles

## Why It Matters
- Traditional EAI (Enterprise Application Integration) requires hardcoded mappings per integration pair — maintenance scales quadratically
- SBRF replaces that with a semantic layer: the consumer figures out what to do with the record
- Reduces integration maintenance overhead at scale
- Enables heterogeneous system interoperability across Nexteer's global manufacturing footprint (North America, Europe, India, China, Morocco, Brazil)

## Open Questions / Exploration Areas
- How does semantic interpretation handle ambiguity or conflicting schemas?
- What are the failure modes when the AI consumer misinterprets a record?
- Could this evolve into a broader open standard (beyond Nexteer)?
- Relationship to existing semantic web / linked data standards (RDF, JSON-LD)?

## Status
- R&D / exploratory concept as of early 2026
- Presented internally to Kris's EA team at Nexteer

## Related Concepts
- [[Nexteer AI Strategy]] — SBRF lives under the Frontier AI R&D pillar
- [[Kris Mekwinski]] — concept originator
- [[Coolify Infrastructure at Nexteer]] — potential deployment environment for SBRF prototypes

## Sources
- [[SBRF - Semantic Business Record Format]]
