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
1. Get exact column list for the 14-table working set (schema study has table-level detail;
   confirm whether column-level DDL is needed beyond what's already documented)
2. Scaffold `app/` (FastAPI) and `frontend/` (React) skeletons
3. Get first batch of (question, hand-written SQL) pairs from Tarun to seed the eval set
4. Build minimal eval harness, run against `qwen3:14b`, establish a baseline pass rate
5. Iterate based on real failures (same cluster-by-cluster method V1 used, applied to the new
   simpler pipeline)

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
