"""Pydantic models for ColdRead API request/response serialization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that serializes snake_case fields as camelCase in JSON responses."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class NarrativeResponse(CamelModel):
    id: str
    user_id: str
    title: str
    content: str
    category: str | None = None
    created_at: datetime
    updated_at: datetime
