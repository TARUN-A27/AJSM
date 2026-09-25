import unittest

from app.schema_context import build_schema_context

EXPECTED_TABLES = {
    "PURCHASEORDER", "GRN", "INVOICEGRN", "ISSUE", "MRS", "MRS_TEMP",
    "ITEMSTOCK", "INVITEMS", "PARTYMASTER", "DEPT", "UNIT", "PLACE", "STATE", "COUNTRY",
}


class TestSchemaContext(unittest.TestCase):
    def test_contains_all_14_working_set_tables(self):
        context = build_schema_context()
        for table in EXPECTED_TABLES:
            self.assertIn(table, context, f"{table} missing from schema context")

    def test_contains_key_quirks(self):
        context = build_schema_context()
        self.assertIn("YYYYMMDD", context)
        self.assertIn("ROWNUM", context)
        self.assertIn("GOODSTYPECODE = 2", context)

    def test_item_join_column_naming_is_documented(self):
        # This is the single most common source of a wrong-join bug — must be explicit.
        context = build_schema_context()
        self.assertIn("ITEM_CODE", context)
        self.assertIn("ITEMCODE", context)

    def test_supplier_join_column_naming_is_documented(self):
        # Real failure hit against qwen3:14b (fix.md #2): model invented "SUPPLIERCODE"
        # instead of the real SUP_CODE column. Must be explicit, not just present in the
        # raw column list, since the model hallucinated past that once already.
        context = build_schema_context()
        self.assertIn("SUP_CODE", context)
        self.assertIn("SUPPLIERCODE", context)  # named as the wrong answer, to rule it out

    def test_schema_qualification_is_required(self):
        # Real failure (fix.md #2): unqualified ITEMSTOCK raised ORA-00942 (table not found).
        context = build_schema_context()
        self.assertIn("fully qualify", context.lower())

    def test_uppercase_text_matching_is_documented(self):
        # Real failure (fix.md #6): LIKE '%yarn%' matched 0 rows against real data (stored as
        # 'YARN'), silently returning NULL instead of an answer or an error.
        context = build_schema_context()
        self.assertIn("UPPER(", context)
        self.assertIn("case-sensitive", context.lower())

    def test_consumption_maps_to_issue_not_purchaseorder(self):
        # Real failure (fix.md #7, from the first eval run): "how much cost was consumed"
        # generated SQL against PURCHASEORDER.NET instead of ISSUE.ISSUEVALUE — the model
        # defaulted to the most-detailed table instead of the one the question is about.
        context = build_schema_context()
        self.assertIn("ISSUEVALUE", context)
        self.assertIn("consum", context.lower())

    def test_issue_quantity_vs_value_distinction_is_documented(self):
        # Real failure (eval run 3, fix.md #7 follow-up): "how much was issued" (a quantity
        # question) got mapped to SUM(ISSUEVALUE) instead of SUM(QTY) once the consumption
        # rule above existed — the first version of that rule didn't distinguish quantity
        # phrasing from cost phrasing, so it over-applied ISSUEVALUE to every "issued"
        # question. Must explicitly say both directions, not just that ISSUEVALUE exists.
        context = build_schema_context()
        self.assertIn("SUM(QTY)", context)
        self.assertIn("SUM(ISSUEVALUE)", context)


if __name__ == "__main__":
    unittest.main()
