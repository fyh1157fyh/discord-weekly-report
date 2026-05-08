from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.codex_review import apply_codex_review, render_codex_review_input
from discord_weekly_report.models import AnalyzedPost, CollectedPost, ReactionStats, WeeklyReport


def _report() -> WeeklyReport:
    tz = ZoneInfo("Asia/Shanghai")
    post = CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title="add fuel to the shop",
        author="player",
        starter_content="Please add fuel to the shop.",
        reply_count=2,
        message_count=3,
        reaction_stats=ReactionStats(positive=1),
        participant_count=2,
        created_at=datetime(2026, 5, 1, tzinfo=tz),
        archived=False,
        url="https://discord/post/1",
        conversation=["player: Please add fuel to the shop."],
    )
    analyzed = AnalyzedPost(post, "商店增加燃油", "旧总结", "旧分类", "旧二级", 5, 10)
    return WeeklyReport("2026-W18", datetime(2026, 4, 27, tzinfo=tz), datetime(2026, 5, 4, tzinfo=tz), 1, 1, 0, [analyzed])


def test_render_codex_review_input_contains_required_json_fields() -> None:
    text = render_codex_review_input(_report())

    assert "post_id" in text
    assert "short_title" in text
    assert "suggestion_core" in text
    assert "玩家建议" in text
    assert "Please add fuel to the shop" in text


def test_apply_codex_review_updates_analyzed_fields() -> None:
    report = apply_codex_review(
        _report(),
        {
            "items": [
                {
                    "post_id": 1,
                    "url": "https://discord/post/1",
                    "short_title": "商店增加燃油",
                    "summary": "玩家反馈燃油不足，希望商店提供稳定购买入口。",
                    "suggestion_core": "在商店加入燃油购买项。",
                    "primary_category": "资源经济",
                    "secondary_category": "燃油获取",
                    "sentiment_score": 3,
                }
            ]
        },
    )

    item = report.posts[0]
    assert item.summary == "燃油(Fuel)不足，希望商店提供稳定购买入口。"
    assert item.suggestion_core == "在商店加入燃油(Fuel)购买项。"
    assert item.primary_category == "资源经济"
    assert item.secondary_category == "燃油获取"
    assert item.sentiment_score == 3
    assert report.successful_analyses == 1
    assert report.failed_analyses == 0


def test_apply_codex_review_removes_redundant_player_prefix() -> None:
    report = apply_codex_review(
        _report(),
        {
            "items": [
                {
                    "post_id": 1,
                    "short_title": "商店增加燃油",
                    "summary": "玩家反馈燃油不足，希望商店提供稳定购买入口。",
                    "suggestion_core": "玩家希望在商店加入燃油购买项。",
                    "primary_category": "资源经济",
                    "secondary_category": "燃油获取",
                    "sentiment_score": 3,
                }
            ]
        },
    )

    item = report.posts[0]
    assert item.summary == "燃油(Fuel)不足，希望商店提供稳定购买入口。"
    assert item.suggestion_core == "在商店加入燃油(Fuel)购买项。"


def test_apply_codex_review_removes_player_word_inside_text() -> None:
    report = apply_codex_review(
        _report(),
        {
            "items": [
                {
                    "post_id": 1,
                    "short_title": "挖掘连点器破坏公平",
                    "summary": "普通玩家几乎抢不到奖励，付费玩家也受到影响。",
                    "suggestion_core": "减少玩家之间的点击速度差距。",
                    "primary_category": "活动玩法",
                    "secondary_category": "宝藏挖掘",
                    "sentiment_score": 2,
                }
            ]
        },
    )

    item = report.posts[0]
    assert "玩家" not in item.summary
    assert "玩家" not in item.suggestion_core


def test_apply_codex_review_adds_bilingual_game_terms() -> None:
    report = apply_codex_review(
        _report(),
        {
            "items": [
                {
                    "post_id": 1,
                    "short_title": "宝藏挖掘奖励",
                    "summary": "宝藏挖掘奖励被低延迟垄断，燃油消耗也偏高。",
                    "suggestion_core": "调整宝藏挖掘奖励，并增加燃油获取。",
                    "primary_category": "活动玩法",
                    "secondary_category": "宝藏挖掘",
                    "sentiment_score": 2,
                }
            ]
        },
    )

    item = report.posts[0]
    assert "宝藏挖掘(Treasure Dig)" in item.summary
    assert "燃油(Fuel)" in item.summary
    assert "宝藏挖掘(Treasure Dig)" in item.suggestion_core
