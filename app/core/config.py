"""Application settings, loaded once from the .env file in the project root."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def require_env(name: str) -> str:
    """Return an environment variable, or fail with a clear message."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is missing. Add it to your .env file.")
    return value


ADMIN_DATABASE_URL = require_env("ADMIN_DATABASE_URL")