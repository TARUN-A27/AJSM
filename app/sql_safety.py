import os
import re

import app.config  # noqa: F401 — loads .env before the os.getenv() call below

BLOCKED_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "EXEC",
    "EXECUTE",
    "CALL",
    "BEGIN",
    "DECLARE",
]


ORACLE_SCHEMAS = os.getenv("ORACLE_SCHEMAS", "INVENTORY,SCM")
ALLOWED_SCHEMAS = {
    schema.strip().upper()
    for schema in ORACLE_SCHEMAS.split(",")
    if schema.strip()
}

KNOWN_SCHEMAS = {"ADMIN", "HRDNEW", "INSUR", "INVENTORY", "SCM"}


class SQLSafetyError(Exception):
    pass


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip())


def remove_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def validate_select_only(sql: str) -> str:
    """
    Strict validator for AJSMGPT Oracle queries.

    Rules:
    1. Only SELECT is allowed.
    2. No INSERT/UPDATE/DELETE/MERGE/DDL/TCL/PLSQL.
    3. Only the configured schemas (ORACLE_SCHEMAS) are allowed.
    4. Multiple statements are blocked.
    5. Semicolon is removed safely at the end only.
    """

    if not sql or not sql.strip():
        raise SQLSafetyError("SQL is empty.")

    cleaned = remove_sql_comments(sql)
    cleaned = normalize_sql(cleaned)

    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    if ";" in cleaned:
        raise SQLSafetyError("Multiple SQL statements are not allowed.")

    upper_sql = cleaned.upper()

    # Allow top-level SELECT or WITH ... SELECT queries
    if not (upper_sql.startswith("SELECT ") or upper_sql.startswith("WITH ")):
        raise SQLSafetyError("Only SELECT (or WITH ... SELECT) queries are allowed.")

    for keyword in BLOCKED_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper_sql):
            raise SQLSafetyError(f"Blocked SQL keyword detected: {keyword}")

    # Block access to any known schema not in allowed schemas.
    if ALLOWED_SCHEMAS:
        forbidden_schemas = KNOWN_SCHEMAS - ALLOWED_SCHEMAS
        if forbidden_schemas:
            forbidden_pattern = r"\b(" + "|".join(sorted(forbidden_schemas)) + r")\s*\."
            if re.search(forbidden_pattern, upper_sql):
                raise SQLSafetyError(
                    f"Schema not allowed. Only schemas {sorted(ALLOWED_SCHEMAS)} are permitted."
                )

    return cleaned


def add_oracle_row_limit(sql: str, max_rows: int = 100) -> str:
    """
    Wrap query with an Oracle 11g-compatible ROWNUM row limit (no FETCH FIRST on 11.2).
    """

    safe_sql = validate_select_only(sql)

    return f"""
SELECT *
FROM (
    {safe_sql}
)
WHERE ROWNUM <= {max_rows}
""".strip()
