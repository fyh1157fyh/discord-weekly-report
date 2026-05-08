from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.date_range import previous_full_week


def test_previous_full_week_uses_monday_boundaries() -> None:
    week = previous_full_week(
        timezone=ZoneInfo("Asia/Shanghai"),
        now=datetime(2026, 5, 6, 12, tzinfo=ZoneInfo("Asia/Shanghai")),
    )

    assert week.start_at.isoformat() == "2026-04-27T00:00:00+08:00"
    assert week.end_at.isoformat() == "2026-05-04T00:00:00+08:00"
    assert week.label == "2026-W18"
