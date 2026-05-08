from __future__ import annotations

from .models import CollectedPost


def filter_posts(posts: list[CollectedPost]) -> list[CollectedPost]:
    return [post for post in posts if post.starter_content.strip() or post.conversation]
