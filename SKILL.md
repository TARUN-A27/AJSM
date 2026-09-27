# AJSMGPT — Working Conventions

How to work on this project session to session. Not a formal Claude Code skill — a project-level
habits doc, same spirit as V1's discipline (see `reference/` docs) but for this fresh codebase.

## The loop
1. Pick a real question (from `reference/question_bank_v1.json` or a new one Tarun gives) that
   the app currently gets wrong.
2. Diagnose the actual root cause — bad SQL from a genuine schema-quirk trap (§5 of the schema
   study), a validator gap, a prompt that under-specifies — not just "the LLM was wrong."
3. Fix the narrowest thing that addresses the root cause, not the specific question's surface
   symptom (same principle as `CLAUDE.md` root-cause-over-symptom guidance).
4. Sync the fix to the server and **restart the service** (`systemctl --user restart
   ajsmgpt-v2.service`) before testing live — rsync alone does not update the running process;
   it keeps executing whatever was in memory at import time (hit for real, plan.md 2026-09-27).
5. Re-run the eval set. Confirm the fix moved the failing case and didn't regress others.
6. Record it: `fix.md` (root cause + fix, one entry per distinct cause), `fixlog.md` (append an
   entry for the session, every prompt, no exceptions — this slipped once already, see the
   2026-09-27 backfill entry), `plan.md` (if a decision changed, not just a bug fix).

## Ground rules
- Never grow the pipeline back toward V1's shape (entity resolution stage, schema grounding
  stage, query plan extraction) as a reflex fix. If the flat generate-and-validate approach
  genuinely can't reach acceptable accuracy on a class of question, that's a `plan.md` decision
  to discuss, not something to patch in silently.
- Ground truth SQL (hand-written, for eval) never touches the LLM prompt or the runtime path.
  If code ever reads eval-answer SQL at runtime, that's a bug, not a feature.
- Model choice lives behind one function (`app/llm_client.py`). Swapping `qwen3:14b` for
  anything else is a config change; don't hardcode the model name elsewhere.
- Schema/quirks context (`app/schema_context.py`) is the only place table/column knowledge
  should be hand-maintained. If a new quirk is discovered, it goes there and into
  `reference/ORACLE_SCHEMA_STUDY_2026-09-22.md` stays as the historical record — don't fork a
  second copy of schema knowledge.

## Running the eval
```bash
# server only — Oracle/Ollama access is server-side (CLAUDE.md §8)
ssh -p 5555 ajsmgpt@103.171.13.142
cd /home/ajsmgpt/projects/AJSMGPT_v2
AJSMGPT_ENV_FILE=/home/ajsmgpt/secrets/ajsmgpt_v2.env PYTHONPATH=. ./venv/bin/python scripts/run_eval.py
```
This calls `generate_sql`/`run_safe_select` directly — it does not go through the running
`/ask` server, so it always reflects whatever's on disk, no restart needed for the eval itself.

## Managing the live service
Systemd user service (no sudo needed — `Linger=yes` already enabled), survives reboot/logout,
auto-restarts on crash. Full detail: `plan.md`'s "Server deployment" section.
```bash
ssh -p 5555 ajsmgpt@103.171.13.142 "systemctl --user restart ajsmgpt-v2.service"   # after every code sync
ssh -p 5555 ajsmgpt@103.171.13.142 "systemctl --user status ajsmgpt-v2.service"    # health check
ssh -p 5555 ajsmgpt@103.171.13.142 "journalctl --user -u ajsmgpt-v2.service -f"    # tail logs
```

## Adding a new query family
Same shape V1 used for stock/GRN (`reference/ORACLE_SCHEMA_STUDY_2026-09-22.md`'s freeze-criteria
history): a family isn't "added" until it has its own read-only profiling pass (verified columns,
joins, row-shape gotchas) — don't extend schema context to a table nobody has studied yet.
