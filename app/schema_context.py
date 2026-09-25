"""
Builds the schema + business-quirks context given to the LLM on every question.

The working set is only 14 tables, so the whole schema fits directly in the prompt —
no RAG/retrieval layer (see plan.md). Column data comes from
reference/working_set_schema.json (pulled from AJSMGPT_v1's verified Oracle profiling,
2026-09-22 — not re-derived). The quirks/business-definitions text below is distilled
from reference/ORACLE_SCHEMA_STUDY_2026-09-22.md sections 5-6, which reverse-engineered
real PL/SQL (GETORDERPENDINGSTATUS etc.) rather than guessing at what status columns mean.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

SCHEMA_PROFILE_PATH = os.getenv(
    "SCHEMA_PROFILE_PATH",
    str(Path(__file__).resolve().parent.parent / "reference" / "working_set_schema.json"),
)

# Distilled from ORACLE_SCHEMA_STUDY_2026-09-22.md §5 (data conventions), §6.1 (verified
# business definitions from ERP PL/SQL, not inferred). Keep this in sync with that doc if
# a new quirk is discovered — see SKILL.md.
QUIRKS = """
Schema membership — every table below belongs to exactly one of these two schemas. Get this
wrong and the table simply doesn't exist (ORA-00942), even though the table name is real:
  INVENTORY: PURCHASEORDER, GRN, INVOICEGRN, ISSUE, MRS, MRS_TEMP, ITEMSTOCK, INVITEMS, DEPT, UNIT
  SCM: PARTYMASTER, PLACE, STATE, COUNTRY
(Also shown per-table below, but check this list first — it's easy to guess wrong on ISSUE/MRS/
MRS_TEMP specifically, since PARTYMASTER's schema is SCM and it's easy to overgeneralize.)

Database facts (Oracle 11g EE 11.2.0.1.0 — a 2009-era database):
1. No `FETCH FIRST n ROWS ONLY` (12c syntax). Never write it. The app wraps every query in a
   ROWNUM limit automatically — do not add your own row-limiting clause.
2. Dates are TEXT, not DATE columns. ORDERDATE, MRSDATE, ISSUEDATE, GRNDATE are VARCHAR2(8)
   'YYYYMMDD'. Compare as strings: `ORDERDATE BETWEEN '20260101' AND '20261231'`. Never use
   TO_DATE(...) or a DATE literal on these columns — it raises ORA-01861. `ORDER BY ORDERDATE
   DESC` is safe (string sort works because the format is fixed-width YYYYMMDD).
3. No primary keys on most tables (574 of 696 database-wide). Uniqueness is by document number
   + block + serial (e.g. PURCHASEORDER: ORDERNO + ORDERBLOCK + SLNO). Don't assume an ID column
   exists or is meaningful for dedup.
4. ITEMSTOCK has multiple rows per item (per mill/HOD). A "stock of X" question must SUM(STOCK)
   grouped by item, not read a single row.
5. Status-shaped columns are usually NOT usable as a plain filter — most are numeric codes with
   undocumented meanings, and several are constant (STATUS, FLAG, POSTED are 0 on every row in
   several tables, including PURCHASEORDER.STATUS). Use the verified business definitions below
   instead of guessing what a status column value means.
6. Supplier = PARTYMASTER row WHERE GOODSTYPECODE = 2 (this is the ERP's own SUPPLIER view
   definition). PARTYMASTER also holds ~11.5k customers/others — always filter GOODSTYPECODE = 2
   for supplier questions.
7. Item names are not unique (407 duplicate ITEM_NAMEs across 41,862 items) and 29% of items are
   OBSOLETE = 1. A name-based item lookup can be genuinely ambiguous.
8. Item join column is named differently per table: ITEM_CODE (PURCHASEORDER, MRS), CODE (GRN,
   ISSUE), ITEMCODE (ITEMSTOCK). Always check the column list below for the right name — never
   guess a plausible-sounding name (e.g. ITEM_CODE is real, ITEMCODE is real on ITEMSTOCK only,
   but "ITEMCD" or "ITEM_ID" do not exist anywhere).
9. Supplier join column is SUP_CODE (PURCHASEORDER, GRN, ENQUIRY, RDC, WORKORDER, INVOICEGRN) ->
   PARTYMASTER.PARTYCODE. It is never called SUPPLIERCODE, SUPPLIER_CODE, or VENDOR_CODE — those
   columns do not exist. Always check the column list below rather than guessing a column name
   that merely sounds right.
10. Always fully qualify every table with its schema exactly as listed below (e.g.
    INVENTORY.ITEMSTOCK, SCM.PARTYMASTER) — an unqualified table name can resolve to the wrong
    object or fail to resolve at all depending on the connected account's search path.
11. PURCHASEORDER's "total value" column is NET (verified: never null on any row). Do NOT use
    BASIC for a total/value question even though the name sounds right — BASIC is NULL on 72%
    of rows (verified 2026-09-25 against live data; a prior schema study's "never null" claim
    for this specific column was wrong) and will silently produce NULL/undercounted sums.
12. Text/name columns (ITEM_NAME, PARTYNAME, and name columns generally) are stored in
    UPPERCASE. Oracle's LIKE is case-sensitive — a lowercase or mixed-case pattern silently
    matches zero rows instead of erroring (verified 2026-09-25: `ITEM_NAME LIKE '%yarn%'`
    matched 0 rows against real data; `LIKE '%YARN%'` matched 121). Always wrap both sides in
    UPPER() for any name-based text match: `UPPER(ITEM_NAME) LIKE UPPER('%yarn%')` — never
    assume the user's input casing matches the stored casing.
13. "Consumption" / "consumed" / "issued" means material actually used by a department — that
    is ISSUE, NOT PURCHASEORDER (purchasing and consuming are different real-world events on
    different tables — do not default to PURCHASEORDER just because it's the most detailed
    table). Within ISSUE, pick the column that matches what's actually being asked:
    "how much QTY / how many units / how much material was issued/consumed" -> SUM(QTY);
    "how much COST / VALUE / money was consumed" -> SUM(ISSUEVALUE). These give genuinely
    different numbers for the same item — check whether the question is asking about a
    quantity or a cost before picking the column, don't default to one for every phrasing.
14. Never add an underscore to a column name that doesn't have one in the listing below. This
    schema's naming is inconsistent by table, not by a general rule you can infer — ISSUENO is
    one word (not ISSUE_NO), SUP_CODE has an underscore, ITEMCODE on ITEMSTOCK does not. Copy
    the exact spelling from the column list below character-for-character; do not normalize it
    to a "cleaner" or more conventional-looking form.
15. Code/number-like columns (SUP_CODE, ITEM_CODE, ITEMCODE, PARTYCODE, GRNNO, ORDERNO, MRSNO,
    ISSUENO, etc.) are VARCHAR2 or NUMBER as shown in the column list — check the type before
    writing a literal. A VARCHAR2 code column needs a quoted string literal even when the value
    looks numeric (`SUP_CODE = '800967'`, never `SUP_CODE = 800967`) — Oracle raises ORA-01722
    ("invalid number") if you compare a text column to a bare numeric literal.

Verified business definitions (reverse-engineered from the ERP's own PL/SQL — safe to rely on):
- PO pending approval stage: on a PURCHASEORDER row, JMDORDERAPPROVAL/SOORDERAPPROVAL/
  IAORDERAPPROVAL all 0 -> pending at Stores Officer; SO=1,IA=0 -> pending at Internal Audit;
  SO=1,IA=1,JMD=0 -> pending at JMD; all 1 -> fully approved.
- Total stock of an item: SUM(ITEMSTOCK.STOCK) WHERE ITEMCODE = item (join to INVITEMS.ITEM_CODE),
  optionally filtered by MILLCODE.
- Last issue date of an item: MAX(ISSUE.ISSUEDATE) WHERE CODE = item.
- MRS pending: an MRS_TEMP row where RejectionStatus=0 AND StoresRejectionStatus=0 AND
  ItemDelete=0 AND isDelete=0 AND MrsFlag=1 AND (MillCode=0 OR MillCode IS NULL), AND there is
  NO matching row in MRS (LEFT JOIN MRS ON MRS.MrsNo=MRS_Temp.MrsNo AND MRS_Temp.SlNo=MRS.SlNo,
  keep only NULL matches) — i.e. never approved into MRS, or approved but no PO cut yet.
- "Order pending" (goods-receipt sense, distinct from approval-stage sense above): a
  PURCHASEORDER line with no matching GRN yet — GRN_PENDINGSTATUS itself is not a usable filter
  (only 7 rows have it set).

Approximate scale, for reasoning about query cost only — NEVER use these numbers as the answer
to a question, they are rough and go stale; always write a query to get the real, current,
exact figure: PURCHASEORDER ~178.7k lines, GRN ~204k, ISSUE ~413.6k, MRS ~177k, MRS_TEMP ~98k,
INVITEMS ~41.8k items, PARTYMASTER ~20k parties (~1,645 are actual suppliers).
""".strip()


@lru_cache(maxsize=1)
def _load_tables() -> list[dict]:
    with open(SCHEMA_PROFILE_PATH) as f:
        return json.load(f)


def _format_table(table: dict) -> str:
    lines = [f"{table['schema']}.{table['table']} (~{table['rows']} rows)"]
    for col in table["columns"]:
        nullable = "" if col["nullable"] else " NOT NULL"
        lines.append(f"  {col['name']} {col['type']}{nullable}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def build_schema_context() -> str:
    """Full prompt context: every working-set table's real columns + documented quirks."""
    tables = _load_tables()
    schema_block = "\n\n".join(_format_table(t) for t in sorted(tables, key=lambda t: t["table"]))
    return f"TABLES:\n\n{schema_block}\n\n{QUIRKS}"
