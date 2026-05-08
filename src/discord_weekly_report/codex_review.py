from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AnalyzedPost, WeeklyReport, to_jsonable


REVIEW_FIELDS = [
    "post_id",
    "url",
    "short_title",
    "summary",
    "suggestion_core",
    "primary_category",
    "secondary_category",
    "sentiment_score",
]


def codex_review_path(analyzed_json: Path) -> Path:
    return analyzed_json.with_name(analyzed_json.name.replace(".analysis.json", ".codex-review.json"))


def render_codex_review_input(report: WeeklyReport) -> str:
    lines = [
        f"# Codex 精修输入 - {report.week_label}",
        "",
        "请阅读下面 Discord 原文，为每条帖子生成可直接写入飞书的中文字段。",
        "",
        "输出要求：",
        "- 只输出 JSON，不要解释。",
        "- JSON 格式：{\"items\": [...]}。",
        "- 每个 item 包含：post_id, url, short_title, summary, suggestion_core, primary_category, secondary_category, sentiment_score。",
        "- short_title 写 6-12 字具体问题，不要写“玩家建议”“体验优化”“相关反馈”。",
        "- summary 说明具体机制、道具、活动或场景里的问题，不要写“提出反馈/没有满足预期/结合原帖评估”这类废话。",
        "- suggestion_core 写具体可执行改法；没有明确方案则写“无明确建议”，不要写“根据原帖补充评估具体改动方案”。",
        "- 游戏专业名词首次出现时尽量写成“中文名(英文名)”，例如：关隘(Gate)、竞技场(Arena)、联盟决斗(Alliance Duel)、峡谷争夺(Canyon Clash)、荣耀战(Glory War)、宝藏挖掘(Treasure Dig)、迁服(Migration)、燃油(Fuel)、总部(HQ)。",
        "- 所有内容用简体中文；英文专有名词用于括号对照，不要整句英文。",
        "",
        "待处理帖子：",
        "",
    ]
    for index, item in enumerate(sorted(report.posts, key=lambda post: post.heat_score, reverse=True), start=1):
        lines.extend(_render_review_item(index, item))
    return "\n".join(lines)


def apply_codex_review(report: WeeklyReport, review_data: dict[str, Any]) -> WeeklyReport:
    review_by_id = {str(item.get("post_id")): item for item in review_data.get("items", []) if isinstance(item, dict)}
    reviewed = 0
    for item in report.posts:
        review = review_by_id.get(str(item.post.post_id))
        if not review:
            continue
        item.short_title = _text(review.get("short_title"), item.short_title)[:24]
        item.summary = _normalize_terms(_remove_player_prefix(_text(review.get("summary"), item.summary)))
        item.suggestion_core = _normalize_terms(_remove_player_prefix(_text(review.get("suggestion_core"), item.suggestion_core or "无明确建议")))
        item.primary_category = _text(review.get("primary_category"), item.primary_category)
        item.secondary_category = _text(review.get("secondary_category"), item.secondary_category)
        item.sentiment_score = _score(review.get("sentiment_score"), item.sentiment_score)
        item.analysis_error = None
        reviewed += 1
    report.successful_analyses = reviewed
    report.failed_analyses = max(0, len(report.posts) - reviewed)
    return report


def write_review_json_template(path: Path, report: WeeklyReport) -> None:
    template = {
        "week_label": report.week_label,
        "items": [
            {
                "post_id": item.post.post_id,
                "url": item.post.url,
                "short_title": item.short_title,
                "summary": item.summary,
                "suggestion_core": item.suggestion_core or "无明确建议",
                "primary_category": item.primary_category,
                "secondary_category": item.secondary_category,
                "sentiment_score": item.sentiment_score,
            }
            for item in report.posts
        ],
    }
    path.write_text(json.dumps(to_jsonable(template), ensure_ascii=False, indent=2), encoding="utf-8")


def _render_review_item(index: int, item: AnalyzedPost) -> list[str]:
    post = item.post
    conversation = "\n".join(post.conversation[:10]) or post.starter_content
    return [
        f"## {index}. {post.title}",
        "",
        f"- post_id：{post.post_id}",
        f"- url：{post.url}",
        f"- 当前短标题：{item.short_title}",
        f"- 当前总结：{item.summary}",
        f"- 热度分：{item.heat_score}",
        f"- 回复数：{post.reply_count}",
        f"- 参与人数：{post.participant_count}",
        f"- reaction：正向 {post.reaction_stats.positive} / 负向 {post.reaction_stats.negative} / 其他 {post.reaction_stats.other}",
        "",
        "```text",
        conversation[:4000],
        "```",
        "",
    ]


def _text(value: Any, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return " ".join(text.split()) if text else fallback


def _score(value: Any, fallback: int) -> int:
    try:
        return max(1, min(10, int(float(value))))
    except (TypeError, ValueError):
        return fallback


def _remove_player_prefix(text: str) -> str:
    replacements = {
        "玩家反馈": "",
        "玩家希望": "",
        "玩家认为": "",
        "玩家提出": "",
        "玩家抱怨": "",
        "玩家要求": "",
        "玩家质疑": "",
        "玩家集中提出": "",
        "玩家围绕": "",
        "普通玩家": "普通成员",
        "付费玩家": "付费用户",
        "老玩家": "老用户",
        "女性玩家": "女性用户",
        "国际玩家": "国际用户",
        "印度玩家": "印度用户",
        "玩家": "",
    }
    result = text
    for source, target in replacements.items():
        result = result.replace(source, target)
    result = result.strip(" ：:，,；;")
    return result + ("。" if result and not result.endswith(("。", "！", "？")) else "")


def _normalize_terms(text: str) -> str:
    terms = {
        "关隘": "Gate",
        "竞技场": "Arena",
        "联盟决斗": "Alliance Duel",
        "峡谷争夺": "Canyon Clash",
        "荣耀战": "Glory War",
        "宝藏挖掘": "Treasure Dig",
        "迁服": "Migration",
        "燃油": "Fuel",
        "总部": "HQ",
    }
    result = text
    for chinese, english in terms.items():
        bilingual = f"{chinese}({english})"
        if bilingual in result:
            continue
        result = result.replace(chinese, bilingual)
    return result
