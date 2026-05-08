from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import IssueGroupConfig, TopicConfig


def default_topics_path(root: Path) -> Path:
    return root / "config" / "topics.yml"


def load_topics(path: Path, active_keys: list[str]) -> list[TopicConfig]:
    if not active_keys:
        return []
    if not path.exists():
        raise FileNotFoundError(f"Topic config file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("topics"), list):
        raise ValueError("Topic config must contain a top-level topics list.")
    topics = [_topic_from_dict(item) for item in data["topics"]]
    if any(key.lower() in {"all", "*"} for key in active_keys):
        return topics
    by_key = {topic.key: topic for topic in topics}
    missing = [key for key in active_keys if key not in by_key]
    if missing:
        raise ValueError(f"ACTIVE_TOPIC_KEYS includes unknown topic keys: {', '.join(missing)}")
    return [by_key[key] for key in active_keys]


def _topic_from_dict(item: Any) -> TopicConfig:
    if not isinstance(item, dict):
        raise ValueError("Each topic entry must be a mapping.")
    key = _required_str(item, "key")
    keywords = item.get("keywords")
    if not isinstance(keywords, list) or not all(isinstance(value, str) for value in keywords):
        raise ValueError(f"Topic {key} must define string keywords.")
    return TopicConfig(
        key=key,
        display_name=_required_str(item, "display_name"),
        keywords=keywords,
        exclude_keywords=_string_list(item.get("exclude_keywords", [])),
        context_before=_optional_int(item, "context_before"),
        context_after=_optional_int(item, "context_after"),
        issue_groups=_issue_groups(item.get("issue_groups", []), key),
    )


def _issue_groups(groups: Any, topic_key: str) -> list[IssueGroupConfig]:
    if not isinstance(groups, list):
        raise ValueError(f"Topic {topic_key} issue_groups must be a list.")
    result: list[IssueGroupConfig] = []
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError(f"Topic {topic_key} issue group must be a mapping.")
        result.append(
            IssueGroupConfig(
                key=_required_str(group, "key"),
                display_name=_required_str(group, "display_name"),
                keywords=_string_list(group.get("keywords")),
            )
        )
    return result


def _required_str(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required string field: {key}")
    return value.strip()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("Expected a string list.")
    return value


def _optional_int(item: dict[str, Any], key: str) -> int | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer.")
    return value
