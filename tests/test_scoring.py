from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.models import CollectedPost, ReactionStats
from discord_weekly_report.scoring import heat_score, reaction_stats_from_pairs


def test_reaction_stats_and_heat_score() -> None:
    stats = reaction_stats_from_pairs([("👍", 2), ("👎", 1), ("x", 3)])
    post = CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title="t",
        author="a",
        starter_content="body",
        reply_count=1,
        message_count=2,
        reaction_stats=stats,
        participant_count=1,
        created_at=datetime(2026, 5, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
        archived=False,
        url="url",
    )

    assert stats.positive == 2
    assert stats.negative == 1
    assert stats.other == 3
    assert heat_score(post) == 12
