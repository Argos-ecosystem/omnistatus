from typing import Any, Optional

from pydantic import BaseModel

class Event(BaseModel):
    source: str
    text: str            # event description
    score: Optional[float] = None  # risk level
    timestamp: Optional[str] = None  # ISO8601 string
    summary: Optional[str] = None
    event_count: Optional[int] = None
    avg_score: Optional[float] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    dedup_key: Optional[str] = None
    samples: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
