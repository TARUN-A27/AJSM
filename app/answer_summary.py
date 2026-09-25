"""
Turns a verified Oracle result into one plain-language sentence. The LLM only phrases
data that has already been fetched — it is given the exact rows and told never to add
a number or fact that isn't there, so this can't introduce a wrong answer, only a
badly-worded one.
"""

from app.llm_client import chat

SYSTEM_PROMPT = """You answer a business question in exactly one short, natural sentence, \
using ONLY the exact data given below — never state a number, name, or fact that isn't in \
that data, and never guess or estimate.

If the data is empty (no rows), say in one natural sentence that no matching records were \
found for the question — do not guess why, do not apologize at length, just state it plainly.

Respond with exactly one sentence. No preamble, no markdown, no explanation of the query."""


def summarize(question: str, columns: list[str], rows: list[list]) -> str:
    if not rows:
        data_block = "(no rows returned)"
    else:
        data_block = f"Columns: {columns}\nRows: {rows}"

    user_prompt = f"Question: {question}\n\n{data_block}"
    reply = chat(SYSTEM_PROMPT, user_prompt, temperature=0.1, think=False, num_predict=120)
    return reply.strip()
