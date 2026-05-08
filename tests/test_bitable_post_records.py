from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from discord_weekly_report.feishu.post_records import (
    POST_DETAIL_FIELDS,
    find_existing_post_record,
    post_to_bitable_record,
    upsert_post_records,
    validate_post_detail_fields,
)
from discord_weekly_report.models import AnalyzedPost, CollectedPost, ReactionStats


def _analyzed() -> AnalyzedPost:
    post = CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title="Need fair arena",
        author="player",
        starter_content="Arena is unfair",
        reply_count=2,
        message_count=3,
        reaction_stats=ReactionStats(positive=1),
        participant_count=2,
        created_at=datetime(2026, 5, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
        archived=False,
        url="https://discord/post/1",
    )
    return AnalyzedPost(
        post=post,
        short_title="Arena 公平性反馈",
        summary="玩家认为 Arena 不公平，需要确认匹配规则。",
        primary_category="活动玩法",
        secondary_category="竞技场",
        sentiment_score=7,
        heat_score=10,
        suggestion_core="优化 Arena 匹配规则。",
    )


def test_post_to_bitable_record_matches_final_fields() -> None:
    record = post_to_bitable_record(_analyzed())

    assert set(POST_DETAIL_FIELDS).issubset(record)
    assert record["AI短标题"] == "Arena 公平性反馈"
    assert record["AI核心总结"] == "玩家认为 Arena 不公平，需要确认匹配规则。"
    assert record["具体建议"] == "优化 Arena 匹配规则。"
    assert record["帖子链接"] == {"text": "查看原帖", "link": "https://discord/post/1"}
    assert record["回复数"] == 2
    assert record["参与人数"] == 2


def test_post_detail_fields_use_readable_chinese_names() -> None:
    assert POST_DETAIL_FIELDS == [
        "AI短标题",
        "帖子链接",
        "模块分类",
        "二级分类",
        "状态",
        "满意度",
        "热度分",
        "回复数",
        "AI核心总结",
        "日期",
        "具体建议",
        "参与人数",
    ]


def test_validate_post_detail_fields_reports_missing() -> None:
    class Client:
        async def list_table_field_names(self, **kwargs):
            return set(POST_DETAIL_FIELDS[:-1])

    import asyncio

    with pytest.raises(ValueError, match="参与人数"):
        asyncio.run(validate_post_detail_fields(client=Client(), token="t", app_token="a", table_id="tbl"))


def test_upsert_updates_existing_post() -> None:
    class Client:
        def __init__(self):
            self.updated_records = []
            self.created_records = []

        async def list_records(self, **kwargs):
            return [{"record_id": "rec1", "fields": {"帖子链接": {"text": "查看原帖", "link": "url"}}}]

        async def batch_update_records(self, **kwargs):
            self.updated_records = kwargs["records"]

        async def batch_create_records(self, **kwargs):
            self.created_records = kwargs["records"]

    import asyncio

    client = Client()
    record = {"帖子链接": {"text": "查看原帖", "link": "url"}}
    asyncio.run(upsert_post_records(client=client, token="t", app_token="a", table_id="tbl", records=[record]))

    assert client.updated_records == [{"record_id": "rec1", "fields": record}]
    assert client.created_records == []


def test_upsert_creates_missing_post() -> None:
    class Client:
        def __init__(self):
            self.updated_records = []
            self.created_records = []

        async def list_records(self, **kwargs):
            return []

        async def batch_update_records(self, **kwargs):
            self.updated_records = kwargs["records"]

        async def batch_create_records(self, **kwargs):
            self.created_records = kwargs["records"]

    import asyncio

    client = Client()
    record = {"帖子链接": {"text": "查看原帖", "link": "url"}}
    asyncio.run(upsert_post_records(client=client, token="t", app_token="a", table_id="tbl", records=[record]))

    assert client.created_records == [record]
    assert client.updated_records == []


def test_find_existing_post_record_uses_post_link() -> None:
    class Client:
        def __init__(self):
            self.called = False

        async def list_records(self, **kwargs):
            self.called = True
            return [{"record_id": "rec1", "fields": {"帖子链接": {"text": "查看原帖", "link": "url"}}}]

    import asyncio

    client = Client()
    record_id = asyncio.run(
        find_existing_post_record(client=client, token="t", app_token="a", table_id="tbl", post_url="url")
    )

    assert record_id == "rec1"
    assert client.called is True
