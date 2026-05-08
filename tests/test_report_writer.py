from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.models import AnalyzedPost, CollectedPost, ReactionStats, WeeklyReport
from discord_weekly_report.report_writer import render_markdown


def test_render_markdown_contains_post_link() -> None:
    tz = ZoneInfo("Asia/Shanghai")
    post = CollectedPost(
        1,
        "forum",
        "suggestion",
        "Title",
        "a",
        "body",
        0,
        1,
        ReactionStats(),
        1,
        datetime(2026, 5, 1, tzinfo=tz),
        False,
        "url",
    )
    analyzed = AnalyzedPost(post, "短标题", "摘要", "分类", "二级", 5, 3)
    report = WeeklyReport("2026-W18", datetime(2026, 4, 27, tzinfo=tz), datetime(2026, 5, 4, tzinfo=tz), 1, 1, 0, [analyzed])

    markdown = render_markdown(report)

    assert "短标题" in markdown
    assert "url" in markdown
