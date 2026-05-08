from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class WeekRange:
    start_at: datetime
    end_at: datetime
    label: str


def previous_full_week(*, timezone: ZoneInfo, now: datetime | None = None) -> WeekRange:
    current = (now or datetime.now(timezone)).astimezone(timezone)
    today_midnight = datetime.combine(current.date(), time.min, tzinfo=timezone)
    this_monday = today_midnight - timedelta(days=today_midnight.weekday())
    last_monday = this_monday - timedelta(days=7)
    return WeekRange(start_at=last_monday, end_at=this_monday, label=f"{last_monday:%G-W%V}")
