import unittest

from app.sql_safety import SQLSafetyError, add_oracle_row_limit, validate_select_only


class TestValidateSelectOnly(unittest.TestCase):
    def test_allows_plain_select(self):
        validate_select_only("SELECT * FROM INVENTORY.PURCHASEORDER")

    def test_allows_with_select(self):
        validate_select_only("WITH x AS (SELECT 1 FROM DUAL) SELECT * FROM x")

    def test_blocks_delete(self):
        with self.assertRaises(SQLSafetyError):
            validate_select_only("DELETE FROM INVENTORY.PURCHASEORDER")

    def test_blocks_update(self):
        with self.assertRaises(SQLSafetyError):
            validate_select_only("UPDATE INVENTORY.PURCHASEORDER SET STATUS = 1")

    def test_blocks_drop(self):
        with self.assertRaises(SQLSafetyError):
            validate_select_only("DROP TABLE INVENTORY.PURCHASEORDER")

    def test_blocks_stacked_statements(self):
        with self.assertRaises(SQLSafetyError):
            validate_select_only(
                "SELECT * FROM INVENTORY.PURCHASEORDER; DELETE FROM INVENTORY.PURCHASEORDER"
            )

    def test_blocks_disallowed_schema(self):
        with self.assertRaises(SQLSafetyError):
            validate_select_only("SELECT * FROM HRDNEW.CURRENTATTENDANCE")

    def test_blocks_empty(self):
        with self.assertRaises(SQLSafetyError):
            validate_select_only("")


class TestAddOracleRowLimit(unittest.TestCase):
    def test_wraps_with_rownum_not_fetch_first(self):
        wrapped = add_oracle_row_limit("SELECT * FROM INVENTORY.PURCHASEORDER", max_rows=50)
        self.assertIn("ROWNUM <= 50", wrapped)
        self.assertNotIn("FETCH FIRST", wrapped.upper())

    def test_rejects_unsafe_sql_before_wrapping(self):
        with self.assertRaises(SQLSafetyError):
            add_oracle_row_limit("DELETE FROM INVENTORY.PURCHASEORDER")


if __name__ == "__main__":
    unittest.main()
