---
title: "IT 2.0 Modern Technical Architecture"
date: 2026-04-19
domain: areas
tags: [nexteer, enterprise-architecture, ai-strategy, agents, mcp]
status: active
---

# IT 2.0 Modern Technical Architecture

IT 2.0 is a Center of Excellence for modern enterprise technology at Nexteer — combining domain knowledge, AI-native development, event-driven infrastructure, and modern data platforms to accelerate innovation across the business. It is an ongoing area of responsibility (no fixed end date) organized around reusable capability pods.

## Key Points
- Organized into three focused **Capability Pods**: Event & Integration, AI & Agents, Modern Data & APIs
- Every project is capability-first: real business problems are selected because they exercise and validate a specific pod's pattern
- Each project produces a **reusable reference architecture** (Blessed Patterns Library)
- Cross-pod technical coordination led by [[Shin Dong-hyun]]
- INTC sourcing of Kafka specialists managed by [[Ravi Ganda]]
- Manufacturing domain experts provided by [[Grzegorz Bobyla]]'s team

## Capability Pods

### Pod 1 — Event & Integration
**People:** [[Ravi Ganda]]'s INTC team sourcing Kafka specialists

**Capabilities:**
- Kafka-based event infrastructure — design, deploy, operate
- Event-driven architecture design patterns
- Real-time streaming pipelines
- Shop floor to cloud data flows
- Kong API Gateway — secure access layers to NVS and enterprise systems
- API-first architecture standards

**Reference Architecture:** Standard Kafka event pipeline — reusable across manufacturing, GSM, and data lake ingestion

---

### Pod 2 — AI & Agents
**People:** [[Shin Dong-hyun]] as technical lead

**Capabilities:**
- Semantic Kernel & Azure AI SDKs
- RAG architectures & vector databases
- Enterprise agent design and operation
- Azure Document Intelligence
- Neo4j graph DB & [[MCP]] server integration
- Enterprise data source connectivity (structured + unstructured)

**Reference Architecture:** Standard enterprise RAG on Azure — reusable across Finance, Legal, Engineering AI use cases

---

### Pod 3 — Modern Data & APIs
**People:** [[Xindong Yang]] — Data Lake & Azure platform ownership

**Capabilities:**
- Azure Data Lake & modern data integration patterns
- Structured & unstructured data access
- Vector store design & management
- Kong API Gateway — API-first access layer
- Supports both traditional applications and AI workloads

**Reference Architecture:** Standard data access layer — all domains query through governed, secure APIs instead of direct DB access

## Capability-First Operating Model

Projects are selected because they exercise specific pod capabilities; the business problem is real but the deeper goal is building and validating the pattern.

### Blessed Patterns Library
- Standard Kafka event pipeline
- Standard RAG on Azure
- Standard enterprise agent architecture
- Standard Kong API gateway pattern

Domain teams adopt these instead of reinventing.

### Internal Capability Levels (hands-on evaluation, not just training)
1. **Kafka Architect** — Designs, deploys & operates Kafka-based event infrastructure at enterprise scale
2. **Enterprise Agent Architect** — Builds & operates agents in Microsoft ecosystem with RAG, vector stores & MCP servers
3. **AI Integration Engineer** — Connects enterprise data sources to AI workloads via modern APIs, graph DBs & document AI
4. **Event-Driven Systems Engineer** — Architects and operates API-first, event-driven systems supporting Kong gateway & integration layer

## Key Decisions
- Team should continuously develop capabilities through real use cases — not support projects in the traditional IT sense
- Goal: top-tier specialists who design modern architectures, experiment with emerging technologies, and elevate overall technical maturity
- [[Ravi Ganda]] plays key role identifying individuals who can own Kafka-based solutions

## Related Concepts
- [[MCP]] — used in Pod 2 (AI & Agents) for Neo4j MCP server integration
- [[Enterprise RAG on Azure]] — Pod 2's reference architecture
- [[Capability Pods]] — the organizational model structuring this area
- [[Event-Driven Architecture]] — core competency of Pod 1

## People
- [[Shin Dong-hyun]] — Technical lead, cross-pod coordinator; Pod 2 lead
- [[Ravi Ganda]] — INTC sourcing lead for Kafka specialists (Pod 1)
- [[Xindong Yang]] — Pod 3 owner, Azure Data Lake & platform
- [[Grzegorz Bobyla]] — Manufacturing domain expert contribution

## Sources
- [[IT 2.0 Modern Technical Architecture — Capability Pods]]
