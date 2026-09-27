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

### Public GitHub repo wired up
- **Prompt:** "use this repo https://github.com/TARUN-A27/AJSM" then "doit" to commit+push.
- **Done:** added `origin`, wrote `.gitignore`. Found the repo is **public** — flagged that
  `reference/` contains real internal Oracle schema/business data before pushing anything;
  Tarun chose to keep the repo public but exclude `reference/` from git entirely (gitignored,
  local-only). Committed and pushed `CLAUDE.md`/`SKILL.md`/`plan.md`/`fix.md`/`fixlog.md`/
  `.gitignore` to `main`.
- **Files:** `.gitignore`, `CLAUDE.md`, `SKILL.md`, `plan.md`, `fix.md`, `fixlog.md`
- **Tests:** none

### Full-coverage goal confirmed; complete two-phase plan written
- **Prompt:** "first we have to successed with structured databse then later with
  unstructutre / our v1 is within the schema which we have it should be able to give any
  answer" + earlier request for a complete project plan including RAG over documents/PDFs/
  images.
- **Done:** rewrote `plan.md` into Phase 1 (structured, in progress) / Phase 2 (unstructured
  RAG) / Phase 3 (unified routing). Recorded the Phase 1 success bar explicitly: answer *any*
  question the 14-table schema can answer, not a fixed set of families like V1. Confirmed
  Qdrant (`:6333`) is already running on the server (5 existing collections, all leftover
  schema-metadata experiments, none reusable for document RAG) and that no vision-capable
  Ollama model is pulled yet. Learned Phase 2's documents/images are stored as Oracle BLOB
  columns, not files — still needs scoping before Phase 2 can be designed for real.
- **Files:** `plan.md`
- **Tests:** none

### Backend scaffold built and unit-tested
- **Prompt:** continuation of "doit" direction — built out `app/` per `plan.md`'s next steps.
- **Done:** pulled the real column-level schema profile for the 14-table working set
  (`reference/working_set_schema.json`, filtered server-side from V1's 1.8MB Oracle dictionary
  dump, not re-derived). Built `app/oracle_client.py`, `app/sql_safety.py`, `app/llm_client.py`
  (adapted from V1's plumbing — dropped `backend_logger`/`sql_datatype_validator` pipeline
  dependencies, stdlib `logging` instead), `app/schema_context.py` (schema + quirks context,
  distilled from `ORACLE_SCHEMA_STUDY_2026-09-22.md` §5/§6.1 — verified business definitions
  like PO-pending ladder and MRS-pending anti-join, not re-guessed), `app/sql_generator.py`
  (question -> SQL, no templates), `app/report.py` (deterministic table/chart/summary shaping,
  no LLM), `app/main.py` (FastAPI `/ask`, `/health`). Verified schema context is ~7k tokens
  (fits `qwen3:14b` comfortably, confirms the no-RAG-for-schema decision). App imports and
  routes register correctly. Not yet run against real Oracle/Ollama (server-only per §8).
- **Files:** `app/__init__.py`, `app/oracle_client.py`, `app/sql_safety.py`,
  `app/llm_client.py`, `app/schema_context.py`, `app/sql_generator.py`, `app/report.py`,
  `app/main.py`, `requirements.txt`, `.env.example`, `scripts/test_sql_safety.py`,
  `scripts/test_schema_context.py`, `reference/working_set_schema.json` (gitignored),
  `plan.md`
- **Tests:** `scripts/test_sql_safety.py` (9), `scripts/test_schema_context.py` (3) — 13/13 pass

### Frontend built
- **Prompt:** "now lets build frontend keep it minimal the ui ux should spectacular... light/dark"
  + "if you can add motion grapgic add it".
- **Done:** scaffolded `frontend/` with Vite + React + TypeScript, Tailwind v4, `motion`
  (animations), `recharts` (chart view). Kept the existing template's violet accent/CSS-variable
  palette (already had a good light/dark foundation) but switched dark mode from
  `prefers-color-scheme`-only to a class-based toggle so the user can override system
  preference, applied pre-paint via an inline script to avoid a flash of the wrong theme on
  load. Built: `ThemeToggle`, `QuestionInput`, `EmptyState` (example question chips),
  `TurnCard` (question bubble + result + collapsible SQL, entrance animation), `ResultView`
  (table/chart/summary, matching `app/report.py`'s `view` field exactly). Removed unused
  default Vite template assets (`App.css`, demo SVGs). Verified with `tsc -b && vite build`
  (no errors) and visually in the browser pane — light and dark themes, all three result views,
  loading state, error state — against a throwaway mock backend (`/tmp/.../mock_backend.py`,
  not part of the repo, deleted after QA). Not yet wired to the real FastAPI backend (needs
  Oracle/Ollama, server-only).
- **Files:** `frontend/` (new), `.claude/launch.json` (dev server preview config), `plan.md`
- **Tests:** `tsc -b` type-check clean; manual visual QA in-browser (both themes, 3 result
  views, loading/error states) — no automated frontend tests yet (YAGNI until there's real
  logic beyond rendering to break)

### Design system pass via ui-ux-pro-max
- **Prompt:** "us the ui ux pro max plugin to maximise the frontend devlopment this inital
  one look so genric".
- **Done:** ran `ui-ux-pro-max` (`--design-system` for product="internal enterprise AI query
  tool", variance 5/motion 6/density 7) plus targeted domain searches (chart, icons, color,
  react stack, ux animation). Applied: dual-accent palette (violet primary + cyan secondary,
  replacing the single-hue purple) with richer near-black dark mode instead of lightened
  violet; Inter + JetBrains Mono replacing system-ui; Phosphor icons (`@phosphor-icons/react`)
  replacing the emoji hero icon and hand-drawn send arrow — `MagicWand`/`ChartBar`/`Database`
  for empty state, `PaperPlaneTilt` for send, `WarningCircle`/`SmileySad`/`CaretDown` for
  error/empty/SQL-toggle states; categorical accessible bar-chart palette (6 distinct hues,
  sorted descending by value) instead of one repeated accent color, per the chart-domain
  guidance; gradient (violet→cyan) question bubbles, send button, and summary-value text;
  glassmorphic blurred header/footer; subtle ambient radial-gradient glow (kept faint,
  `opacity-[0.07]`, so it doesn't compete with content); `prefers-reduced-motion` respected
  globally via a CSS media query. Verified with `tsc -b && vite build` (clean) and visual QA
  in-browser against the same throwaway mock backend, both themes, chart/table views.
- **Files:** `frontend/src/index.css`, `frontend/src/App.tsx`,
  `frontend/src/components/EmptyState.tsx`, `QuestionInput.tsx`, `TurnCard.tsx`,
  `ResultView.tsx`, `frontend/package.json` (added `@phosphor-icons/react`)
- **Tests:** `tsc -b` clean; manual visual QA (both themes, chart/table/summary views)

### Monochrome redesign — second ui-ux-pro-max pass
- **Prompt:** "need more improvemnt with frontned show me your full potential dotn add
  colour keep it dark chromatic it feels genric take time as you wish to devlop" — the
  violet/cyan gradient version (previous entry) was judged generic; asked for a proper
  monochrome direction instead of a color swap.
- **Done:** re-ran `ui-ux-pro-max` for a monochrome/dark-precision direction (`dark-mode-oled`
  + `minimalism-and-swiss-style`, "Developer Mono" typography pairing). Full palette
  rebuild — true zinc/black-white scale (`#000000`/`#fafafa` dark, `#fafafa`/`#09090b`
  light), no hue anywhere except error-red (kept as the one functional exception, not
  decorative). Swapped Inter -> IBM Plex Sans (body) + JetBrains Mono (labels/data/headings)
  — the "developer tools, precise, technical" pairing. This was a structural redesign, not
  just new CSS variables: replaced chat-bubble metaphor with a QUERY/RESULT mono-labeled
  layout (reads as a query tool, not a consumer chatbot); replaced the gradient hero icon
  with an animated corner-bracket "scan target"; replaced the 3-dot loading indicator with a
  scanning progress line + "querying database…" mono status text; replaced the chart's single
  repeated accent color with a grayscale intensity ramp (6 shades, sorted descending) plus
  direct value labels on each bar, since color can no longer distinguish categories at all
  (chart-domain guidance: never rely on color alone — doubly true with zero hues); added a
  terminal-style input (`>` prompt, bordered square send button instead of a filled gradient
  circle); added a barely-perceptible SVG noise-grain texture on the body for tactile depth
  on pure black (`opacity 0.05` dark / `0.025` light); mono `AJSMGPT` wordmark with a
  blinking cursor block and a pulsing "LIVE" status dot. Verified clean `tsc -b && vite
  build` and full visual QA in-browser, both themes, chart/table/summary views, against the
  same throwaway mock backend (stopped after).
- **Files:** `frontend/src/index.css`, `frontend/src/App.tsx`,
  `frontend/src/components/EmptyState.tsx`, `QuestionInput.tsx`, `TurnCard.tsx`,
  `ResultView.tsx`
- **Tests:** `tsc -b` clean; manual visual QA (both themes, all 3 result views, loading
  scanner state)

### First real end-to-end test — deployed to server, found and fixed 5 real bugs
- **Prompt:** "now lets come to the main part where should be able answer by meta need to
  devlop that" — develop/verify the actual metadata-driven NL-to-SQL capability for real,
  not just scaffold it.
- **Done:** deployed to `/home/ajsmgpt/projects/AJSMGPT_v2` on the server (port 8002 reserved,
  8000/8001 already taken by legacy/V1). User asked for the deployment directory to be
  separate from V1/legacy (not a flat sibling under `/home/ajsmgpt/`) — moved to
  `projects/AJSMGPT_v2`. User also asked for `.env` to live outside the project directory
  entirely — added `app/config.py` (loads from `$AJSMGPT_ENV_FILE` if set) and moved the
  secret file to `/home/ajsmgpt/secrets/ajsmgpt_v2.env`; refactored `oracle_client.py`,
  `llm_client.py`, `sql_safety.py` to use it instead of each calling `load_dotenv()`
  independently. Verified Oracle connectivity (real `ajsmgpt_ro` account, real row counts)
  and Ollama connectivity independently, then ran 5 real natural-language questions through
  the full `generate_sql` -> `validate_select_only` -> `run_safe_select` pipeline against live
  data. Found and fixed 5 real bugs this surfaced (full detail in `fix.md` #1-5): SQL
  extraction not robust to prose-wrapped responses; model answering from an approximate
  row-count hint instead of querying; an invented column name (`SUPPLIERCODE` vs real
  `SUP_CODE`); an unqualified table name failing to resolve; and a genuine data-quality
  discrepancy — `PURCHASEORDER.BASIC` is NULL on 72% of rows, contradicting the schema study's
  "never null" claim, `NET` is the reliable total-value column instead. All 5 questions now
  return correct results with zero hardcoded queries. `/ask` HTTP endpoint itself not yet
  tested (only the internal functions directly) — next step.
- **Files:** `app/config.py` (new), `app/oracle_client.py`, `app/llm_client.py`,
  `app/sql_safety.py`, `app/sql_generator.py`, `app/schema_context.py`,
  `scripts/test_sql_generator.py` (new), `scripts/test_schema_context.py`, `fix.md`, `plan.md`
- **Tests:** 19/19 unit tests pass locally; 5/5 real questions verified correct against live
  Oracle + Ollama on the server

### Live end-to-end test through the actual frontend
- **Prompt:** "test alll possible question forntnend and show live".
- **Done:** started the real backend on the server (`uvicorn`, port 8002 — 8000/8001 already
  taken), opened an SSH local port-forward (`-L 8002:localhost:8002`) so the local frontend
  dev server could reach it, pointed `vite.config.ts`'s proxy at 8002, and ran real questions
  through the actual UI (not the mock backend). Verified live: stock aggregation ("total
  stock of item A12001392" -> 3, matches earlier CLI test), a ranked join ("top 5 suppliers by
  PO value" -> same 5 suppliers/values as the CLI test, rendered as a table), and the MRS
  anti-join ("how many MRS are pending" -> 923) — the model correctly reproduced the *entire*
  compound anti-join business definition (LEFT JOIN on MrsNo+SlNo, all 5 flag conditions, the
  MillCode null-or-zero check, the NULL anti-join check) from the schema context alone, the
  exact case V1's own team flagged as needing dedicated code to handle. Found one more real
  bug this way (fix.md #6): "what was issued for yarn in 2024" returned NULL live in the UI —
  case-sensitive `LIKE '%yarn%'` matched 0 rows against real (uppercase) data. Fixed with an
  explicit `UPPER()` quirk rule, re-verified live through the same UI after restarting the
  server — same question now returns a real value (8,816.795) with `UPPER(...) LIKE
  UPPER(...)` in the generated SQL. Hit a real deployment snag along the way: moving the
  project directory (`mv AJSMGPT_v2 -> projects/AJSMGPT_v2`) broke every `venv/bin/*` console
  script's shebang (still pointed at the old path) — worked around by invoking
  `venv/bin/python -m uvicorn` instead of the broken `venv/bin/uvicorn` script.
- **Files:** `app/schema_context.py`, `scripts/test_schema_context.py`,
  `frontend/vite.config.ts` (proxy port 8001 -> 8002), `fix.md`
- **Tests:** 20/20 unit tests pass locally; 4 more questions verified correct live through the
  actual frontend UI against real Oracle + Ollama (total across this session: 9 real questions
  verified end-to-end, 6 real bugs found and fixed)

### Formal eval harness built, 12/12 reached, answer summaries added [backfilled]
- **Prompt:** "now lets come to the main part..." continuation + "test alll possible question
  forntnend and show live" + "for each output in the ajsmgpt give summary also if data does not
  exist five reply in sentnece as if resppned by llm" + "do it" (commit) + "tell me next plan".
- **Done:** built `scripts/run_eval.py` + `reference/eval/golden_answers.json` (12 questions
  across 7 families, Claude-derived and Oracle-verified, same pattern V1 used). Six eval runs,
  fixing a real bug after each (fix.md #7-#13): no anchor for "today" in relative-date
  questions; "consumed" mapped to the wrong table; wrong schema prefixes on real tables
  (`SCM.ISSUE` instead of `INVENTORY.ISSUE`); an invented underscore in a column name
  (`ISSUE_NO` vs real `ISSUENO`); a numeric literal against a VARCHAR2 code column; an
  over-broad quirk fix that broke a sibling question; and a date range that was correct in the
  system prompt but not attended to until repeated next to the question in the user prompt.
  Reached **12/12**. Along the way found and fixed a bug in the harness itself (hardcoded
  `sql=None` in its own error handler, hiding the real failing SQL) and reworded two golden
  questions that were genuinely ambiguous ("how many GRNs" — line items vs distinct documents).
  Added `app/answer_summary.py`: a second LLM call that phrases the already-verified result as
  one sentence, told never to add a fact not in the data and to state plainly (not guess why)
  when there are no rows; wired into `/ask`'s `summary` field and the frontend. Deployed to the
  server (`/home/ajsmgpt/projects/AJSMGPT_v2`, port 8002, `.env` moved outside the project dir
  to `/home/ajsmgpt/secrets/ajsmgpt_v2.env` per explicit request, `app/config.py` added to load
  it from there). Verified live through the actual frontend (SSH tunnel to port 8002): a
  same-theme cluster (supplier count, top-5 ranking, earliest PO date) and a different-theme
  question (MRS pending) — all matched the eval golden answers exactly, summary sentences
  correct including for the 5-row ranking case. Committed and pushed everything to
  `github.com/TARUN-A27/AJSM` (`f331ca3`) — `reference/` stays gitignored (public repo, real
  internal schema/business data).
- **Files:** `app/sql_generator.py`, `app/schema_context.py`, `app/answer_summary.py`,
  `app/main.py`, `app/config.py`, `app/oracle_client.py`, `app/llm_client.py`,
  `app/sql_safety.py`, `scripts/run_eval.py`, `scripts/test_sql_generator.py`,
  `scripts/test_answer_summary.py`, `scripts/test_schema_context.py`,
  `reference/eval/golden_answers.json`, `frontend/src/types.ts`, `frontend/src/App.tsx`,
  `frontend/src/components/TurnCard.tsx`, `fix.md`, `plan.md`
- **Tests:** 29/29 unit tests pass locally; 12/12 eval questions pass against live Oracle +
  Ollama; 4 additional questions verified live through the actual frontend

### Next-plan discussion + ambiguous-entity design brief [backfilled]
- **Prompt:** "what is the next big plan" -> user specified the design for ambiguous item names
  ("if they ask just mouse we can show them all if in particular we can show exact product...
  for do it later, give me brief... no need to dev now").
- **Done:** proposed two priorities (deployment stability via systemd; the ambiguous-entity
  problem, since "keyboard"/"mouse"/"dell system" are the *highest-occurrence* real questions in
  the bank, far more common than the clean exact-code questions the 12/12 batch covered). User
  gave the design for the latter (exact match -> one answer; ambiguous match -> show all
  candidates, leaning `GROUP BY` so each gets its own row) but deferred building it. No code
  changed — documentation/discussion only.
- **Files:** none
- **Tests:** none

### Knowledge graph built with graphify; local visualization served
- **Prompt:** "/graphify" then "i need to visualise the graph give me lcoal host link".
- **Done:** ran the full graphify pipeline on the project (no existing graph) — 41 files
  detected (32 code, 8 docs, 1 image), AST extraction (228 nodes/407 edges) run in parallel with
  two semantic-extraction subagents (8 docs in one chunk, the favicon SVG in its own per the
  vision-needs-separate-context rule) since no `GEMINI_API_KEY` was set. Merged to 321 nodes/528
  edges, clustered into 18 communities, labeled each, exported `graph.html` + `GRAPH_REPORT.md`
  + `graph.json`. Health check flagged 36 dangling-endpoint edges (docs referenced code modules
  as whole-file concepts; AST creates per-function/class nodes, so some cross-references didn't
  align to an exact node) — surfaced per the honesty rule, not blocking. Notably, the graph's
  own "Surprising Connections" analysis independently re-surfaced the fabricated-looking
  "project marked abandoned" claim from earlier in the project's history as an AMBIGUOUS edge,
  without being told about it. Served `graphify-out/` over `python3 -m http.server` (added to
  `.claude/launch.json` as `graphify-viz`, port 4321) so the interactive graph is reachable at
  `http://localhost:4321/graph.html`.
- **Files:** `.claude/launch.json` (added `graphify-viz` config), `graphify-out/` (generated,
  not committed — matches `reference/`'s local-only treatment for anything schema/business-data
  adjacent, though graphify's own output isn't in `.gitignore` yet — worth adding if this
  becomes a recurring habit)
- **Tests:** none (tooling/visualization only)

### Ambiguous-name matching fixed (fix.md #14) [2026-09-27]
- **Prompt:** "do it" (continuing "today's plan": verify server checkpoint, then tackle the
  ambiguous-entity problem per the design brief from two sessions ago).
- **Done:** verified the backend on the server survived the session gap (real `setsid`-detached
  process, independent of the local session — still running from 2026-09-25). Baseline-tested
  the two highest-occurrence real questions in the bank before changing anything: "keyboard
  stock" (62x/38x/5x) and "last supply of mouse" (44x) — both failed exactly as predicted,
  blindly aggregating across genuinely different products or ignoring the question entirely.
  Fixed with quirk #16 (`app/schema_context.py`): any name-based (`LIKE`) match must `GROUP BY`
  the item so each matching product gets its own row — never a blind aggregate. Re-verified:
  both questions now correctly disaggregate (4 separate keyboard-ish products with individual
  stock figures; 4 separate mouse-ish products with individual last-issue dates). Also verified
  the true-zero-match case ("barcode label," a real 44x-occurrence question for an item that
  doesn't exist under that name) — correct empty result, correctly joined across 3 tables, and
  `answer_summary` produces an honest "No matching records were found" sentence. Noted one
  residual, non-bug ambiguity: "last supply" was read as `ISSUE` (issued out) rather than
  `GRN`/`PURCHASEORDER` (received in) — a defensible reading of genuinely ambiguous business
  language, left open pending Tarun's input on which the business actually means. Also noticed
  and backfilled a gap in this file itself — several prior prompts had `plan.md`/`fix.md`
  updated but no corresponding `fixlog.md` entry, against this project's own "every prompt, no
  exceptions" rule.
- **Files:** `app/schema_context.py`, `scripts/test_schema_context.py`, `fix.md`, `plan.md`,
  `fixlog.md` (this entry + backfill)
- **Tests:** 30/30 unit tests pass locally; 3 real questions re-verified against live Oracle +
  Ollama (2 fixed, 1 confirmed correctly-empty)

### Committed fix.md #14; deployment moved to systemd
- **Prompt:** "continue with next" — commit today's fix, then move to the other open "next plan"
  item (deployment stability).
- **Done:** committed and pushed fix.md #14 (`3487cb5`) — added `graphify-out/` to `.gitignore`
  first (regenerable build artifact, not source). Then tackled deployment: discovered no sudo
  access on the server account, and that the legacy app's systemd-sounding service name
  ("ajsmgpt-api.service") was misleading — it's actually just a raw background process, not
  systemd-managed at all, so there was no existing pattern to copy this time. Found
  `Linger=yes` already enabled for the account and `systemctl --user` working, which makes a
  user-level systemd service fully viable without root. Created
  `~/.config/systemd/user/ajsmgpt-v2.service` on the server (port 8002, `Restart=on-failure`,
  reads `AJSMGPT_ENV_FILE` from the same secrets path as before), enabled it, and verified two
  things for real rather than assuming: (1) killed the process with `kill -9` directly —
  systemd respawned it in under 2 seconds, `/health` immediately serving again; (2) confirmed no
  duplicate process ended up bound to the port after switching over from the old manual
  `setsid nohup` process. Documented the new restart-after-sync workflow in `plan.md`,
  `SKILL.md`, and `CLAUDE.md` §7, since this changes how every future code change reaches the
  live server.
- **Files:** `plan.md`, `SKILL.md`, `CLAUDE.md` (server-side: new systemd unit file, not part of
  this repo)
- **Tests:** crash-recovery verified live (kill -9 -> auto-respawn -> health check passing)
