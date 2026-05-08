from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import AnalyzedPost, CollectedPost, ReactionStats, WeeklyReport


def load_weekly_report(path: Path) -> WeeklyReport:
    data = json.loads(path.read_text(encoding="utf-8"))
    posts = [_load_analyzed_post(item) for item in data.get("posts", [])]
    return WeeklyReport(
        week_label=data["week_label"],
        start_at=datetime.fromisoformat(data["start_at"]),
        end_at=datetime.fromisoformat(data["end_at"]),
        total_posts=int(data.get("total_posts", len(posts))),
        successful_analyses=int(data.get("successful_analyses", len(posts))),
        failed_analyses=int(data.get("failed_analyses", 0)),
        posts=posts,
    )


def _load_analyzed_post(data: dict[str, Any]) -> AnalyzedPost:
    post_data = dict(data["post"])
    post_data["created_at"] = datetime.fromisoformat(post_data["created_at"])
    post_data["reaction_stats"] = ReactionStats(**post_data.get("reaction_stats", {}))
    return AnalyzedPost(
        post=CollectedPost(**post_data),
        short_title=data.get("short_title", ""),
        summary=data.get("summary", ""),
        primary_category=data.get("primary_category", ""),
        secondary_category=data.get("secondary_category", ""),
        sentiment_score=int(data.get("sentiment_score", 5)),
        heat_score=int(data.get("heat_score", 0)),
        suggestion_core=data.get("suggestion_core", ""),
        analysis_error=data.get("analysis_error"),
    )
