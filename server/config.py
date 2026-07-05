import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DEFAULT_CORS_ORIGIN = "http://localhost:5173"


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


def get_supabase_anon_key() -> str:
    """Return the Supabase anon (public) key.

    Multi-user fork: use this key instead of the service key so that
    Row Level Security policies are enforced per-request.
    """
    return _require("SUPABASE_ANON_KEY")


DEFAULT_USER_ID: str = os.environ.get("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")


def get_cors_origins() -> list[str]:
    """Return the browser origins allowed to call the API.

    Comma-separated `CORS_ORIGINS` env var; defaults to the Vite dev server.
    Never use "*" — a wildcard lets any site the user visits drive the full
    API cross-origin, and it is invalid to pair with credentialed requests
    (which the multi-user fork will add). Set this explicitly in production.

    A literal "*" entry is defensively dropped (with a warning) so a
    misconfigured env can never silently reintroduce the wildcard; if that
    leaves no valid origin, we fall back to the dev-server default rather
    than an empty allowlist.
    """
    raw = os.environ.get("CORS_ORIGINS", _DEFAULT_CORS_ORIGIN)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        logger.warning('CORS_ORIGINS contains "*"; dropping it — set explicit origins instead.')
        origins = [origin for origin in origins if origin != "*"]
    return origins or [_DEFAULT_CORS_ORIGIN]


# Pipeline model. claude-sonnet-4-20250514 retired 2026-06-15; claude-sonnet-5
# is Anthropic's documented drop-in replacement (same $3/$15 per-MTok sticker;
# intro pricing $2/$10 through 2026-08-31).
PIPELINE_MODEL: str = "claude-sonnet-5"
