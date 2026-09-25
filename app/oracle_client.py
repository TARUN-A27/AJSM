import logging
import os
import time
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import TypeAlias

import oracledb

import app.config  # noqa: F401 — loads .env before the os.getenv() calls below
from app.sql_safety import add_oracle_row_limit, validate_select_only

logger = logging.getLogger("ajsmgpt.oracle")

ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_DSN = os.getenv("ORACLE_DSN")
ORACLE_CLIENT_LIB_DIR = os.getenv("ORACLE_CLIENT_LIB_DIR")
SQL_MAX_ROWS = max(1, min(int(os.getenv("SQL_MAX_ROWS", "100")), 1000))
ORACLE_QUERY_TIMEOUT_MS = max(
    1000,
    min(int(os.getenv("ORACLE_QUERY_TIMEOUT_MS", "30000")), 120000),
)
ORACLE_CONNECT_TIMEOUT_SECONDS = max(
    1,
    min(int(os.getenv("ORACLE_CONNECT_TIMEOUT_SECONDS", "10")), 60),
)

OracleBindValue: TypeAlias = str | int | float | bool | Decimal | date | datetime | None


class OracleUnavailableError(RuntimeError):
    """The database could not be reached within the configured boundary."""


class OracleExecutionError(RuntimeError):
    """Oracle rejected or could not complete the safe SELECT."""


_oracle_client_initialized = False


def init_oracle_client_once():
    global _oracle_client_initialized

    if _oracle_client_initialized:
        return

    if ORACLE_CLIENT_LIB_DIR:
        oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_LIB_DIR)

    _oracle_client_initialized = True


def get_connection():
    init_oracle_client_once()

    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
        tcp_connect_timeout=ORACLE_CONNECT_TIMEOUT_SECONDS,
        retry_count=0,
    )


def _safe_database_error(exc: oracledb.DatabaseError) -> RuntimeError:
    error = exc.args[0] if exc.args else None
    code = getattr(error, "code", None)
    unavailable_codes = {
        1012, 1033, 1034, 1089, 1090, 1092, 12154, 12505, 12514,
        12516, 12518, 12520, 12521, 12528, 12537, 12541, 12543,
        12545, 12547, 12560, 12570, 12571, 3135,
    }
    if code in unavailable_codes:
        return OracleUnavailableError("Oracle is unavailable.")
    return OracleExecutionError("Oracle could not execute the safe query.")


def run_safe_select(
    sql: str,
    binds: Mapping[str, OracleBindValue] | None = None,
    *,
    enforce_row_limit: bool = True,
):
    """
    Runs SELECT-only SQL safely: blocks write/DDL/PLSQL commands, applies a row limit.
    Read-only is also enforced at the DB level by the `ajsmgpt_ro` account — this is
    defense in depth, not the only guarantee.
    """

    started = time.time()

    validate_select_only(sql)
    safe_sql = add_oracle_row_limit(sql, max_rows=SQL_MAX_ROWS) if enforce_row_limit else sql

    conn = None
    cur = None
    try:
        conn = get_connection()
        conn.call_timeout = ORACLE_QUERY_TIMEOUT_MS
        cur = conn.cursor()
        cur.execute(safe_sql, dict(binds or {}))

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        elapsed_ms = int((time.time() - started) * 1000)
        logger.info("query executed rows=%d elapsed_ms=%d", len(rows), elapsed_ms)

        return {
            "sql": safe_sql,
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "elapsed_ms": elapsed_ms,
        }

    except oracledb.DatabaseError as exc:
        raise _safe_database_error(exc) from None

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
