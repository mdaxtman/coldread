"""Request-scoped dependencies for the ColdRead API.

Multi-user fork: replace ``get_current_user_id`` with JWT extraction
from the Authorization header via Supabase Auth.
"""

from config import DEFAULT_USER_ID


def get_current_user_id() -> str:
    """Return the authenticated user's ID.

    Single-user mode: always returns DEFAULT_USER_ID.
    Multi-user fork: extract from JWT in the request's Authorization header
    and return the authenticated user's ``sub`` claim.
    """
    return DEFAULT_USER_ID
