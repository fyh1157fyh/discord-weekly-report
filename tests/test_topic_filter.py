from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.models import (
    AnalyzedPost,
    CollectedMessage,
    CollectedPost,
    IssueGroupConfig,
    ReactionStats,
    TopicConfig,
)
from discord_weekly_report.topic_filter import build_topic_report, match_keywords
from discord_weekly_report.topics import load_topics


def test_match_keywords_ascii_word_boundary() -> None:
    topic = TopicConfig(key="arena", display_name="竞技场", keywords=["ava"])

    assert match_keywords("avatar", topic) == []
    assert match_keywords("AvA is unfair", topic) == ["ava"]


def test_topic_concentration_counts_participant_ids() -> None:
    tz = ZoneInfo("Asia/Shanghai")
    topic = TopicConfig(
        key="arena",
        display_name="竞技场",
        keywords=["champion duel"],
        issue_groups=[IssueGroupConfig(key="time", display_name="时区问题", keywords=["3am", "champion duel"])],
    )
    raw = CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title="Champion duel 3am",
        author="a",
        starter_content="3am is impossible",
        reply_count=1,
        message_count=2,
        reaction_stats=ReactionStats(),
        participant_count=2,
        created_at=datetime(2026, 5, 1, tzinfo=tz),
        archived=False,
        url="url",
        participant_ids=[1, 2],
    )
    analyzed = AnalyzedPost(raw, "title", "summary", "Arena", "竞技场", 8, 10)
    messages = [
        CollectedMessage(1, 10, "general", "b", "champion duel also bad", datetime(2026, 5, 1, tzinfo=tz), "m", 3)
    ]

    report = build_topic_report(
        topic=topic,
        week_label="2026-W18",
        start_at=datetime(2026, 4, 27, tzinfo=tz),
        end_at=datetime(2026, 5, 4, tzinfo=tz),
        posts=[analyzed],
        messages=messages,
        default_context_before=0,
        default_context_after=0,
    )

    assert report.issue_groups[0].unique_players == 3


def test_generated_category_does_not_create_topic_match() -> None:
    tz = ZoneInfo("Asia/Shanghai")
    topic = TopicConfig(key="arena", display_name="竞技场", keywords=["竞技场"])
    raw = CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title="Fuel pass",
        author="a",
        starter_content="We need a weekly fuel pass.",
        reply_count=0,
        message_count=1,
        reaction_stats=ReactionStats(),
        participant_count=1,
        created_at=datetime(2026, 5, 1, tzinfo=tz),
        archived=False,
        url="url",
    )
    analyzed = AnalyzedPost(raw, "Fuel pass", "summary", "Arena", "竞技场", 5, 3)

    report = build_topic_report(
        topic=topic,
        week_label="2026-W18",
        start_at=datetime(2026, 4, 27, tzinfo=tz),
        end_at=datetime(2026, 5, 4, tzinfo=tz),
        posts=[analyzed],
        messages=[],
        default_context_before=0,
        default_context_after=0,
    )

    assert report.post_matches == []


def test_load_topics_all_enables_every_topic(tmp_path) -> None:
    path = tmp_path / "topics.yml"
    path.write_text(
        """
topics:
  - key: arena
    display_name: 竞技场
    keywords: [arena]
  - key: trunk
    display_name: Trunk
    keywords: [trunk]
""",
        encoding="utf-8",
    )

    topics = load_topics(path, ["all"])

    assert [topic.key for topic in topics] == ["arena", "trunk"]
