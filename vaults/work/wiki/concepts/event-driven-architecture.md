---
title: "Event-Driven Architecture"
date: 2026-04-19
domain: concepts
tags: [nexteer, enterprise-architecture, agents]
status: active
---

# Event-Driven Architecture

Event-Driven Architecture (EDA) is a software design pattern in which system components communicate by producing and consuming discrete events rather than by direct calls. It enables loose coupling, real-time responsiveness, and scalable data flows — particularly valuable for shop-floor-to-cloud integration in manufacturing contexts.

## Key Points
- Core competency of **Pod 1 — Event & Integration** within [[IT 2.0 Modern Technical Architecture]]
- Primary broker technology: **Apache Kafka** — distributed event streaming at enterprise scale
- **API layer:** Kong API Gateway provides secure, governed access to NVS and enterprise systems alongside the event bus
- **Standard reference architecture:** Kafka event pipeline — reusable across manufacturing, GSM, and data lake ingestion
- Shop floor to cloud data flows are a primary manufacturing use case at Nexteer

## Key Components
- **Apache Kafka** — distributed event log and streaming backbone
- **Real-time streaming pipelines** — low-latency data movement between systems
- **Kong API Gateway** — API-first access layer, complements the event bus
- **Event-driven design patterns** — choreography, sagas, event sourcing

## Capability Levels (IT 2.0 Definition)
- **Kafka Architect** — Designs, deploys & operates Kafka-based event infrastructure at enterprise scale
- **Event-Driven Systems Engineer** — Architects and operates API-first, event-driven systems with Kong gateway

## Related Concepts
- [[Capability Pods]] — Pod 1 is the organizational home for this capability
- [[Enterprise RAG on Azure]] — Pod 1 data flows supply structured data to the RAG data layer

## People
- [[Ravi Ganda]] — INTC sourcing lead for Kafka specialists filling Pod 1

## Sources
- [[IT 2.0 Modern Technical Architecture — Capability Pods]]
