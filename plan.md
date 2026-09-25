# AJSMGPT — Plan

Goal: user asks a business question in plain English → AJSMGPT answers it from whichever source
actually has the answer — structured Oracle ERP data, or unstructured documents/PDFs/images — and
returns a report. Fresh rebuild; V1's data reused, V1's pipeline architecture not reused (see
`CLAUDE.md` §1).

---

## Phases

| Phase | Scope | Status |
|---|---|---|
| 1 | Structured data: NL → SQL → Oracle → report | **in progress** |
| 2 | Unstructured data: documents/PDFs/images → RAG → NL answer | not started — scope below |
| 3 | Unified routing: one question, correct source(s) picked automatically, combined answer when a question needs both | not started — depends on 1 and 2 each working alone first |

Sequencing reason: Phase 1 already has real data (schema study, question bank, a read-only DB
account) and is mid-build. Phase 2 needs its own discovery pass (what documents, what images, what
"correct" looks like) before it can be scoped precisely — building it blind risks the same mistake
Phase 1 almost made (assuming "from scratch" meant re-deriving things that already existed).
Phase 3 is genuinely blocked on both — a router that picks between two sources needs both sources
to exist first.

---

## Phase 1 — Structured data (Oracle DB)

**Success bar (confirmed 2026-09-25):** within the 14-table working set, AJSMGPT should be able to
answer *any* question the data can answer — not scoped to a fixed list of pre-approved question
families like V1's 7. This is why the pipeline is flat generate-and-validate rather than V1's
plan/ground/generate: a family-based pipeline caps coverage at whatever families were explicitly
built; a general SQL-generation approach (LLM sees full schema + quirks, writes SQL directly) is
what makes "any question" possible. The tradeoff, to watch during eval: broader coverage but each
answer needs the same "zero wrong answers" bar V1 held — a confident wrong query is worse than a
refusal, so validation has to catch bad SQL regardless of how novel the question's phrasing is.

### Decisions made (2026-09-25)

| Decision | Choice | Why |
|---|---|---|
| DB | Oracle 11g, existing ERP | Company's real data lives here |
| DB access | Read-only account `ajsmgpt_ro`, 14-table working set | Reused from V1; DB-level guarantee, not just app-level |
| Frontend | React | Given |
| Backend | Python (FastAPI) | Given |
| LLM | `qwen3:14b` via Ollama on company server | Already proven in V1's own A/B test (fix.md #11 there): beat qwen3:8b on classification, adopted as dev/eval model. Swappable — kept behind one function, not hardcoded. |
| Embeddings | `nomic-embed-text` via Ollama | Shared with Phase 2 — text-chunk embeddings for document RAG will use the same model |
| Schema grounding | Full schema + quirks in every prompt, no RAG | Working set is only 14 tables — small enough to fit directly; RAG would be solving a problem we don't have (YAGNI) |
| Pipeline shape | Flat: question → LLM generates SQL directly → validate SELECT-only → execute → report | V1's 9-stage plan/ground/generate pipeline was deliberately not carried over — this project tests whether a simpler generate-and-validate approach gets acceptable accuracy before adding V1-style intermediate stages |
| Auth | None for MVP | Internal employees only, single company |
| DB write access | None — read-only only | Non-negotiable per user |
| Dev workflow | Develop locally, push to server to test | Oracle/Ollama access is server-side only |

### Reused from V1 (`reference/`)
- `ORACLE_SCHEMA_STUDY_2026-09-22.md` — full schema, quirks, join paths (ground truth, not re-derived)
- `ORACLE_READONLY_ACCOUNT.md` — `ajsmgpt_ro` account setup
- `question_bank_v1.json` — 223 real questions across 7 families (purchase, mrs, consumption,
  supplier_lookup, material_lookup, stock, grn) — source of realistic eval questions, no SQL/answers
- `v1_plumbing/oracle_client.py`, `ollama_client.py`, `sql_safety.py` — pure infrastructure,
  no pipeline coupling; starting point for our own versions

### Eval approach
User (Tarun) writes the correct SQL by hand for a set of real questions (ground truth). App
generates SQL for the same questions via the LLM. Compare. This SQL is eval-only — never shown to
the LLM or used at runtime for any other question. Question source: `question_bank_v1.json`
(real, already-collected phrasings) rather than inventing new ones from scratch.

### Next steps
1. ~~Get exact column list for the 14-table working set~~ — done: pulled the real column-level
   profile (`reference/working_set_schema.json`, from V1's verified Oracle dictionary dump) for
   all 14 tables, no re-derivation needed.
2. ~~Scaffold `app/` (FastAPI)~~ — done: `oracle_client.py`, `sql_safety.py`, `llm_client.py`
   (all adapted from V1's plumbing, pipeline dependencies stripped), `schema_context.py` (builds
   the full schema + quirks prompt context from real column data — ~7k tokens, comfortably fits
   `qwen3:14b`'s window, confirms no RAG needed), `sql_generator.py` (question -> SQL via LLM),
   `report.py` (deterministic result shaping, no LLM), `main.py` (`/ask`, `/health`). 13 unit
   tests passing (`scripts/test_sql_safety.py`, `scripts/test_schema_context.py`).
3. ~~Scaffold `frontend/` (React)~~ — done: Vite + React + TypeScript, Tailwind v4 (class-based
   dark mode, manual toggle persisted to localStorage, theme applied pre-paint to avoid a flash),
   `motion` for animation, `recharts` for the chart view. Single-page chat-style UI: question
   bubbles, animated loading state, table/chart/summary result rendering (matches `report.py`'s
   `view` field), collapsible "Show SQL". Verified visually in-browser (light + dark, all three
   result views) against a throwaway mock backend — not yet wired to the real FastAPI backend.
4. Get first batch of (question, hand-written SQL) pairs from Tarun to seed the eval set —
   still open, blocking real accuracy measurement
5. Build minimal eval harness, run against `qwen3:14b`, establish a baseline pass rate
6. Iterate based on real failures (same cluster-by-cluster method V1 used, applied to the new
   simpler pipeline)

### Verified against live Oracle + Ollama (2026-09-25)
Deployed to `/home/ajsmgpt/projects/AJSMGPT_v2` on the server (separate from V1 and the legacy
app — see "Server deployment" below). Ran 5 real questions end-to-end (generate SQL -> validate
-> execute against real `ajsmgpt_ro` -> real result), fixing real failures as they surfaced
(`fix.md` #1-5): a COUNT, a date-filtered COUNT, a business-logic-filtered COUNT (supplier),
a stock SUM, and a ranked join with GROUP BY — all now return correct, verified results with
no hardcoded queries or templates, only the schema+quirks context. This is the core "any
question, answered from metadata alone" bar (confirmed 2026-09-25) actually working, not just
scaffolded.

**Not yet done:** a real held-out eval set (still need Tarun's hand-written SQL for a proper
answer key — `plan.md` next steps #3-4 below), and the `/ask` HTTP endpoint itself hasn't been
hit yet (only the internal `generate_sql`/`run_safe_select` functions directly) — still need to
run `uvicorn` and test through the actual API the frontend calls.

### Live end-to-end test through the real frontend (2026-09-25)
Ran the actual UI (not the mock) against the real backend on the server (SSH tunnel to port
8002). Verified: stock aggregation, a ranked supplier join, and — notably — the MRS-pending
compound anti-join, which the model reproduced correctly (5 flag conditions + a LEFT JOIN NULL
check) from the schema context alone, the exact case V1 flagged as needing dedicated code.
Found and fixed one more real bug live: case-sensitive `LIKE` matched 0 rows against real
(uppercase) data on a name-based question — fixed with an explicit `UPPER()` rule (fix.md #6).

### First formal eval harness (2026-09-25)
Built `scripts/run_eval.py` + `reference/eval/golden_answers.json` (12 questions across 7
families, gitignored — contains real business figures). Golden SQL/answers derived by Claude
and verified directly against live Oracle — same pattern V1 used successfully ("Claude
generated, grounded against real entities, computed answers directly, confirmed by the
client"). Pending Tarun's confirmation the golden answers are correct.

**Results across 6 runs, fixing real bugs between each (fix.md #7-#13):**
7/12 -> 6/12 (dip was the harness's own bug hiding the real SQL, not a regression) -> 11/12 ->
11/12 (same question, new root cause: date arithmetic) -> 11/12 (date hint present in prompt
but not attended to) -> **12/12**. Every failure was genuinely diagnosable and fixable at the
schema-context/prompt level — no case yet where the flat generate-and-validate approach hit a
wall requiring V1-style dedicated pipeline stages. Notable methodological lesson: putting a
correct fact in the system prompt is not the same as the model using it — proximity to the
actual question (user prompt, not just system prompt) mattered more than expected (fix.md #13).

**Caveat on what 12/12 means:** this is 12 hand-picked, unambiguous questions across 7 families
— a real signal that the approach works, not a claim of general accuracy. The known-hard
category (ambiguous item names like "keyboard"/"mouse"/"dell system", and "barcode label" which
matches zero real items despite being a 44x-occurrence real question) is deliberately excluded
from this batch and still needs its own entity-resolution approach before it can be measured
fairly. Next: expand the golden set using more of the 223-question bank, including that harder
category, and get Tarun's confirmation the golden answers themselves are right.

### Answer summaries (2026-09-25)
Added `app/answer_summary.py`: a second, tightly-scoped LLM call that phrases the *already-
verified* Oracle result as one plain-language sentence — given the real rows, told never to
add a fact not in them, explicitly told to state plainly (not guess why) when there are no
rows. Wired into `/ask`'s response (`summary` field) and the frontend (shown above the
table/chart/summary view; empty results now show only the sentence, no generic "no rows"
block). This doubles the LLM calls per question (SQL generation + summary), roughly doubling
latency — acceptable tradeoff for the UX gain, not yet stress-tested under load.

### Server deployment
```text
Code:    /home/ajsmgpt/projects/AJSMGPT_v2   (rsync'd from local, not git-based yet)
Secrets: /home/ajsmgpt/secrets/ajsmgpt_v2.env (deliberately outside the project directory;
                                                copied from AJSMGPT_v1's .env, same DB/Ollama)
Run with: AJSMGPT_ENV_FILE=/home/ajsmgpt/secrets/ajsmgpt_v2.env ./venv/bin/uvicorn app.main:app
Port:    8002 reserved (8000 = legacy, 8001 = V1, both already running)
```
`app/config.py` loads `.env` from `$AJSMGPT_ENV_FILE` if set, else python-dotenv's normal
cwd/parent search — local dev can still just drop a `.env` in the project root if wanted.

---

## Phase 2 — Unstructured data (documents, PDFs, images)

### What's already available on the server
- **Qdrant** (`:6333`) is already running — no new vector-DB infra needed. 5 existing collections
  are all leftover schema-metadata/value-index experiments from an earlier abandoned RAG approach
  to Phase-1-style questions, unrelated to documents — Phase 2 starts with its own fresh
  collection(s), doesn't reuse those.
- **`nomic-embed-text`** (Ollama) — same embedding model Phase 1 already has available, reusable
  for document chunk embeddings.
- **No vision-capable model pulled yet.** Only `qwen3:14b` (text) and `nomic-embed-text` exist on
  the server. Whether one is needed depends on what the images actually are (see open questions).

### Draft architecture (subject to change once scope is known)
```text
document/PDF/image ingested
→ text extraction: native PDF text, or OCR for scanned pages/images
→ chunk → embed (nomic-embed-text) → store in Qdrant (new collection, separate from Phase 1's schema data)

NL question (document-shaped)
→ embed question → Qdrant similarity search (top-k chunks)
→ LLM answers from retrieved chunks, with source citation
→ report (NL answer, not table/chart, unless the question wants extracted structured fields)
```

### Open — needs Tarun's input before this can be scoped for real
- What kinds of documents? (contracts, invoices, circulars, policies, technical specs — each
  implies different extraction/chunking needs)
- Are they already digitized somewhere, or do they need to be collected/uploaded first?
- What are the **images** actually for — scanned paper documents that need OCR (text extraction),
  or photos (item/machine/damage photos) that need visual/semantic search? These need different
  tooling: OCR (e.g. Tesseract, lightweight, no GPU-model pull needed) vs. a vision-capable model
  or image embeddings (needs pulling a new Ollama model, GPU headroom TBD on the RTX 5070).
- Should a document-sourced answer ever combine with a DB-sourced answer in one response (Phase 3
  territory), or are these two clearly separate question types from the user's point of view for now?

---

## Not building yet (YAGNI until proven necessary)
- Auth
- Write access to Oracle
- RAG / vector retrieval over the **Oracle schema** (Phase 1 stays flat — this is different from
  Phase 2's document RAG, which is the whole point of Phase 2)
- Fine-tuning (start with prompting `qwen3:14b` as-is)
- V1's multi-stage entity resolution / schema grounding / query plan pipeline
- Phase 3 routing — not until Phase 1 and Phase 2 each work independently

## Open questions
- Exact `SKILL.md` scope — currently written as "how to work on this project" conventions doc;
  confirm if a different format/content was intended.
- Phase 2 scope questions above.
