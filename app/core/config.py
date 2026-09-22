"""Settings loaded from the .env file in the project root."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is missing. Add it to your .env file.")
    return value


ADMIN_DATABASE_URL = require_env("ADMIN_DATABASE_URL")      # setup scripts only
ANALYST_DATABASE_URL = require_env("ANALYST_DATABASE_URL")  # the agent's connection
GROQ_API_KEY = require_env("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RESULT_ROWS = 200