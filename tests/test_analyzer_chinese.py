from datetime import datetime
from zoneinfo import ZoneInfo

from discord_weekly_report.analyzer import analyze_posts_locally
from discord_weekly_report.models import CollectedPost, ReactionStats


def _post(title: str, body: str) -> CollectedPost:
    return CollectedPost(
        post_id=1,
        source_type="forum",
        channel_name="suggestion",
        title=title,
        author="player",
        starter_content=body,
        reply_count=0,
        message_count=1,
        reaction_stats=ReactionStats(),
        participant_count=1,
        created_at=datetime(2026, 5, 1, tzinfo=ZoneInfo("Asia/Shanghai")),
        archived=False,
        url="https://discord/post/1",
    )


def test_analyzer_generates_chinese_title_and_summary_for_ava_points_bug() -> None:
    analyzed = analyze_posts_locally(
        [
            _post(
                "Ava points and al stuff used for mod vevical",
                "I have lost all my mod vevical stuff and it doesn't count for ava points because of the glitch.",
            )
        ]
    )[0]

    assert analyzed.short_title == "AvA 积分和载具材料未计入"
    assert "AvA" in analyzed.summary
    assert "未计入" in analyzed.summary


def test_analyzer_generates_chinese_title_for_group_vote_post() -> None:
    analyzed = analyze_posts_locally([_post("Voting in group chats", "Can we get voting option in group chats?")])[0]

    assert analyzed.short_title == "群聊投票功能"
    assert analyzed.summary == "玩家希望在群聊中增加投票功能，方便联盟或队伍内部做决策。"


def test_analyzer_fallback_uses_concrete_issue_title() -> None:
    analyzed = analyze_posts_locally([_post("Better mailbox sorting", "Please add filters to mailbox.")])[0]

    assert analyzed.short_title == "优化邮箱排序筛选"
    assert not analyzed.short_title.startswith("玩家建议")
    assert "体验优化" not in analyzed.short_title
    assert "待人工复核" not in analyzed.short_title
    assert "待人工复核" not in analyzed.summary


def test_analyzer_translates_common_english_suggestion_titles() -> None:
    cases = {
        "gift": "增加礼包赠送功能",
        "add fuel to the shop": "商店增加燃油",
        "new hq skins": "新增总部皮肤",
        "auto translation in chat": "聊天自动翻译",
        "headquarter decoration for women": "增加女性向总部装饰",
        "state ruler rework": "重做州长系统",
        "add upi as a payment method on website": "官网支付支持 UPI",
        "add electric engine!!!!": "增加电动引擎",
        "roses": "增加玫瑰内容",
        "speed ups": "增加加速道具",
        "please actually start taking action": "官方实际处理玩家反馈",
        "Hello everyone here, to be fair, none of the clusters in Last Z are balanced": "集群平衡和官方干预争议",
        "Think twice about putting my money in a game that has lag issues": "游戏长期卡顿问题",
        "The TvT point manipulation in EB is getting out of hand": "TvT 刷 EB 分机制问题",
        "Merger": "服务器合并建议",
    }

    for title, expected in cases.items():
        analyzed = analyze_posts_locally([_post(title, title)])[0]
        assert analyzed.short_title == expected
        assert not analyzed.short_title.startswith("玩家建议")
