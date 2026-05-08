from __future__ import annotations

from .models import IssueGroupSummary, TopicPostMatch


def issue_summary(group: IssueGroupSummary) -> str:
    evidence = f"{group.post_count} 条帖子、{group.message_count} 条聊天"
    if group.unique_players >= 5:
        level = "属于本周高浓度问题，建议优先看原帖确认。"
    elif group.unique_players >= 2:
        level = "已经有多名玩家重复提及，建议持续观察。"
    else:
        level = "目前更像单点反馈，可先作为样本保留。"
    return f"{group.display_name}被 {group.unique_players} 名独立玩家提及，覆盖 {evidence}。{level}"


def suggested_action(group: IssueGroupSummary) -> str:
    text = group.display_name
    if "匹配" in text or "公平" in text:
        return "检查匹配规则、分组口径和玩家感知是否一致；如果规则正确，补充公告或 FAQ 解释。"
    if "奖励" in text or "价值" in text:
        return "对比活动投入与奖励获得，确认是否存在奖励感知偏低或关键奖励缺口。"
    if "时区" in text or "时间" in text:
        return "评估活动时间对不同时区玩家的影响，必要时提供轮换时间或补偿机制。"
    if group.unique_players >= 3 or group.max_heat_score >= 50:
        return "作为本周重点问题进入策划复盘，先核对代表原帖中的具体场景。"
    return "先保留样本，后续若玩家数继续增加再进入正式问题池。"


def representative_links(group: IssueGroupSummary, limit: int = 3) -> list[str]:
    links = [match.item.post.url for match in group.post_matches]
    links.extend(match.message.url for match in group.message_matches)
    result: list[str] = []
    for link in links:
        if link not in result:
            result.append(link)
    return result[:limit]


def readable_post_takeaway(match: TopicPostMatch) -> str:
    title = match.item.post.title.strip()
    body = match.item.post.starter_content.strip()
    text = f"{title}\n{body}".casefold()

    if "ava" in text and ("lost" in text or "not count" in text or "doesn't cout" in text or "glitch" in text):
        return "玩家反馈 AvA 相关积分或载具材料因疑似故障未计入，影响活动积分结算。"
    if ("eu" in text or "europe" in text) and ("3/4 am" in text or "3am" in text or "4am" in text or "reset" in text):
        return "EU 玩家反馈服务器重置时间落在凌晨 3/4 点，影响 AvA 冲分和活动参与。"
    if "unable" in text and "attack" in text and "arena" in text:
        return "玩家反馈重置前无法在 Silver/Peak Arena 发起攻击，因此错过每日/每周奖励机会。"
    if "free teleport" in text and ("same server" in text or "same state" in text):
        return "玩家反馈同服联盟决斗时没有免费迁城，但跨服对手有免费迁城，规则感知不一致。"
    if "export" in text and "duel" in text and "results" in text:
        return "玩家希望 R5 能导出 Duel 对战结果，减少联盟手工统计和追踪成本。"
    if "alliance squad management" in text:
        return "玩家建议增加联盟小队管理功能，用于 AvA/Duel 等活动的编组和协作。"
    if "radars" in text and "not counted" in text:
        return "玩家反馈 Duel 中雷达事件未计数，疑似活动积分统计异常。"
    if "points" in text or "ranking" in text or "reward" in text or "rewards" in text:
        return "玩家反馈积分、排名或奖励结算存在具体损失，需结合原帖核对活动日志。"
    if "bug" in text or "unable" in text or "lost" in text or "missed" in text:
        return "玩家反馈疑似 Bug 导致进度、积分或参与机会损失。"
    if "unfair" in text or "matchmaking" in text or "opponent" in text:
        return "玩家反馈匹配或对手规则不公平，需确认规则设计与玩家理解是否一致。"
    return f"需人工复核：标题为“{title}”，机器只能确认其命中专题关键词。"


def compact_source_text(text: str, limit: int = 240) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return "无可读原文。"
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1].rstrip() + "…"
