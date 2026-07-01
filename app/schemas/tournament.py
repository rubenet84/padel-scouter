import re
from datetime import date as DateType, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TournamentCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Tournament name")
    date: DateType
    fep_points: int | None = Field(default=0, ge=0, le=99999)
    player_id: Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def strip_html(cls, v: str) -> str:
        return re.sub(r"<[^>]*>", "", v).strip()


class TournamentUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    date: Optional[DateType] = None
    fep_points: Optional[int] = Field(default=None, ge=0, le=99999)

    @field_validator("name")
    @classmethod
    def strip_html(cls, v: str) -> str:
        if v is None:
            return v
        return re.sub(r"<[^>]*>", "", v).strip()


class TournamentPublicSchema(BaseModel):
    id: UUID
    name: str
    date: DateType
    fep_points: int | None
    owner_id: UUID
    player_id: UUID | None = None
    created_at: datetime
    match_count: int = 0

    model_config = {"from_attributes": True}
