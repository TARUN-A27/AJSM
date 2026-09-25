# AJSMGPT

## 1. Product goal
A user types a plain-English business question. AJSMGPT returns a report built from the company's
Oracle ERP database — no SQL knowledge, no schema knowledge required from the user.

This is a **fresh rebuild**, not a continuation of `AJSMGPT_v1` (server path
`/home/ajsmgpt/AJSMGPT_v1`). V1's 9-stage plan-extract-ground-generate pipeline (QueryPlan →
semantic validation → schema grounding → grounded SQL generation → SQL validation) is not being
reused — this project takes a flatter, purely generative approach: give the LLM the schema +
known quirks as context, let it write SQL directly, validate SELECT-only, execute, report. V1's
**data** (schema study, question bank, read-only Oracle account) is reused; see `reference/`.

## 2. Architecture
```text
NL question
→ build prompt: question + 14-table schema + documented quirks   app/schema_context.py
→ LLM generates Oracle SQL                                       app/llm_client.py (Ollama)
→ SELECT-only validation (defense in depth)                      app/sql_safety.py
→ read-only Oracle execution                                     app/oracle_client.py
→ shape result as table / chart / summary                        app/report.py
```
Principle: **the LLM generates SQL fresh for every question. No templates, no pre-written
queries, no lookup table.** Ground truth SQL (written by hand) exists only in the eval set, never
shown to the LLM or the app at runtime.

## 3. Non-negotiable safety rules
- Oracle access is read-only. Never introduce DML, DDL, or PL/SQL execution.
- Never bypass SQL safety validation (SELECT-only check runs on every generated query, even
  though the DB account itself is also read-only — defense in depth).
- Never expose credentials, DSNs, or ERP result rows in code, logs, tests, or chat.
- Do not read or print `.env` contents into the conversation — variable names only if needed.
- Do not modify `.env`.

## 4. Repository structure
```text
app/                 backend (FastAPI): llm_client, oracle_client, sql_safety, schema_context, report
frontend/             React app
reference/            reused V1 data: schema study, read-only account doc, question bank,
                       plumbing-only source files (oracle_client.py, ollama_client.py, sql_safety.py)
plan.md               architecture decisions, phases, next steps — update when a decision lands
fix.md                open failures with root cause + fix — update status as fixed
fixlog.md             append-only session log — one entry per prompt
SKILL.md              how to work on this project — conventions, eval workflow, how to add scope
```

## 5. Current active work
Phase: **scaffolding**. See `plan.md` for status and next steps.

## 6. Current known issues
None yet — see `fix.md` once evaluation starts.

## 7. Server / access
```text
ssh -p 5555 ajsmgpt@103.171.13.142      # key-auth, RTX 5070, Ollama 0.30.10
Ollama models: qwen3:14b (generation), nomic-embed-text (embeddings, held in reserve)
Oracle: 11g EE 11.2.0.1.0 — no FETCH FIRST, use ROWNUM wrapper for pagination
Read-only account: ajsmgpt_ro — CREATE SESSION + SELECT on the 14-table working set only
```
14-table working set: `PURCHASEORDER`, `GRN`, `INVOICEGRN`, `ISSUE`, `MRS`, `MRS_TEMP`,
`ITEMSTOCK`, `INVITEMS`, `PARTYMASTER`, `DEPT`, `UNIT`, `PLACE`, `STATE`, `COUNTRY`. Full detail,
quirks, and join paths: `reference/ORACLE_SCHEMA_STUDY_2026-09-22.md`.

## 8. Oracle restrictions
- Do not run Oracle/network checks (schema access tests, live eval runs) from the laptop — server
  only, same as V1's convention.
- Do not run Ollama commands unless explicitly asked.
- Oracle execution goes only through the validated path (`sql_safety` → `oracle_client`).

## 9. Git restrictions
- Never `git add .`; stage only files you changed.
- Preserve unrelated dirty worktree changes.
- Never reset, restore, clean, or delete unrelated work.
- Commit or push only when asked.

## 10. Change discipline
- Work only within the requested task; no unrelated refactors, no scope expansion.
- Prefer deterministic validation over LLM assumptions.
- Do not port V1 pipeline modules (entity resolution, schema grounding, query plan) into this
  codebase — the flatter architecture in §2 is the deliberate replacement.
- Stop when acceptance criteria are met; do not continue to the next task unasked.

## 11. Definition of done
- Requested acceptance criteria met.
- Changed files listed.
- `fixlog.md` entry appended (prompt · done · files · tests). Every prompt, no exceptions.
- `plan.md` / `fix.md` updated if a decision or fix landed.
