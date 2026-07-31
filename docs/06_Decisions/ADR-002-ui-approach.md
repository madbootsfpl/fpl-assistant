# Architectural Decision Record: UI Approach

**Decision ID:** ADR-002
**Date:** 2026-07-31
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The Charter names FastAPI and lists React as an optional future item; the Roadmap
adds Streamlit/Dash as "acceptable only for rapid prototyping" and React/Next.js as
"preferred long-term." Sprint 001 only needs to *prove the data pipeline* (fetch →
store → display players), so we must decide how much UI to build now versus defer.

The risk is premature complexity: standing up a web framework and a JavaScript
front end before there is any data worth serving.

#### Decision Drivers (Key Requirements)
- **Prove the slice:** Sprint 001 needs to *display* players, nothing more.
- **Keep it simple / defer complexity:** don't build a web stack with no data yet.
- **Preserve the long-term path:** the Charter/Roadmap direction (FastAPI, later a
  web UI) must remain open without rework.

---

### 💡 Options Considered

#### Option 1: Console output now → FastAPI later, web UI deferred *(Chosen)*
* **Description:** v0.1 renders a plain console table. FastAPI is introduced in a
  later sprint once there is data worth serving over HTTP. The choice of web UI
  framework (React/Next.js vs Streamlit/Dash) is deferred until then.
* **Pros:**
  - ✅ Smallest thing that proves the pipeline — no web stack to learn yet
  - ✅ Keeps focus on data/API/storage fundamentals in Sprint 001
  - ✅ The layered architecture lets presentation be swapped without touching
    ingestion or storage
* **Cons:**
  - ❌ Console output is throwaway (but cheap)
  - ❌ Defers, rather than settles, the web-UI framework choice

#### Option 2: FastAPI + web UI now
* **Description:** Stand up FastAPI and a front end (React/Next.js or Streamlit) in
  Sprint 001.
* **Pros:**
  - ✅ Closer to the long-term product shape immediately
* **Cons:**
  - ❌ Significant complexity before any data exists to display
  - ❌ Splits Sprint 001 focus across API, storage, web server, and front end
  - ❌ Risks committing to a UI framework before requirements are understood

---

### 🎯 Decision & Justification

**Chosen Option:** Option 1 — Console now → FastAPI later, web UI deferred

**Reasoning:**
Displaying a table does not require a web server. Building one now would add a large
learning and complexity surface for no data benefit, against "keep it simple" and
"small steps." The v0.1 layered design isolates presentation behind the storage
layer, so moving from "print a table" to a FastAPI endpoint — and later a web UI —
is an additive change, not a rewrite. Deferring the React vs Streamlit/Dash choice
avoids committing before we understand the UI's real requirements.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** Sprint 001 stays small (stdlib + `requests`); the data
  pipeline is proven before any UI investment.
* **Negative Impact / Trade-offs:** The console renderer is temporary; a UI-framework
  decision is postponed (tracked as a future ADR).
* **Risks & Mitigations:**
  - *Risk:* presentation logic leaks into lower layers, making the later swap hard.
    *Mitigation:* keep the display layer read-only over storage; enforce one-way
    data flow (Architecture §3) in review.

---

### 🛠 Implementation & Migration
* **Components Affected:** Architecture, Code (presentation layer), Docs
* **Action Items:**
  - [x] Record provisional stance in Architecture v0.1 §8
  - [ ] Implement console table in Sprint 001 (US-004)
  - [ ] Plan FastAPI introduction in a later sprint (once data is worth serving)
  - [ ] Open a follow-up ADR for the web-UI framework (React/Next.js vs Streamlit/Dash)

---

### 🔄 Review & Reconsideration
* **Review Date:** When a later sprint introduces FastAPI / an HTTP interface
* **Triggers for Reconsideration:**
  - [ ] A stakeholder needs to view data outside the developer's terminal
  - [ ] Analytics outputs (Roadmap Phase 2+) need richer, interactive presentation
  - [ ] The AI/RAG chat layer (Roadmap Phase 4) needs a front end

---

### 🔗 References & Related Artifacts
- **Related Stories/Bugs:** US-001 (Architecture v0.1), US-004 (Display player table)
- **External Docs:** [Roadmap](../04_Roadmap/Roadmap.md) · [Architecture v0.1 §8](../03_Architecture/Architecture.md) · [ADR-001](./ADR-001-single-user-vs-multi-user.md)
