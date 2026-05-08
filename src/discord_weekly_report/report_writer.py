from __future__ import annotations

import json

from .models import WeeklyReport, to_jsonable
from .paths import OutputPaths


def write_outputs(paths: OutputPaths, raw_posts, report: WeeklyReport) -> None:
    paths.raw_json.write_text(json.dumps(to_jsonable(raw_posts), ensure_ascii=False, indent=2), encoding="utf-8")
    paths.analyzed_json.write_text(json.dumps(to_jsonable(report), ensure_ascii=False, indent=2), encoding="utf-8")
    paths.markdown.write_text(render_markdown(report), encoding="utf-8")
    paths.codex_input.write_text(render_codex_input(report), encoding="utf-8")


def render_markdown(report: WeeklyReport) -> str:
    lines = [
        f"# Discord 玩家建议周报 - {report.week_label}",
        "",
        f"周期：{report.start_at:%Y-%m-%d %H:%M} 到 {report.end_at:%Y-%m-%d %H:%M}",
        "",
        f"- 帖子数：{report.total_posts}",
        f"- 成功分析：{report.successful_analyses}",
        f"- 失败分析：{report.failed_analyses}",
        "",
        "## 高热建议",
        "",
    ]
    for index, item in enumerate(sorted(report.posts, key=lambda post: post.heat_score, reverse=True), start=1):
        lines.extend(
            [
                f"### {index}. {item.short_title}",
                "",
                f"- 分类：{item.primary_category} / {item.secondary_category}",
                f"- 满意度：{item.sentiment_score}",
                f"- 热度分：{item.heat_score}",
                f"- 参与人数：{item.post.participant_count}",
                f"- 摘要：{item.summary}",
                f"- 原帖：{item.post.url}",
                "",
            ]
        )
    return "\n".join(lines)


def render_codex_input(report: WeeklyReport) -> str:
    lines = [
        f"# Codex 周报整理输入 - {report.week_label}",
        "",
        "请基于下面 Discord 原文整理中文周报，不要编造原文没有的信息。",
        "",
    ]
    for index, item in enumerate(report.posts, start=1):
        conversation = "\n".join(item.post.conversation) or item.post.starter_content
        lines.extend(
            [
                f"## {index}. {item.post.title}",
                "",
                f"- 链接：{item.post.url}",
                f"- 热度分：{item.heat_score}",
                f"- 参与人数：{item.post.participant_count}",
                "",
                "```text",
                conversation,
                "```",
                "",
            ]
        )
    return "\n".join(lines)
