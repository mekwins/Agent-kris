---
title: "Enterprise RAG on Azure"
date: 2026-04-19
domain: concepts
tags: [nexteer, ai-strategy, agents, enterprise-architecture]
status: active
---

# Enterprise RAG on Azure

Retrieval-Augmented Generation (RAG) is an AI architecture pattern that grounds a language model's responses in retrieved documents or data, reducing hallucination and enabling access to proprietary enterprise knowledge. The Nexteer IT 2.0 standard is a production-grade RAG reference architecture built on Azure services.

## Key Points
- **Standard reference architecture** produced by Pod 2 (AI & Agents) within [[IT 2.0 Modern Technical Architecture]]
- Designed to be reusable across Finance, Legal, and Engineering AI use cases
- Key Azure components: Azure AI SDKs, Semantic Kernel, Azure Document Intelligence, vector databases
- Paired with Neo4j graph DB and [[MCP]] server integration for richer knowledge retrieval
- Data layer supplied by Pod 3 ([[Xindong Yang]]): Azure Data Lake, structured & unstructured data, vector stores

## Key Components
- **Semantic Kernel** — orchestration framework for agent/RAG workflows
- **Azure Document Intelligence** — extracts structured data from unstructured documents
- **Vector Databases** — semantic similarity search over enterprise content
- **Neo4j Graph DB** — graph-based knowledge representation
- **MCP Servers** — expose enterprise data sources to AI agents (see [[MCP]])

## Related Concepts
- [[MCP]] — used for enterprise data source connectivity in the RAG pipeline
- [[Capability Pods]] — Pod 2 owns and evolves this reference architecture
- [[Event-Driven Architecture]] — Pod 1's data flows feed structured data into the RAG data layer

## People
- [[Shin Dong-hyun]] — Pod 2 lead, owns this reference architecture
- [[Xindong Yang]] — Pod 3 provides underlying data and vector infrastructure

## Sources
- [[IT 2.0 Modern Technical Architecture — Capability Pods]]
