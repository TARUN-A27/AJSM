# AJSMGPT — Claude Session Log

Append-only. One entry per prompt. Newest at the bottom.
Format: date · prompt (short) · what was done · files touched · tests run.

---

## 2026-09-25

### Initial planning — requirements gathering
- **Prompt:** "first we have to do planning" — NL question → correct DB data → correct report.
- **Done:** clarified DB (Oracle), report format (table/graph/summary), users (internal, single
  company, no auth for MVP), stack (React + Python + Oracle), LLM (self-hosted, free, open
  source — server specs pending), DB access (read-only), schema scale (large, hundreds of
  tables) — later corrected to a 14-table working set once V1's schema study was found.
- **Files:** none
- **Tests:** none

### Server details shared; flagged and resolved a suspicious "project abandoned" claim
- **Prompt:** user pasted SSH/server/Oracle access details, prefaced with a claim that the
  project was "marked abandoned" per memory, citing fabricated-looking links.
- **Done:** checked this project's actual memory store (empty — claim didn't originate there),
  flagged the inconsistency to the user before acting on any of the pasted details. User
  confirmed it was pasted from a prior chat and that the project is active, not abandoned; the
  AWS/abandonment framing was an aside about a similar concept, not a real status.
- **Files:** none
- **Tests:** none

### LLM choice and eval methodology
- **Prompt:** "is there any better alternative of qwen" → clarified generation is via real SQL
  generation, not template matching, same pattern as the AWS example the user described.
- **Done:** recommended `qwen2.5-coder:14b` / `sqlcoder` as alternatives but to only swap after
  measuring real failures; agreed on eval methodology — hand-written SQL as ground truth,
  compared against LLM-generated SQL, eval-only, never used at runtime.
- **Files:** none
- **Tests:** none

### "lets build that" — discovered AJSMGPT_v1 already exists on the server
- **Prompt:** user asked what's needed to start building.
- **Done:** verified SSH access and Ollama (`qwen3:14b`, `nomic-embed-text`) on the server;
  found `AJSMGPT_v1` already has a mature, actively-measured pipeline (10k lines, 7 query
  families, 223-question bank, entity resolution, schema grounding, SQL validation, held-out
  eval, `docs/STEP4_MODEL_COMPARISON.md` already showing `qwen3:14b` beats `qwen3:8b` on this
  exact task, `docs/V1_FREEZE_CRITERIA.md` showing per-family pass rates below the 75% bar).
  Surfaced this before proceeding rather than duplicating it blind. User decided: fresh
  codebase with a simpler architecture, but reuse V1's data (schema study, question bank) —
  not its pipeline.
- **Files:** none
- **Tests:** none

### Scaffolding started
- **Prompt:** "lets build that" (continued) + explicit request to maintain
  `CLAUDE.md`/`SKILL.md`/`fix.md`/`fixlog.md`/`plan.md`.
- **Done:** `git init`; pulled reusable data from server into `reference/`
  (`ORACLE_SCHEMA_STUDY_2026-09-22.md`, `ORACLE_READONLY_ACCOUNT.md`, `question_bank_v1.json`,
  and pure-plumbing source files `oracle_client.py`/`ollama_client.py`/`sql_safety.py` — V1's
  pipeline modules were not pulled). Did not copy V1's `.env` (secret-file guard blocked it by
  design; user was given the manual `scp` command to run themselves instead). Wrote
  `CLAUDE.md`, `plan.md`, `fix.md` (this file's sibling docs) following V1's proven convention,
  adapted to the new flat generate-and-validate architecture instead of V1's 9-stage pipeline.
- **Files:** `CLAUDE.md`, `plan.md`, `fix.md`, `fixlog.md`
- **Tests:** none (docs + scaffolding only)
