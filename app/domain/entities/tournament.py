from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Tournament:
    id: UUID = field(default_factory=uuid4)
    name: str
    date: date
    fep_points: int | None = 0
    owner_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
