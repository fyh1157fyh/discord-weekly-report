from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal


SourceType = Literal["forum", "thread"]


@dataclass
class ReactionStats:
    positive: int = 0
    negative: int = 0
    other: int = 0

    @property
    def total(self) -> int:
        return self.positive + self.negative + self.other


@dataclass
class CollectedPost:
    post_id: int
    source_type: SourceType
    channel_name: str
    title: str
    author: str
    starter_content: str
    reply_count: int
    message_count: int
    reaction_stats: ReactionStats
    participant_count: int
    created_at: datetime
    archived: bool
    url: str
    conversation: list[str] = field(default_factory=list)
    author_id: int | None = None
    participant_ids: list[int] = field(default_factory=list)


@dataclass
class CollectedMessage:
    message_id: int
    channel_id: int
    channel_name: str
    author: str
    content: str
    created_at: datetime
    url: str
    author_id: int | None = None


@dataclass
class AnalyzedPost:
    post: CollectedPost
    short_title: str
    summary: str
    primary_category: str
    secondary_category: str
    sentiment_score: int
    heat_score: int
    suggestion_core: str = ""
    analysis_error: str | None = None


@dataclass
class WeeklyReport:
    week_label: str
    start_at: datetime
    end_at: datetime
    total_posts: int
    successful_analyses: int
    failed_analyses: int
    posts: list[AnalyzedPost]


@dataclass
class IssueGroupConfig:
    key: str
    display_name: str
    keywords: list[str]


@dataclass
class TopicConfig:
    key: str
    display_name: str
    keywords: list[str]
    exclude_keywords: list[str] = field(default_factory=list)
    context_before: int | None = None
    context_after: int | None = None
    issue_groups: list[IssueGroupConfig] = field(default_factory=list)


@dataclass
class TopicPostMatch:
    item: AnalyzedPost
    matched_keywords: list[str]


@dataclass
class TopicMessageMatch:
    message: CollectedMessage
    matched_keywords: list[str]
    context: list[CollectedMessage] = field(default_factory=list)


@dataclass
class IssueGroupSummary:
    key: str
    display_name: str
    unique_players: int
    post_count: int
    message_count: int
    max_heat_score: int
    matched_keywords: list[str]
    post_matches: list[TopicPostMatch] = field(default_factory=list)
    message_matches: list[TopicMessageMatch] = field(default_factory=list)


@dataclass
class TopicReport:
    topic: TopicConfig
    week_label: str
    start_at: datetime
    end_at: datetime
    post_matches: list[TopicPostMatch]
    message_matches: list[TopicMessageMatch]
    issue_groups: list[IssueGroupSummary] = field(default_factory=list)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
