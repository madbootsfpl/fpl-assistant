# Architectural Decision Record: Single-User Tool vs Multi-User Product

**Decision ID:** ADR-001
**Date:** 2026-07-31
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The Roadmap (Phase 1) explicitly flags an early decision: *"Decide early whether
this is an internal tool or a multi-user product — this choice drives later UI
decisions."* It affects authentication, data model (whose team? whose data?),
storage, deployment, and the entire UI direction.

We need a stance now so Sprint 001 (and the v0.1 Architecture) can proceed without
building machinery — user accounts, auth, per-user data isolation — that a learning
project does not yet need.

#### Decision Drivers (Key Requirements)
- **Learn first:** the Charter prioritises understanding over shipping a product.
- **Keep it simple:** avoid complexity (auth, multi-tenancy) with no current user.
- **Don't paint into a corner:** later multi-manager/league analysis (Roadmap
  Phases 3+) should remain possible without a rewrite.

---

### 💡 Options Considered

#### Option 1: Single-user / internal tool *(Chosen)*
* **Description:** The app serves one person (the developer). No accounts, no auth.
  A manager ID, when needed, is supplied via config rather than a login.
* **Pros:**
  - ✅ Simplest possible foundation — matches "keep it simple" and "small steps"
  - ✅ No auth, sessions, or per-user isolation to build or secure
  - ✅ Fastest path to the learning goals (Python, APIs, SQLite, testing)
* **Cons:**
  - ❌ Not directly shippable to other users without later work
  - ❌ Some multi-user concerns are deferred rather than solved

#### Option 2: Multi-user product from the start
* **Description:** Build user accounts, authentication, and per-user data
  isolation up front.
* **Pros:**
  - ✅ No later migration if the project ever becomes a public product
* **Cons:**
  - ❌ Large upfront complexity (auth, security, multi-tenancy) with zero users
  - ❌ Distracts from the core learning goals and the data-pipeline slice
  - ❌ Violates "build small working features; avoid large unfinished systems"

---

### 🎯 Decision & Justification

**Chosen Option:** Option 1 — Single-user / internal tool

**Reasoning:**
For a learning project with one user, multi-user machinery is complexity without a
customer. Option 1 lets Sprint 001 focus on the data pipeline and core skills. The
risk of Option 1 — a costly rewrite later — is mitigated by the v0.1 data model,
which the Roadmap already asks to "design from day one to support multi-manager /
league analysis later (even if Phase 1 only uses a single manager ID)." We adopt
that guidance: schema stays multi-manager-friendly, but no auth/UI is built for it
yet.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** Minimal foundation; no auth to design or secure; effort goes
  to the data pipeline and learning objectives.
* **Negative Impact / Trade-offs:** The app is not multi-user-ready; adding accounts
  later will require auth, session handling, and per-user data scoping.
* **Risks & Mitigations:**
  - *Risk:* schema assumes a single user and blocks multi-manager later.
    *Mitigation:* keep entities keyed by FPL ids (player id, team id, and later
    manager id) rather than baking in a single implicit owner.

---

### 🛠 Implementation & Migration
* **Components Affected:** Architecture, Database, Docs
* **Action Items:**
  - [x] Record provisional stance in Architecture v0.1 §9
  - [ ] Ensure v0.1 schema uses explicit FPL ids (no implicit single-owner columns)
  - [ ] Revisit before any feature that reads a specific manager's team

---

### 🔄 Review & Reconsideration
* **Review Date:** When Roadmap Phase 3 (Team Analyser / manager ID features) begins
* **Triggers for Reconsideration:**
  - [ ] Intent to share the tool with other users
  - [ ] A feature needs more than one manager's data at once
  - [ ] Deployment beyond the developer's own machine

---

### 🔗 References & Related Artifacts
- **Related Stories/Bugs:** US-001 (Architecture v0.1)
- **External Docs:** [Roadmap](../04_Roadmap/Roadmap.md) · [Architecture v0.1 §9](../03_Architecture/Architecture.md)
