import unittest
from datetime import date
from unittest.mock import patch

from app.sql_generator import _extract_sql, _relative_date_hints, generate_sql


class TestExtractSql(unittest.TestCase):
    def test_plain_sql_passthrough(self):
        sql = "SELECT COUNT(*) FROM INVENTORY.PURCHASEORDER"
        self.assertEqual(_extract_sql(sql), sql)

    def test_whole_response_fenced(self):
        raw = "```sql\nSELECT COUNT(*) FROM INVENTORY.PURCHASEORDER\n```"
        self.assertEqual(_extract_sql(raw), "SELECT COUNT(*) FROM INVENTORY.PURCHASEORDER")

    def test_prose_with_embedded_fence(self):
        # The real failure mode hit against qwen3:14b (fix.md #1): model answers
        # conversationally and puts the actual query in a fence partway through.
        raw = (
            "Based on the schema, the total is approximately 178,700.\n\n"
            "```sql\nSELECT COUNT(*) FROM INVENTORY.PURCHASEORDER\n```\n\n"
            "This counts all lines with no filtering."
        )
        self.assertEqual(_extract_sql(raw), "SELECT COUNT(*) FROM INVENTORY.PURCHASEORDER")

    def test_unfenced_with_surrounding_whitespace(self):
        raw = "\n\n  SELECT 1 FROM DUAL  \n\n"
        self.assertEqual(_extract_sql(raw), "SELECT 1 FROM DUAL")


class TestGenerateSqlPrompt(unittest.TestCase):
    def test_todays_date_is_injected_into_the_prompt(self):
        # Real failure (fix.md #7): with no date anchor, the model guessed "last month" as
        # September 2023 for a question asked in 2026 — completely ungrounded. The system
        # prompt must carry the real current date so relative-date questions have something
        # real to compute from.
        with patch("app.sql_generator.chat") as mock_chat:
            mock_chat.return_value = "SELECT 1 FROM DUAL"
            generate_sql("how much was consumed last month?")

        system_prompt = mock_chat.call_args[0][0]
        today_str = date.today().strftime("%Y%m%d")
        self.assertIn(today_str, system_prompt)

    def test_date_hints_are_repeated_next_to_the_question_not_only_in_system_prompt(self):
        # Real failure (fix.md #13 follow-up): the date range was correctly computed and
        # present in the system prompt, but the model still fabricated a wrong date — the fact
        # was stated once, early, before a long schema listing, and got lost by generation
        # time. Repeating it immediately next to the question (the user prompt) is the fix;
        # this test would have caught the earlier version that only put it in the system
        # prompt and assumed that was enough.
        with patch("app.sql_generator.chat") as mock_chat:
            mock_chat.return_value = "SELECT 1 FROM DUAL"
            generate_sql("how much was consumed last month?")

        user_prompt = mock_chat.call_args[0][1]
        self.assertIn("how much was consumed last month?", user_prompt)
        self.assertIn(date.today().strftime("%Y%m%d"), user_prompt)


class TestRelativeDateHints(unittest.TestCase):
    def test_last_month_is_computed_not_left_to_the_model(self):
        # Real failure: even with today's date given, the model computed "last month" as the
        # *current* month (September instead of August) for today=2026-09-25. Date arithmetic
        # must be deterministic Python, not delegated to the LLM.
        hints = _relative_date_hints(date(2026, 9, 25))
        self.assertIn("'20260801' AND '20260831'", hints)
        self.assertNotIn("'20260901'", hints.split("last month")[1].split("\n")[0])

    def test_last_month_handles_january_year_rollover(self):
        # The trap case: "last month" from January must be December of the *previous* year,
        # not month 0 or month 13.
        hints = _relative_date_hints(date(2026, 1, 15))
        self.assertIn("'20251201' AND '20251231'", hints)

    def test_last_year_handles_full_year_range(self):
        hints = _relative_date_hints(date(2026, 9, 25))
        self.assertIn("'20250101' AND '20251231'", hints)


if __name__ == "__main__":
    unittest.main()
