import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from discord_weekly_report.ai_analyzer import analyze_posts
from discord_weekly_report.config import Settings
from discord_weekly_report.models import CollectedPost, ReactionStats


def _settings(*, enabled: bool = True) -> Settings:
    return Settings(
        discord_bot_token="token",
        discord_guild_id=1,
        discord_forum_channel_ids=[1],
        discord_thread_channel_ids=[],
        discord_text_channel_ids=[],
        timezone=ZoneInfo("Asia/Shanghai"),
        output_dir=".",
        enable_ai_analysis=enabled,
        ai_api_key="key" if enabled else "",
        ai_base_url="https://example.test/v1",
        ai_model="model",
    )


def _post() -> CollectedPost:
    return CollectedPost(
        post_id=123,
        source_type="forum",
        channel_name="suggestion",
        title="add fuel to the shop",
        author="player",
        starter_content="Please add fuel to the shop.",
        reply_count=2,
        message_count=3,
        reaction_stats=ReactionStats(positive=2),
        participant_count=2,
        created_at=datetime(2026, 5, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
        archived=False,
        url="https://discord/post/123",
        conversation=["Fuel is always not enough."],
    )


class FakeClient:
    def __init__(self, content: str | None = None, *, raises: Exception | None = None):
        self.content = content
        self.raises = raises
        self.requests = []

    async def post(self, url: str, **kwargs):
        self.requests.append((url, kwargs))
        if self.raises:
            raise self.raises
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": self.content}}]},
            request=httpx.Request("POST", url),
        )


def test_ai_analyzer_maps_valid_json_to_analyzed_post() -> None:
    content = json.dumps(
        {
            "items": [
                {
                    "id": "123",
                    "short_title": "商店增加燃油",
                    "summary": "玩家反馈燃油长期不足，希望商店提供稳定购买入口。",
                    "suggestion_core": "在商店加入燃油购买项。",
                    "primary_category": "资源经济",
                    "secondary_category": "燃油获取",
                    "sentiment_score": 3,
                }
            ]
        },
        ensure_ascii=False,
    )
    analyzed = asyncio.run(analyze_posts([_post()], _settings(), client=FakeClient(content)))[0]

    assert analyzed.short_title == "商店增加燃油"
    assert analyzed.summary == "玩家反馈燃油长期不足，希望商店提供稳定购买入口。"
    assert analyzed.suggestion_core == "在商店加入燃油购买项。"
    assert analyzed.primary_category == "资源经济"
    assert analyzed.secondary_category == "燃油获取"
    assert analyzed.sentiment_score == 3
    assert analyzed.heat_score > 0
    assert analyzed.analysis_error is None


def test_ai_analyzer_falls_back_when_ai_returns_invalid_json() -> None:
    analyzed = asyncio.run(analyze_posts([_post()], _settings(), client=FakeClient("not json")))[0]

    assert analyzed.short_title == "商店增加燃油"
    assert analyzed.suggestion_core == "无明确建议"
    assert analyzed.analysis_error


def test_ai_analyzer_cleans_generic_short_title() -> None:
    content = json.dumps(
        {
            "items": [
                {
                    "id": "123",
                    "short_title": "玩家建议：体验优化",
                    "summary": "玩家反馈燃油不足。",
                    "suggestion_core": "增加燃油购买入口。",
                    "primary_category": "资源经济",
                    "secondary_category": "燃油获取",
                    "sentiment_score": 4,
                }
            ]
        },
        ensure_ascii=False,
    )
    analyzed = asyncio.run(analyze_posts([_post()], _settings(), client=FakeClient(content)))[0]

    assert analyzed.short_title == "商店增加燃油"
    assert analyzed.summary == "玩家反馈燃油不足。"
    assert analyzed.suggestion_core == "增加燃油购买入口。"


def test_ai_analyzer_disabled_uses_local_rules_without_http_call() -> None:
    client = FakeClient("{}")
    analyzed = asyncio.run(analyze_posts([_post()], _settings(enabled=False), client=client))[0]

    assert analyzed.short_title == "商店增加燃油"
    assert client.requests == []
