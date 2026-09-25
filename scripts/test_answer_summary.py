import unittest
from unittest.mock import patch

from app.answer_summary import summarize


class TestSummarize(unittest.TestCase):
    def test_real_data_is_passed_to_the_model(self):
        with patch("app.answer_summary.chat") as mock_chat:
            mock_chat.return_value = "Total stock of item A12001392 is 3 units."
            result = summarize("total stock of A12001392", ["TOTALSTOCK"], [[3]])

        user_prompt = mock_chat.call_args[0][1]
        self.assertIn("3", user_prompt)
        self.assertIn("TOTALSTOCK", user_prompt)
        self.assertEqual(result, "Total stock of item A12001392 is 3 units.")

    def test_empty_rows_are_flagged_distinctly_not_silently_omitted(self):
        # The model must be told explicitly that there are no rows, rather than being
        # handed an empty list it might paper over or hallucinate a value for.
        with patch("app.answer_summary.chat") as mock_chat:
            mock_chat.return_value = "No matching records were found."
            summarize("stock of a nonexistent item", ["TOTALSTOCK"], [])

        user_prompt = mock_chat.call_args[0][1]
        self.assertIn("no rows returned", user_prompt.lower())


if __name__ == "__main__":
    unittest.main()
