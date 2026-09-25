import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.answer_summary import summarize
from app.oracle_client import OracleExecutionError, OracleUnavailableError, run_safe_select
from app.report import shape_result
from app.sql_generator import SQLGenerationError, generate_sql
from app.sql_safety import SQLSafetyError, validate_select_only

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ajsmgpt")

app = FastAPI(title="AJSMGPT")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # single internal company app, no auth yet — CLAUDE.md §5
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    sql: str
    view: str
    columns: list[str]
    rows: list[list]
    row_count: int
    summary: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        sql = generate_sql(request.question)
        validate_select_only(sql)  # defense in depth, oracle_client also validates
        result = run_safe_select(sql)
    except (SQLGenerationError, SQLSafetyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OracleUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OracleExecutionError as exc:
        logger.warning("query failed for question=%r sql=%r", request.question, sql)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    shaped = shape_result(result)
    summary = summarize(request.question, shaped["columns"], shaped["rows"])

    return AskResponse(
        question=request.question,
        sql=result["sql"],
        view=shaped["view"],
        columns=shaped["columns"],
        rows=shaped["rows"],
        row_count=shaped["row_count"],
        summary=summary,
    )
