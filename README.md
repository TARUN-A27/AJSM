# AJSMGPT

A private assistant for a company's own data, behind one search bar:

1. **Ask the database.** Type a question in plain English. The app writes a read-only Oracle SQL query, checks it,
   runs it, and shows a table, a chart or a short summary. *(built, paused)*
2. **Ask your files.** Upload PDFs, scans, photos, Word / Excel / PowerPoint files, mail, archives and more, then ask
   questions about them. Every answer comes with the exact quote it rests on, or the app says it did not find it.
   *(in active development, running internally)*

Everything runs on the company's own server: local language models ([Ollama](https://ollama.com)), a local vector
store ([Qdrant](https://qdrant.tech)) and local file storage. No cloud API is called and no document leaves the machine.

## Status

| Phase | What | State |
|---|---|---|
| 1 | Plain-English question → Oracle SQL → table / chart / summary | built, in this repository; paused |
| 2 | Questions over uploaded files, with quotes or a refusal | in development; its code is not in this repository yet |

Phase 2 is being cleaned of internal references before it is published here. Its design is described below and in
[`plan.md`](plan.md).

## Principles

- **A wrong answer is worse than no answer.** Checks that run in code come before trust in the model.
- **Read-only.** The database account can only `SELECT`, and every generated query is validated as a single `SELECT`
  before it runs (defence in depth).
- **Local.** Models, vectors and files stay on the company's server. Nothing is fetched or sent at run time.
- **Keep company data out of the repository.** Credentials live in a local `.env` that is never committed; internal
  schema studies and question banks stay in the git-ignored `reference/` folder.

## How the database part works

```text
question → prompt (question + schema + documented quirks) → LLM writes Oracle SQL
         → SELECT-only validation → read-only execution → table / chart / summary
```

There are no templates and no stored queries: the model writes the SQL fresh for every question, and a hand-written
evaluation set (kept local) measures it. Schema knowledge lives in one place, [`app/schema_context.py`](app/schema_context.py).

## How the files part works (design)

```text
upload → read → split into chunks → embed → store (per set of files)
question → find the best excerpts of each file → the model answers with quotes → checks → answer or refusal
```

- **Reading.** PDFs page by page; scanned pages and photos by a local vision model, with a second reader that
  confirms the digits; Word, Excel and PowerPoint directly; legacy and OpenDocument formats (`.doc`, `.xls`, `.ppt`,
  `.odt`, `.ods` …) converted offline by LibreOffice; mail; text under any extension; `.zip` files unpacked into files
  of the same set.
- **Answering.** The model replies with the quotes it relies on and a short answer. Code then checks that every quote
  is an exact copy of the excerpt it names, that every number in the answer appears in a quote, that a code named in
  the question (a PO or invoice number) is in the cited excerpt, and that no digit read from a scan is unconfirmed.
  A reply that fails a check the model can mend is retried with the problem named; one that still fails becomes
  "Not found in the uploaded files." A question over several files that is refused is asked again file by file.
- **Feedback.** Under every answer a thumbs up / down records whether the answer was right, and the ratings can be
  replayed as a regression test.

## Repository layout

```text
app/          backend (FastAPI): llm_client, oracle_client, sql_safety, schema_context, sql_generator, report
frontend/     React + TypeScript + Vite; built to frontend/dist and served by the backend
scripts/      evaluation harness and unit tests
plan.md       decisions, phases and next steps
fix.md        open failures with root cause and fix
fixlog.md     append-only working log
CLAUDE.md     rules for working on the project
SKILL.md      working conventions and how to run things
```

## Running the database part locally

You need Python 3.12, a current Node.js LTS, an Oracle client library, and an Ollama server with a chat model.

```bash
python3 -m venv venv && ./venv/bin/python -m pip install -r requirements.txt
cp .env.example .env            # fill it in locally; it is git-ignored, never commit it
./venv/bin/python -m uvicorn app.main:app --port 8000
cd frontend && npm install && npm run build   # the backend serves frontend/dist
```

Settings are read from the environment; the variable names are in [`.env.example`](.env.example).

Tests:

```bash
PYTHONPATH=. ./venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
```

## Contributing and safety

Read [`CLAUDE.md`](CLAUDE.md) first. In short: never commit `.env` or any company data, never bypass the SELECT-only
validation, never add DML, DDL or PL/SQL, and keep every document, embedding and answer on the company's own
infrastructure.
