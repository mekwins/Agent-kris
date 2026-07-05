---
title: "MCP"
date: 2026-04-19
domain: concepts
tags: [nexteer, mcp, agents, ai-strategy, enterprise-architecture]
status: active
---

# MCP (Model Context Protocol)

MCP (Model Context Protocol) is an open protocol that allows AI agents and language models to connect to external data sources and tools through a standardized server interface. MCP servers expose enterprise systems, databases, and APIs to AI workloads in a governed, reusable way — eliminating the need to build bespoke integrations for every agent.

## Key Points
- Used in **Pod 2 — AI & Agents** within [[IT 2.0 Modern Technical Architecture]] for Neo4j graph DB connectivity
- Enables enterprise data source connectivity (structured + unstructured) for AI agent workflows
- One of the core capabilities of the **Enterprise Agent Architect** capability level at Nexteer
- Fits into the [[Enterprise RAG on Azure]] reference architecture as the integration layer between agents and knowledge stores

## At Nexteer (IT 2.0)
- **Neo4j MCP server** — exposes the graph database to AI agents as a context source
- Part of the Pod 2 standard toolchain alongside Semantic Kernel, Azure AI SDKs, and vector databases
- Enables the "Enterprise Agent Architect" capability: builds & operates agents with RAG, vector stores & MCP servers

## Related Concepts
- [[Enterprise RAG on Azure]] — MCP servers are part of the RAG pipeline's integration layer
- [[Capability Pods]] — Pod 2 (AI & Agents) is the organizational home for MCP work
- [[Event-Driven Architecture]] — event streams and MCP servers together form the enterprise data connectivity layer

## People
- [[Shin Dong-hyun]] — Pod 2 lead; directly works with MCP server integration

## Sources
- [[IT 2.0 Modern Technical Architecture — Capability Pods]]
