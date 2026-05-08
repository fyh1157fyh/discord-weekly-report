from __future__ import annotations

from .models import CollectedPost, ReactionStats


POSITIVE_REACTIONS = {"👍", "💯", "⬆️", "✅", "❤️", "🔥"}
NEGATIVE_REACTIONS = {"👎", "⬇️", "❌"}


def reaction_stats_from_pairs(pairs: list[tuple[str, int]]) -> ReactionStats:
    stats = ReactionStats()
    for emoji, count in pairs:
        if emoji in POSITIVE_REACTIONS:
            stats.positive += count
        elif emoji in NEGATIVE_REACTIONS:
            stats.negative += count
        else:
            stats.other += count
    return stats


def heat_score(post: CollectedPost) -> int:
    return post.message_count * 3 + post.reaction_stats.total
