from __future__ import annotations

from pathlib import Path

from .models import CollectedMessage, TopicMessageMatch, TopicPostMatch, TopicReport
from .topic_insights import (
    compact_source_text,
    issue_summary,
    readable_post_takeaway,
    representative_links,
    suggested_action,
)


def write_topic_outputs(*, data_dir: Path, reports_dir: Path, topic_report: TopicReport) -> tuple[Path, Path]:
    codex_input = data_dir / f"{topic_report.week_label}.{topic_report.topic.key}.codex-input.md"
    markdown = reports_dir / f"{topic_report.week_label}.{topic_report.topic.key}.md"
    codex_input.write_text(render_topic_codex_input(topic_report), encoding="utf-8")
    markdown.write_text(render_topic_markdown(topic_report), encoding="utf-8")
    return codex_input, markdown


def render_topic_markdown(report: TopicReport) -> str:
    grouped_posts = {id(match) for group in report.issue_groups for match in group.post_matches}
    review_posts = [match for match in report.post_matches if id(match) not in grouped_posts]
    lines = [
        f"# {report.topic.display_name}舆情专题 - {report.week_label}",
        "",
        f"周期：{report.start_at:%Y-%m-%d %H:%M} 到 {report.end_at:%Y-%m-%d %H:%M}",
        "",
        "## 一句话结论",
        "",
        _one_line_conclusion(report, review_posts),
        "",
        "## 概览",
        "",
        f"- 命中帖子数：{len(report.post_matches)}",
        f"- 命中聊天消息数：{len(report.message_matches)}",
        f"- 已归类问题组数：{len(report.issue_groups)}",
        f"- 需人工复核命中：{len(review_posts)}",
        "",
        "## 本周最值得关注",
        "",
    ]
    if report.issue_groups:
        for index, group in enumerate(report.issue_groups[:3], start=1):
            lines.extend(
                [
                    f"### {index}. {group.display_name}",
                    "",
                    f"- 浓度：{group.unique_players} 名独立玩家，{group.post_count} 条帖子，{group.message_count} 条聊天。",
                    f"- 判断：{issue_summary(group)}",
                    f"- 建议动作：{suggested_action(group)}",
                    f"- 代表链接：{', '.join(representative_links(group, 3)) or '暂无'}",
                    "",
                ]
            )
    else:
        lines.append("本周没有形成明确的重复问题，建议只抽查高热命中。")
    lines.extend(["", "## 舆情浓度排行", ""])
    lines.extend(_issue_group_table(report))
    lines.extend(["", "## 高热原帖解读", ""])
    if report.post_matches:
        for index, match in enumerate(sorted(report.post_matches, key=lambda item: item.item.heat_score, reverse=True), start=1):
            lines.extend(_post_match_lines(index, match))
    else:
        lines.append("本周期没有命中相关帖子。")
    lines.extend(["", "## 聊天舆情摘录", ""])
    if report.message_matches:
        for index, match in enumerate(report.message_matches[:20], start=1):
            lines.extend(_message_match_lines(index, match))
    else:
        lines.append("本周期没有命中相关聊天消息。")
    return "\n".join(lines)


def render_topic_codex_input(report: TopicReport) -> str:
    lines = [
        f"# Codex 专题整理输入 - {report.topic.display_name} - {report.week_label}",
        "",
        "请用中文合并重复问题，优先关注同类问题由多少个不同玩家提出。",
        "",
        "## 舆情浓度统计",
        "",
    ]
    for index, group in enumerate(report.issue_groups, start=1):
        lines.extend(
            [
                f"### {index}. {group.display_name}",
                f"- 独立玩家数：{group.unique_players}",
                f"- 摘要：{issue_summary(group)}",
                f"- 建议动作：{suggested_action(group)}",
                f"- 代表链接：{', '.join(representative_links(group, 3)) or '无'}",
                "",
            ]
        )
    return "\n".join(lines)


def _one_line_conclusion(report: TopicReport, review_posts: list[TopicPostMatch]) -> str:
    if report.issue_groups:
        top = report.issue_groups[0]
        return (
            f"本周“{report.topic.display_name}”最集中的问题是“{top.display_name}”，"
            f"涉及 {top.unique_players} 名独立玩家；另有 {len(review_posts)} 条关键词命中需要人工复核，避免误判。"
        )
    if report.post_matches or report.message_matches:
        return f"本周有零散命中，但未形成明确重复问题，建议抽查高热原帖确认是否为误命中。"
    return f"本周未发现明显“{report.topic.display_name}”相关舆情。"


def _issue_group_table(report: TopicReport) -> list[str]:
    if not report.issue_groups:
        return ["暂无明确问题组命中。"]
    lines = [
        "| 排名 | 问题 | 独立玩家数 | 帖子数 | 聊天数 | 最高热度 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for index, group in enumerate(report.issue_groups, start=1):
        lines.append(f"| {index} | {group.display_name} | {group.unique_players} | {group.post_count} | {group.message_count} | {group.max_heat_score} |")
    return lines


def _post_match_lines(index: int, match: TopicPostMatch) -> list[str]:
    item = match.item
    source = item.post.starter_content or item.post.title
    return [
        f"### {index}. {item.post.title}",
        "",
        f"- 具体问题：{readable_post_takeaway(match)}",
        f"- 命中关键词：{', '.join(match.matched_keywords)}",
        f"- 热度/参与：热度 {item.heat_score}，{item.post.participant_count} 名参与者，{item.post.reply_count} 条回复。",
        f"- 原文摘录：{compact_source_text(source)}",
        f"- 原帖：{item.post.url}",
        "",
    ]


def _message_match_lines(index: int, match: TopicMessageMatch) -> list[str]:
    return [
        f"### {index}. {match.message.channel_name} / {match.message.created_at:%Y-%m-%d %H:%M}",
        "",
        f"- 命中关键词：{', '.join(match.matched_keywords)}",
        f"- 作者：{match.message.author}",
        f"- 内容：{compact_source_text(match.message.content)}",
        f"- 链接：{match.message.url}",
        "",
    ]


def context_text(messages: list[CollectedMessage]) -> str:
    return "\n".join(f"[{item.created_at:%Y-%m-%d %H:%M}] {item.author}: {item.content}" for item in messages)
