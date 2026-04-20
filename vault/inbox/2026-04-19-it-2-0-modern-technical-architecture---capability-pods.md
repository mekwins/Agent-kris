---
date: '2026-04-19'
domain: work
status: inbox
tags:
- nexteer
- enterprise-architecture
- ai-strategy
- agents
- mcp
title: IT 2.0 Modern Technical Architecture — Capability Pods
---

# IT 2.0 Modern Technical Architecture — Capability Pods

## Vision
IT 2.0 is a Center of Excellence for modern enterprise technology — combining domain knowledge, AI-native development, event-driven infrastructure, and modern data platforms to accelerate innovation across the business.

## Structure
The Modern Technical Architecture pillar is organized into three focused capability pods. **Technical lead coordinating across pods: Shin Dong-hyun.**

---

## Pod 1 — Event & Integration
**People**: Ravi Ganda's INTC team sourcing Kafka specialists

**Core capabilities:**
- Kafka-based event infrastructure — design, deploy, operate
- Event-driven architecture design patterns
- Real-time streaming pipelines
- Shop floor to cloud data flows
- Kong API Gateway — secure access layers to NVS and enterprise systems
- API-first architecture standards

**Reference Architecture**: Standard Kafka event pipeline pattern — reusable across manufacturing, GSM, and data lake ingestion

---

## Pod 2 — AI & Agents
**People**: Shin Dong-hyun as technical lead

**Core capabilities:**
- Semantic Kernel & Azure AI SDKs
- RAG architectures & vector databases
- Enterprise agent design and operation (not just experimentation)
- Azure Document Intelligence
- Neo4j graph DB & MCP server integration
- Enterprise data source connectivity (structured + unstructured)

**Reference Architecture**: Standard enterprise RAG on Azure — reusable across Finance, Legal, Engineering AI use cases

---

## Pod 3 — Modern Data & APIs
**People**: Xindong Yang — Data Lake & Azure platform ownership

**Core capabilities:**
- Azure Data Lake & modern data integration patterns
- Structured & unstructured data access
- Vector store design & management
- Kong API Gateway — API-first access layer
- Supports both traditional applications and AI workloads

**Reference Architecture**: Standard data access layer — all domains query through governed, secure APIs instead of direct DB access

---

## Capability-First Operating Model

### How we work
- **Capability-First Projects**: Projects are selected because they exercise specific pod capabilities (Kafka pipeline, RAG system, agent workflow). Business problem is real but deeper goal is building and validating the pattern. Every project produces a reusable reference architecture.
- **Blessed Patterns Library**: Standard Kafka event pipeline · Standard RAG on Azure · Standard enterprise agent architecture · Standard Kong API gateway pattern. Domain teams adopt these instead of reinventing.
- **Cross-functional composition**: Manufacturing domain experts (Grzegorz Bobyla's team) + IT specialists supporting manufacturing + INTC engineers (Ravi Ganda) sourced for specific depth + Shin as cross-pod coordinator.

### Internal Capability Levels (hands-on evaluation, not just training)
1. **Kafka Architect** — Designs, deploys & operates Kafka-based event infrastructure at enterprise scale
2. **Enterprise Agent Architect** — Builds & operates agents in Microsoft ecosystem with RAG, vector stores & MCP servers
3. **AI Integration Engineer** — Connects enterprise data sources to AI workloads via modern APIs, graph DBs & document AI
4. **Event-Driven Systems Engineer** — Architects and operates API-first, event-driven systems supporting Kong gateway & integration layer

---

## Related decisions
- Ravi Ganda (INTC India) plays key role identifying individuals who can own Kafka-based solutions
- Team should continuously develop capabilities through real use cases — not support projects in the traditional IT sense
- Goal: top-tier specialists who design modern architectures, experiment with emerging technologies, and elevate overall technical maturity