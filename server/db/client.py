"""Lazy-initialized Supabase client singleton.

MULTI-USER FORK: Switch from the service role key to the anon key so that
Supabase Row Level Security (RLS) policies are enforced.  Either:
  - Use ``get_supabase_anon_key()`` here and write RLS policies on every
    table scoped to ``auth.uid() = user_id``, OR
  - Use per-request JWTs via ``supabase.auth.set_session(token)`` so each
    request runs with the authenticated user's privileges.
"""

from supabase import Client, create_client

from config import get_supabase_service_key, get_supabase_url

_client: Client | None = None


def get_client() -> Client:
    """Return the shared Supabase client, creating it on first call.

    Uses the service role key (bypasses RLS).  This is intentional for the
    single-user portfolio app.  The multi-user fork must switch to the anon
    key + RLS or per-request JWTs — see module docstring.
    """
    global _client  # noqa: PLW0603
    if _client is None:
        _client = create_client(get_supabase_url(), get_supabase_service_key())
    return _client
