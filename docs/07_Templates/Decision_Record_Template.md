# Architectural Decision Record: [Short Descriptive Title]

**Decision ID:** ADR-XXX  
**Date:** [YYYY-MM-DD]  
**Status:** [ Proposed | Accepted | Superseded | Rejected | Deprecated ]  
**Superseded By / Replaces:** [ ADR-YYY / N/A ]  
**Deciders / Participants:** [ Names ]  

---

### 📌 Context & Problem Statement
[Describe the situation, background, current limitations, and why a decision is needed now.]

#### Decision Drivers (Key Requirements)
- **Driver 1:** 
- **Driver 2:** 

---

### 💡 Options Considered

#### Option 1: [Name] *(Chosen)*
* **Description:** [Brief summary]
* **Pros:**
  - ✅ Advantage 1
  - ✅ Advantage 2
* **Cons:**
  - ❌ Disadvantage 1

#### Option 2: [Name]
* **Description:** [Brief summary]
* **Pros:**
  - ✅ Advantage 1
* **Cons:**
  - ❌ Disadvantage 1

---

### 🎯 Decision & Justification
**Chosen Option:** Option 1 - [Option Name]

**Reasoning:**  
[Explain why this option won over the others against your decision drivers.]

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** [Benefits gained]
* **Negative Impact / Trade-offs:** [Downsides accepted]
* **Risks & Mitigations:** [Potential future issues and how to manage them]

---

### 🛠 Implementation & Migration
* **Components Affected:** [ Architecture | Code | Database | Infrastructure | Docs ]
* **Action Items:**
  - [ ] Task 1 (e.g., Update compose config)
  - [ ] Task 2 (e.g., Migrate database schema)

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.** `tests/test_adr_index.py` fails without one.
      *(The index once stopped at ADR-122 while 171 existed — 49 missing, found by accident three sprints
      later. A stale document does not fail on its own, so now it does.)*

#### 🧭 If this ADR **renames, moves, merges or retires a user-facing surface**
A page, a tab, a sub-tab, a button, a feature name — anything a person could be told to go and find.

- [ ] **Add the retired phrasing to `RETIRED` in `tests/test_navigation_copy.py`**, with one line on what
      replaced it. Do this *in the same commit as the rename*, not afterwards.
- [ ] **Run the suite.** The guard sweeps every module under `src/web_streamlit` and **names every place still
      using the old wording** — captions, help text, `st.markdown`, the lot. That list is your work item; you
      do not have to go looking for it.
- [ ] **Then check by hand what the guard structurally cannot catch.** It sweeps every module under
      `src/web_streamlit` — Home and Help included — but only for **phrases already in `RETIRED`**. It knows
      nothing about wording that is newly wrong, and nothing at all outside that package:
      - `docs/08_Marketing/Video_Scripts.md` — scripts, shot lists, the series roadmap *(**not swept**)*
      - `~/madboots-site/index.html` — **outside the repo**, and needs a Cloudflare Pages deploy *(**not
        swept**)*
      - any **produced video** that says the old name out loud — the expensive one; check before recording,
        not after
      - and inside the package, re-read the two that *explain* rather than label:
        `Home.py`'s "Explore the sidebar" list and `7_Help.py`'s guide + glossary. A tab can be renamed in a
        way that leaves every listed phrase intact and the surrounding sentence still wrong.
- [ ] **Check no test is pinning the old wording.** Three were found doing exactly that; each would have
      failed the moment the docs were corrected. **A test that fails when you fix the documentation actively
      defends the error** — assert the requirement, never the phrasing.

> **Why this section exists.** In one week, five documents were found teaching a navigation that no longer
> existed — the ADR index, Home, Help, eight strings in `src/web_streamlit`, and all nine marketing scripts.
> Every one was found *by accident, while doing something else*, because **when navigation changes the code
> gets updated and the copy describing it does not — nothing connects them**. This checklist is the
> connection, and the moment to use it is while you are writing the ADR that causes the change.

---

### 🔄 Review & Reconsideration
* **Review Date:** [YYYY-MM]
* **Triggers for Reconsideration:**
  - [ ] Trigger 1 (e.g., Scaling beyond X users)
  - [ ] Trigger 2 (e.g., Cost exceeds threshold)

---

### 🔗 References & Related Artifacts
- **Related Stories/Bugs:** [US-XXX / BUG-YYY]
- **External Docs:** [Link]