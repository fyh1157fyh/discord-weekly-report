from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.filters import filter_posts
from discord_weekly_report.models import CollectedPost, ReactionStats


def _post(content: str) -> CollectedPost:
    return CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title="t",
        author="a",
        starter_content=content,
        reply_count=0,
        message_count=1,
        reaction_stats=ReactionStats(),
        participant_count=1,
        created_at=datetime(2026, 5, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
        archived=False,
        url="url",
    )


def test_filter_drops_missing_starter_content() -> None:
    assert filter_posts([_post(""), _post("body")]) == [_post("body")]
