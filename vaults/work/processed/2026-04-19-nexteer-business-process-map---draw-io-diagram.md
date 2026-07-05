---
date: '2026-04-19'
domain: work
status: processed
tags:
- nexteer
- business-process-map
- drawio
- architecture
- BPM
- MOP
- COP
- SOP
- diagram
title: Nexteer Business Process Map – draw.io Diagram
---

# Nexteer Business Process Map – draw.io Diagram

Created a full draw.io (.drawio) diagram recreating the Nexteer Business Process Map from the official source image.

## Structure

### MOP Lane (Management-Oriented Process) – Blue
- **Global Strategic Business Planning** (GSC + GOC)
- **Sales Customer Focus**: Strategy Development → Prospect Alignment → Strategy Alignment → Quote → Business Award → Perform & Service
- **Innovation**: 1. Concept Evaluation → 2. Make It Work → 3. Make It Good
- **Product Line Architecture & Pursuit**: Define Architecture → Initiate Pursuit → ECR → Business Case → Comm & Tech Review → Charter Program
  - Sub-rows: GSM PLPM Collaboration with PL Strategy, VEM/GCM/SDE, Pursuit Cost Management

### COP Lane (Customer-Oriented Process) – Green
- **Customer Program Implementation** (6 phases):
  1. Develop Product/Process Analysis/Test Plan
  2. Develop Production Intent Product/Process Design
  3. Validate Product Design for Production
  4. Implement MFG. System
  5. Validate MFG. System
  6. Production
- **Software & Calibration Delivery to OEM**
- Sub-rows: Pur. Launch Mgmt., Direct Purchasing, VEM/GCM/SDE, Indirect Purchasing, Supplier APQP, Supplier Performance Improvement
- **Product Delivery/Service Parts**:
  - PC&L – Production Control
  - PC&L – Transportation Management
  - PC&L – Supplier Logistics Management
  - Manufacturing / Remanufacturing [D-NA]
  - PC&L – Customer Logistics Management
  - Direct/Indirect Purchasing, Supplier Performance/Commercial Improvement

### SOP Global Lane (Amber)
Functions: GSM, PE, ME, HR, PC&L, H&S, IT, ENV, Legal, Quality, Finance, Overall

### SOP Divisional Lane
EMS [D] | Maintenance [D] | Contingency [D]

## File
- Output: `Nexteer_Business_Process_Map.drawio`
- Format: mxGraph XML, fully editable in draw.io / diagrams.net
- Built using: mxGraph XML authored directly (not CLI), 1700×1100px canvas
- Branding: Nexteer red (#DE0202) title bar, blue MOP lane, green COP lane, amber SOP lane

## Legend
- [GSM] – Global Supply Management Processes
- [D] – Divisional Processes
- [D-NA] – U.S. & Mexico Divisions