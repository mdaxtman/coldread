"""Lazy-initialized Supabase client singleton."""

from supabase import Client, create_client

from config import get_supabase_service_key, get_supabase_url

_client: Client | None = None


def get_client() -> Client:
    """Return the shared Supabase client, creating it on first call."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = create_client(get_supabase_url(), get_supabase_service_key())
    return _client
