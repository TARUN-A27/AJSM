# AJSMGPT — Fix List

Open failures with root cause + fix. Status: ⬜ open · 🔄 in progress · ✅ fixed.

Found by manually running real questions against live Oracle + Ollama (`qwen3:14b`) on the
server — not yet a formal eval harness (`plan.md` next steps), but the same
diagnose-root-cause-not-symptom method.

## 1. ✅ Model answers in prose with SQL embedded in a fence, instead of pure SQL
- **Question:** "How many purchase order lines are there in total?"
- **Symptom:** response was a paragraph of explanation ending in a ```` ```sql ...``` ```` block;
  `_strip_code_fences` only handled a fence wrapping the *whole* response, so
  `validate_select_only` rejected the multi-line prose as "multiple statements."
- **Root cause:** `_strip_code_fences` wasn't robust to prose-wrapped SQL — a formatting gap,
  not a validator bug (the validator correctly rejected non-SQL, exactly as it should).
- **Fix:** `app/sql_generator.py` — renamed to `_extract_sql`, now searches for a fenced block
  anywhere in the response first, falls back to whole-string fence stripping, then raw text.
  Regression test: `scripts/test_sql_generator.py::test_prose_with_embedded_fence`.

## 2. ✅ Model answers from its own estimate instead of writing a query at all
- **Question:** same as #1, re-tested after fix #1 with `think=False`.
- **Symptom:** response was pure prose (no SQL, no fence) stating "approximately 178,700" —
  taken directly from the "Row-count scale" hint in the schema context, not computed.
- **Root cause:** `schema_context.py`'s row-count hint (added so the model could reason about
  LIMIT/aggregation cost) was phrased as a fact the model could just repeat as an answer, and
  the system prompt never explicitly forbade answering from memory/estimation.
- **Fix:** reworded the hint to "NEVER use these numbers as the answer... always write a query"
  (`app/schema_context.py`); added an explicit system-prompt rule in `app/sql_generator.py`
  forbidding answering from memory even when the model "believes it already knows." Also
  reverted `think=False` back to default — disabling thinking made this specific failure mode
  *more* likely, not less.

## 3. ✅ Invented column name: `SUPPLIERCODE` instead of the real `SUP_CODE`
- **Question:** "Which 5 suppliers have the highest total purchase order value?"
- **Symptom:** `ORA-00904: "PO"."SUPPLIERCODE": invalid identifier` — the real column
  (`SUP_CODE`, present in the schema context's own column listing) was never used; the model
  guessed a plausible-sounding name instead.
- **Root cause:** the schema context listed every column but never called out the supplier
  join column specifically, unlike the item join column (which already had an explicit quirk
  entry and never got hallucinated in any test question).
- **Fix:** added an explicit quirk entry naming `SUP_CODE` as the only correct supplier join
  column and `SUPPLIERCODE`/`SUPPLIER_CODE`/`VENDOR_CODE` as names that don't exist
  (`app/schema_context.py` quirk #9). Regression test:
  `scripts/test_schema_context.py::test_supplier_join_column_naming_is_documented`.

## 4. ✅ Unqualified table name fails to resolve
- **Question:** "What is the total current stock of item A12001392?"
- **Symptom:** `ORA-00942: table or view does not exist` on a bare `ITEMSTOCK` (no schema
  prefix), even though an earlier unqualified `PARTYMASTER` query had worked — inconsistent,
  account-search-path-dependent behavior, not something to rely on either way.
- **Fix:** added an explicit rule to always fully qualify every table with its schema exactly
  as shown in the context (`app/schema_context.py` quirk #10). Regression test:
  `scripts/test_schema_context.py::test_schema_qualification_is_required`.

## 5. ✅ `PURCHASEORDER.BASIC` is NULL on 72% of rows — contradicts the schema study
- **Question:** same as #3, re-tested after fixes #3/#4 — query ran without error but every
  `SUM(PO.BASIC)` came back NULL.
- **Root cause:** verified directly against live Oracle: `BASIC IS NULL` on 128,992 of 178,815
  `PURCHASEORDER` rows (72%). `reference/ORACLE_SCHEMA_STUDY_2026-09-22.md` §2.2 states
  "BASIC... never null" — that specific claim was wrong (or the data changed materially since
  the 2026-09-22 study; either way, not safe to trust for this one column going forward).
  Checked the alternative amount columns directly: `NET`, `QTY`, `RATE`, `DISC`, `TAX` are all
  genuinely 0 NULL rows.
- **Fix:** added a quirk entry naming `NET` as the correct "total value" column for
  PURCHASEORDER, explicitly warning off `BASIC` despite the name sounding right
  (`app/schema_context.py` quirk #11). Not yet fixed: the upstream schema study doc itself
  still says BASIC is never-null — should be corrected there too so this doesn't get
  re-trusted if the doc is read again for a different question.

## 6. ✅ Case-sensitive `LIKE` silently matches zero rows on name-text questions
- **Question:** "What was issued for yarn in 2024?" (live UI test, not CLI)
- **Symptom:** query ran without error, returned NULL instead of a number — no crash, no
  refusal, just a confidently-empty answer. Exactly the "confidently wrong" failure shape the
  project's zero-wrong-answers bar exists to catch.
- **Root cause:** verified directly against live Oracle: `ITEM_NAME LIKE '%yarn%'` matches 0
  rows; `LIKE '%YARN%'` matches 121. Item names (and by convention, other name columns) are
  stored uppercase; Oracle's `LIKE` is case-sensitive, and nothing in the schema context told
  the model to account for this.
- **Fix:** added quirk #12 (`app/schema_context.py`) requiring `UPPER()` on both sides of any
  name-based text match. Re-tested live through the frontend after the fix: same question now
  generates `UPPER(INVENTORY.INVITEMS.ITEM_NAME) LIKE UPPER('%YARN%')` and returns a real value
  (8,816.795). Regression test:
  `scripts/test_schema_context.py::test_uppercase_text_matching_is_documented`.

## 7. ✅ No anchor for "today" — relative dates were pure guesswork
- **Question:** "How much cost was consumed last month?" (first formal eval run, #1)
- **Symptom:** generated SQL filtered `ORDERDATE BETWEEN '20230901' AND '20230930'` — September
  2023, for a question asked in 2026. Not close to "last month" by any reading.
- **Root cause:** nothing in the system prompt or schema context ever told the model what
  today's date is. An LLM has no built-in sense of "now" — asked to compute a relative date
  with zero anchor, it produced a plausible-looking but ungrounded one.
- **Fix:** `app/sql_generator.py` now computes `date.today()` fresh on every call and injects
  it into the system prompt ("Today's date is {today}... compute any relative date from this
  exact date — never guess"). Regression test:
  `scripts/test_sql_generator.py::test_todays_date_is_injected_into_the_prompt`.

## 8. ✅ "Consumed" mapped to PURCHASEORDER instead of ISSUE
- **Question:** same as #7.
- **Symptom:** same query also summed `PURCHASEORDER.NET` — purchasing, not consumption — for
  a question about what was *consumed*. Purchasing and consuming are different real-world
  events on different tables; nothing told the model that "consumed" means ISSUE.
- **Fix:** added quirk #13 mapping consumption/consumed/issued to ISSUE. Refined once more after
  this over-corrected the *next* question (see #11). Regression test:
  `scripts/test_schema_context.py::test_consumption_maps_to_issue_not_purchaseorder`.

## 9. ✅ Wrong schema prefix on real tables (`SCM.ISSUE`, `SCM.MRS_TEMP`)
- **Questions:** "How much was issued for item A12001392?", "How many MRS are pending?" (second
  eval run, after the sql-capture bug in the harness itself was fixed — see harness note below)
- **Symptom:** `ORA-00942: table or view does not exist`. ISSUE and MRS_TEMP are real tables,
  just not in the schema the model guessed (SCM instead of INVENTORY).
- **Root cause:** the per-table headers in the schema context do show each table's schema
  (`INVENTORY.ISSUE (~413597 rows)`), but that's easy to lose track of scanning a long column
  listing, especially when SCM.PARTYMASTER is right there in the same context and the model
  overgeneralizes "party/master data lives in SCM" to other tables.
- **Fix:** added a compact schema-membership lookup table at the very top of the quirks text
  (`app/schema_context.py`), separate from and before the full per-table listing, specifically
  calling out that ISSUE/MRS/MRS_TEMP are INVENTORY despite PARTYMASTER being SCM.

## 10. ✅ Invented underscore in a real column name (`ISSUE_NO` vs real `ISSUENO`)
- **Question:** "How many line items are in issue number 737?" (second eval run)
- **Symptom:** `ORA-00904: "ISSUE_NO": invalid identifier` — real column is `ISSUENO`, one word.
- **Root cause:** the third instance of this exact pattern (after `SUP_CODE`/`SUPPLIERCODE` in
  #3) — the model normalizes a column name toward a "cleaner"-looking convention instead of
  copying the exact spelling from the listing. Fixing this one column would just leave the next
  one to fail the same way.
- **Fix:** added a general rule instead of another one-off exception (`app/schema_context.py`
  quirk #14): this schema's naming is inconsistent by table, not inferable from a pattern —
  copy column names character-for-character from the listing, never normalize them.

## 11. ✅ Numeric literal against a VARCHAR2 code column
- **Question:** "How many GRNs are there for supplier code 800967?" (second eval run)
- **Symptom:** `ORA-01722: invalid number` on `WHERE SUP_CODE = 800967` (no quotes) — `SUP_CODE`
  is VARCHAR2(15); Oracle's implicit conversion failed on some non-numeric-looking values in
  the column when trying to compare it as a number.
- **Fix:** added quirk #15 (`app/schema_context.py`): code/number-like columns are VARCHAR2 or
  NUMBER as shown in the listing, not by how the value looks — always check the type and quote
  VARCHAR2 literals even when the value is all digits.

## 12. ✅ Quirk #13 (fix #8) over-corrected: quantity questions got mapped to cost
- **Question:** "How much was issued for item A12001392?" (third eval run, after #7-#11 fixed)
- **Symptom:** returned `SUM(ISSUEVALUE)` = 21,216 instead of `SUM(QTY)` = 32 — a real number,
  just answering a different question than the one asked ("how much was issued" without "cost"
  most naturally means quantity).
- **Root cause:** fix #8's rule said "consumed -> ISSUE.ISSUEVALUE" without distinguishing
  quantity-phrased questions ("how much/how many units") from cost-phrased ones ("how much
  cost/value") — it fixed #7's failure but was broad enough to break a sibling question that
  passed before #8 existed.
- **Fix:** reworded quirk #13 to give both directions explicitly: quantity phrasing -> `SUM(QTY)`,
  cost/value phrasing -> `SUM(ISSUEVALUE)`. Regression test:
  `scripts/test_schema_context.py::test_issue_quantity_vs_value_distinction_is_documented`.

## 13. ✅ Model given real "today" still computed "last month" wrong (current month, not prior)
- **Question:** "How much cost was consumed last month?" (fourth eval run, after fix #7 gave
  the model real "today")
- **Symptom:** SQL was otherwise fully correct (`ISSUE.ISSUEVALUE`, real quirks applied) but
  filtered `ISSUEDATE BETWEEN '20260901' AND '20260930'` — September, the *current* month for
  today=2026-09-25, not August (last month).
- **Root cause:** fix #7 gave the model a real date to anchor to, but relative-date arithmetic
  (subtract one month, handle month/year rollover) is exactly the kind of small-but-easy-to-get-
  wrong computation an LLM shouldn't be trusted to do reliably — same class of problem as SQL
  correctness itself, which is why this project validates rather than trusts throughout.
- **Fix, round 1 (insufficient on its own):** `app/sql_generator.py`'s `_relative_date_hints()`
  computes "today", "yesterday", "this/last month", "last 7/30 days", "this/last year" as ready
  `BETWEEN` literals in deterministic Python (stdlib `datetime`), placed early in the system
  prompt. Re-tested: **still failed**, reverting to the original September-2023 symptom even
  though the correct range was verified present in the prompt (checked directly — the hint text
  was exactly right). The fact was stated once, early, before the long schema/column listing,
  and evidently didn't survive to generation time.
- **Fix, round 2 (resolved):** repeated the same pre-computed date block immediately next to
  the question in the *user* prompt, not just earlier in the system prompt — proximity to the
  question matters more than where the fact first appears. Re-tested: **12/12 passed**,
  including this question. Regression tests:
  `scripts/test_sql_generator.py::TestRelativeDateHints` (3 cases, including the January
  rollover trap) and `test_date_hints_are_repeated_next_to_the_question_not_only_in_system_prompt`
  (would have caught round 1's insufficiency).

## Harness bugs (not app bugs, but worth recording — same discipline)
- **`scripts/run_eval.py` hardcoded `sql=None` in its own error handler**, discarding the
  actual generated SQL for every `ERROR`-status question and making #9/#10/#11 impossible to
  diagnose from the first eval run's output alone. Fixed by capturing `sql` in an outer-scope
  variable before the fallible calls, only overwritten by the exception path when it's still
  `None`. A reminder that the eval tooling needs the same care as the app it's testing.
- **Golden question wording (`reference/eval/golden_answers.json` #5/#6) was ambiguous**: "how
  many GRNs" could mean line items or distinct GRN documents (`COUNT(DISTINCT GRNNO)`), and the
  model's document-count reading wasn't wrong, my question was underspecified. Reworded to "GRN
  line items" to match the verified golden SQL. Open question for Tarun: which does "how many
  GRNs" mean in real usage — worth confirming since a future question phrased that way will hit
  the same ambiguity in reverse.

## Open, not yet fixed
- **"Top N" phrasing doesn't guarantee exactly N rows returned.** The system prompt tells the
  model not to write its own row-limiting clause (so it can't accidentally use 12c `FETCH
  FIRST` on this 11g database) — but for #3's retest the model added its own correct 11g
  `ROWNUM <= 5` subquery anyway and got it right, so this may already be self-resolving in
  practice. Not confirmed across enough questions yet to close; watch for cases where "top N"
  returns the default `SQL_MAX_ROWS` (100) instead of N.
