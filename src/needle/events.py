"""
needle.events - Real-time event definitions, frames, options, and urgency tiers.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EventUrgency(StrEnum):
    """Urgency / Priority tiers for real-time events."""

    AMBIENT = "ambient"  # Background telemetry, periodic status (urgency ~0.1)
    NOTICE = "notice"  # Standard state changes, task completion, info (urgency ~0.3)
    ALERT = "alert"  # High priority alerts, warnings, tension sparks (urgency ~0.7)
    FLASH = "flash"  # Critical errors, crashes, immediate emergency (urgency 1.0)

    @property
    def numeric(self) -> float:
        mapping = {
            EventUrgency.AMBIENT: 0.1,
            EventUrgency.NOTICE: 0.3,
            EventUrgency.ALERT: 0.7,
            EventUrgency.FLASH: 1.0,
        }
        return mapping.get(self, 0.3)

    @classmethod
    def from_value(cls, val: Any) -> EventUrgency:
        if isinstance(val, EventUrgency):
            return val
        s = str(val or "").lower().strip()
        if s in {"flash", "crit", "critical", "emerg", "emergency", "1.0", "1"}:
            return EventUrgency.FLASH
        if s in {"alert", "warning", "warn", "0.7", "0.8", "0.9"}:
            return EventUrgency.ALERT
        if s in {"ambient", "debug", "trace", "0.1", "0.2"}:
            return EventUrgency.AMBIENT
        return EventUrgency.NOTICE


@dataclass(slots=True)
class EventOptions:
    """Options and payload configuration for publishing events."""

    data: Any = None
    summary: str = ""
    urgency: EventUrgency = EventUrgency.NOTICE
    retained_slot: str | None = None
    retained_value: Any = None

    def __post_init__(self) -> None:
        if self.urgency is None:
            self.urgency = EventUrgency.NOTICE
        elif not isinstance(self.urgency, EventUrgency):
            self.urgency = EventUrgency.from_value(self.urgency)


from pydantic import BaseModel, Field


class EventFrame(BaseModel):
    """Standardized, self-describing immutable event packet."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    topic: str
    source: str = "system"
    urgency: EventUrgency = EventUrgency.NOTICE
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    process_id: int = Field(default_factory=os.getpid)
    retained_slot: str | None = None
    retained_value: Any = None


__all__ = ["EventFrame", "EventOptions", "EventUrgency"]
