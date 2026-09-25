"""
Turns a natural-language question into Oracle SQL. Pure generation — no templates,
no pre-written queries (see CLAUDE.md §2). The LLM sees the real schema + quirks
every time and writes SQL fresh.
"""

import re
from datetime import date, timedelta

from app.llm_client import chat
from app.schema_context import build_schema_context

SYSTEM_PROMPT = """You are a SQL generator for an Oracle 11g database. You are given the exact \
schema and known data quirks of the tables you may query. Write one single Oracle SELECT \
statement that answers the user's question.

Today's date is {today} ({today_yyyymmdd} in this database's date format).

Do not compute relative date ranges yourself — date arithmetic (especially month/year
boundaries) is a common source of off-by-one errors. Use these already-computed ranges
exactly as given whenever the question matches one of these phrases:
{date_ranges}
For any other relative phrase not listed above, reason from today's date above, but double
-check month/year rollover by hand (e.g. "last month" from January is December of the
*previous* year, not month 0).

Rules:
- Respond with the SQL statement and nothing else. No explanation, no reasoning, no markdown
  code fences, no prose before or after — your entire response must be the SQL statement.
- Never answer from your own knowledge, memory, or an approximate/example figure mentioned
  below, even if you believe you already know the answer. Always write a query that computes
  the real, exact, current answer from the database. Any approximate numbers in the schema
  notes below are for reasoning about query cost only — they are never a valid final answer.
- SELECT statements only. Never write INSERT/UPDATE/DELETE/DDL.
- Only use tables and columns listed in the schema below. Never invent a column.
- Follow every data-quirk rule below exactly (especially: dates are strings, not DATE values).
- Do not add your own row-limiting clause (no ROWNUM, no FETCH FIRST) — the caller adds one.

{schema_context}"""

# Matches a fenced ```sql ... ``` or ``` ... ``` block anywhere in the response — the model
# sometimes answers in prose with the real query embedded in a fence rather than replying
# with pure SQL despite the system prompt (fix.md #1). Falls back to stripping a fence that
# wraps the whole response, then to the raw text, so this only narrows what's returned, never
# rejects a plain unfenced SQL reply.
_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class SQLGenerationError(RuntimeError):
    pass


def _yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _relative_date_hints(today: date) -> str:
    """
    Pre-computed date ranges for the phrases actually seen in real questions (question_bank_v1
    families). Deterministic Python arithmetic instead of LLM date math — fix.md: "last month"
    was computed as the *current* month (Sept instead of Aug) when left to the model, even with
    today's date given. Handles month/year rollover correctly (Jan -> prior December).
    """
    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    yesterday = today - timedelta(days=1)
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    this_year_start = today.replace(month=1, day=1)
    last_year_start = today.replace(year=today.year - 1, month=1, day=1)
    last_year_end = today.replace(year=today.year - 1, month=12, day=31)

    return "\n".join([
        f'- "today" -> {_yyyymmdd(today)}',
        f'- "yesterday" -> {_yyyymmdd(yesterday)}',
        f'- "this month" -> BETWEEN {_yyyymmdd(this_month_start)!r} AND {_yyyymmdd(today)!r}',
        f'- "last month" -> BETWEEN {_yyyymmdd(last_month_start)!r} AND {_yyyymmdd(last_month_end)!r}',
        f'- "last 7 days" -> BETWEEN {_yyyymmdd(last_7_days)!r} AND {_yyyymmdd(today)!r}',
        f'- "last 30 days" -> BETWEEN {_yyyymmdd(last_30_days)!r} AND {_yyyymmdd(today)!r}',
        f'- "this year" -> BETWEEN {_yyyymmdd(this_year_start)!r} AND {_yyyymmdd(today)!r}',
        f'- "last year" -> BETWEEN {_yyyymmdd(last_year_start)!r} AND {_yyyymmdd(last_year_end)!r}',
    ])


def _extract_sql(text: str) -> str:
    text = text.strip()
    fenced = _FENCE_RE.search(text)
    if fenced:
        return fenced.group(1).strip()
    return re.sub(r"^```(?:sql)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()


def generate_sql(question: str) -> str:
    if not question or not question.strip():
        raise SQLGenerationError("Question is empty.")

    today = date.today()
    date_hints = _relative_date_hints(today)
    system_prompt = SYSTEM_PROMPT.format(
        schema_context=build_schema_context(),
        today=today.isoformat(),
        today_yyyymmdd=_yyyymmdd(today),
        date_ranges=date_hints,
    )
    # Repeated here, right next to the question, not just earlier in the system prompt: a
    # fact stated once before a long schema listing gets lost by generation time (fix.md
    # #13 follow-up — the model still fabricated a wrong date even with the correct range
    # given in the system prompt). Immediate proximity to the question is what actually
    # gets attended to.
    user_prompt = (
        f"(For reference if this question uses a relative date — today is {_yyyymmdd(today)}. "
        f"Pre-computed ranges:\n{date_hints}\n)\n\n{question}"
    )
    raw = chat(system_prompt, user_prompt, temperature=0.1)
    sql = _extract_sql(raw)

    if not sql:
        raise SQLGenerationError("Model returned no SQL.")

    return sql
