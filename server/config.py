import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


# Loaded lazily by modules that need them — not at import time.
# This allows tests to run without all env vars present.
def get_anthropic_api_key() -> str:
    return _require("ANTHROPIC_API_KEY")


def get_supabase_url() -> str:
    return _require("SUPABASE_URL")


def get_supabase_service_key() -> str:
    return _require("SUPABASE_SERVICE_KEY")


DEFAULT_USER_ID: str = os.environ.get("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
