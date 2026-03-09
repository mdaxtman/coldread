"""ColdRead API routes."""

from fastapi import APIRouter

from db import narratives
from models import NarrativeResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Narratives (read-only — seeded in DB, not created via API)
# ---------------------------------------------------------------------------


@router.get("/narratives", response_model=list[NarrativeResponse])
def list_narratives() -> list[NarrativeResponse]:
    rows = narratives.list_narratives()
    return [NarrativeResponse(**r) for r in rows]
