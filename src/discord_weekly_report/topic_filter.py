from __future__ import annotations

from collections import defaultdict
import re

from .models import (
    AnalyzedPost,
    CollectedMessage,
    IssueGroupConfig,
    IssueGroupSummary,
    TopicConfig,
    TopicMessageMatch,
    TopicPostMatch,
    TopicReport,
)


def build_topic_report(
    *,
    topic: TopicConfig,
    week_label: str,
    start_at,
    end_at,
    posts: list[AnalyzedPost],
    messages: list[CollectedMessage],
    default_context_before: int,
    default_context_after: int,
) -> TopicReport:
    post_matches = [
        TopicPostMatch(item=post, matched_keywords=keywords)
        for post in posts
        if (keywords := match_keywords(_post_text(post), topic))
    ]
    message_matches = match_messages_with_context(
        messages=messages,
        topic=topic,
        context_before=topic.context_before if topic.context_before is not None else default_context_before,
        context_after=topic.context_after if topic.context_after is not None else default_context_after,
    )
    return TopicReport(
        topic=topic,
        week_label=week_label,
        start_at=start_at,
        end_at=end_at,
        post_matches=post_matches,
        message_matches=message_matches,
        issue_groups=_build_issue_groups(topic.issue_groups, post_matches, message_matches),
    )


def match_keywords(text: str, topic: TopicConfig) -> list[str]:
    haystack = text.casefold()
    if any(_keyword_matches(haystack, keyword) for keyword in topic.exclude_keywords):
        return []
    return [keyword for keyword in topic.keywords if _keyword_matches(haystack, keyword)]


def match_messages_with_context(
    *,
    messages: list[CollectedMessage],
    topic: TopicConfig,
    context_before: int,
    context_after: int,
) -> list[TopicMessageMatch]:
    by_channel: dict[int, list[CollectedMessage]] = defaultdict(list)
    for message in sorted(messages, key=lambda item: item.created_at):
        by_channel[message.channel_id].append(message)
    matches: list[TopicMessageMatch] = []
    for channel_messages in by_channel.values():
        for index, message in enumerate(channel_messages):
            keywords = match_keywords(message.content, topic)
            if not keywords:
                continue
            start = max(index - context_before, 0)
            end = min(index + context_after + 1, len(channel_messages))
            matches.append(TopicMessageMatch(message=message, matched_keywords=keywords, context=channel_messages[start:end]))
    return matches


def _build_issue_groups(
    groups: list[IssueGroupConfig],
    post_matches: list[TopicPostMatch],
    message_matches: list[TopicMessageMatch],
) -> list[IssueGroupSummary]:
    summaries = [
        summary
        for group in groups
        if (summary := _issue_group_summary(group, post_matches, message_matches)) is not None
    ]
    return sorted(summaries, key=lambda item: (item.unique_players, item.post_count + item.message_count, item.max_heat_score), reverse=True)


def _issue_group_summary(
    group: IssueGroupConfig,
    post_matches: list[TopicPostMatch],
    message_matches: list[TopicMessageMatch],
) -> IssueGroupSummary | None:
    matched_posts: list[TopicPostMatch] = []
    matched_messages: list[TopicMessageMatch] = []
    matched_keywords: list[str] = []
    players: set[str] = set()
    for match in post_matches:
        keywords = _match_keyword_list(_post_text(match.item), group.keywords)
        if keywords:
            matched_posts.append(match)
            matched_keywords.extend(keywords)
            _add_post_players(players, match.item.post)
    for match in message_matches:
        text = "\n".join([match.message.content, "\n".join(item.content for item in match.context)])
        keywords = _match_keyword_list(text, group.keywords)
        if keywords:
            matched_messages.append(match)
            matched_keywords.extend(keywords)
            _add_identity(players, match.message.author_id, match.message.author)
    if not matched_posts and not matched_messages:
        return None
    return IssueGroupSummary(
        key=group.key,
        display_name=group.display_name,
        unique_players=len(players),
        post_count=len(matched_posts),
        message_count=len(matched_messages),
        max_heat_score=max((match.item.heat_score for match in matched_posts), default=0),
        matched_keywords=_ordered_unique(matched_keywords),
        post_matches=matched_posts,
        message_matches=matched_messages,
    )


def _post_text(post: AnalyzedPost) -> str:
    raw = post.post
    # Topic matching must use player-authored Discord text only. If we include
    # generated labels such as "竞技场", the label itself can cause false hits.
    return "\n".join([raw.title, raw.starter_content, "\n".join(raw.conversation), post.summary])


def _match_keyword_list(text: str, keywords: list[str]) -> list[str]:
    haystack = text.casefold()
    return [keyword for keyword in keywords if _keyword_matches(haystack, keyword)]


def _keyword_matches(haystack: str, keyword: str) -> bool:
    needle = keyword.casefold().strip()
    if not needle:
        return False
    if all(ord(char) < 128 for char in needle):
        return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack) is not None
    return needle in haystack


def _add_post_players(players: set[str], post) -> None:
    if post.participant_ids:
        players.update(f"id:{player_id}" for player_id in post.participant_ids)
    else:
        _add_identity(players, post.author_id, post.author)


def _add_identity(players: set[str], user_id: int | None, fallback_name: str) -> None:
    if user_id is not None:
        players.add(f"id:{user_id}")
        return
    if fallback_name.strip():
        players.add(f"name:{fallback_name.strip().casefold()}")


def _ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
