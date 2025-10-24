
from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict
from datetime import datetime

class Event(BaseModel):
    topic: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    timestamp: str
    source: str = Field(min_length=1)
    payload: Dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def validate_ts(cls, v: str):
        try:
            datetime.fromisoformat(v.replace("Z","+00:00"))
        except Exception as e:
            raise ValueError("timestamp must be ISO8601") from e
        return v
