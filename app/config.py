"""
Loads .env from AJSMGPT_ENV_FILE if set, otherwise falls back to python-dotenv's
default search (cwd and parents). Keeps secrets out of the project directory in
production — see plan.md deployment notes.
"""

import os

from dotenv import load_dotenv

load_dotenv(os.getenv("AJSMGPT_ENV_FILE") or None)
