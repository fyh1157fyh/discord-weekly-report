from __future__ import annotations

import json
import re
from typing import Any, Protocol

import httpx

from .analyzer import analyze_posts_locally
from .config import Settings
from .models import AnalyzedPost, CollectedPost
from .scoring import heat_score


FORBIDDEN_TITLE_WORDS = ["玩家建议", "体验优化", "相关反馈", "相关建议", "待人工确认", "待分类"]


class AsyncPostClient(Protocol):
    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        ...


async def analyze_posts(
    posts: list[CollectedPost],
    settings: Settings,
    *,
    client: AsyncPostClient | None = None,
) -> list[AnalyzedPost]:
    if not _ai_enabled(settings):
        return analyze_posts_locally(posts)

    close_client = client is None
    http_client = client or httpx.AsyncClient(timeout=60)
    results: list[AnalyzedPost] = []
    try:
        for chunk in _chunks(posts, settings.ai_batch_size):
            results.extend(await _analyze_chunk(chunk, settings, http_client))
    finally:
        if close_client and isinstance(http_client, httpx.AsyncClient):
            await http_client.aclose()
    return results


def _ai_enabled(settings: Settings) -> bool:
    return bool(settings.enable_ai_analysis and settings.ai_api_key and settings.ai_base_url and settings.ai_model)


async def _analyze_chunk(
    posts: list[CollectedPost],
    settings: Settings,
    client: AsyncPostClient,
) -> list[AnalyzedPost]:
    local_fallbacks = {str(post.post_id): analyze_posts_locally([post])[0] for post in posts}
    try:
        response = await client.post(
            _chat_completions_url(settings.ai_base_url),
            headers={
                "Authorization": f"Bearer {settings.ai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.ai_model,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": _analysis_prompt(posts)}],
            },
        )
        response.raise_for_status()
        ai_items = _extract_ai_items(response.json())
        return [_merge_ai_result(post, ai_items.get(str(post.post_id)), local_fallbacks[str(post.post_id)]) for post in posts]
    except Exception as exc:
        return [_fallback_with_error(local_fallbacks[str(post.post_id)], f"AI batch failed: {exc}") for post in posts]


def _analysis_prompt(posts: list[CollectedPost]) -> str:
    payload = [
        {
            "id": str(post.post_id),
            "title": post.title,
            "starter_content": post.starter_content,
            "conversation": post.conversation[:10],
            "reply_count": post.reply_count,
            "participant_count": post.participant_count,
            "reaction_total": post.reaction_stats.total,
            "positive_reactions": post.reaction_stats.positive,
            "negative_reactions": post.reaction_stats.negative,
        }
        for post in posts
    ]
    return (
        "你是游戏 Discord 社区舆情分析助手。请逐条理解玩家帖子的真实诉求，输出简体中文 JSON。\n"
        "分析步骤：1. 判断玩家遇到的问题或不满点；2. 选择模块分类和二级分类；"
        "3. 提炼具体改进建议；4. 给出满意度分。\n"
        "输出要求：只返回 JSON 对象，格式为 {\"items\": [...]}。\n"
        "每个 item 必须包含：id, short_title, summary, suggestion_core, "
        "primary_category, secondary_category, sentiment_score。\n"
        "short_title 必须是 6-12 字的中文问题标题，像“商店增加燃油”“活动积分异常”；"
        "不要写“玩家建议”“体验优化”“相关反馈”“待人工确认”等泛词。\n"
        "summary 只说明玩家遇到什么问题或为什么不满，不写空泛评价。\n"
        "suggestion_core 写玩家希望怎么改；如果原文没有明确方案，写“无明确建议”。\n"
        "sentiment_score 为 1-10，1 表示极度不满，10 表示非常满意。\n"
        "所有输出必须是中文；游戏英文专有名词可保留，但不能整句英文。\n"
        "待分析数据：\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def _extract_ai_items(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = _loads_json_object(content)
    items = parsed.get("items") if isinstance(parsed, dict) else parsed
    if not isinstance(items, list):
        raise ValueError("AI response must contain an items array.")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict) and item.get("id") is not None:
            result[str(item["id"])] = item
    return result


def _loads_json_object(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(1))


def _merge_ai_result(post: CollectedPost, ai_item: dict[str, Any] | None, fallback: AnalyzedPost) -> AnalyzedPost:
    if not ai_item:
        return _fallback_with_error(fallback, "AI item missing.")
    try:
        short_title = _clean_short_title(str(ai_item.get("short_title", "")), fallback.short_title)
        summary = _clean_text(str(ai_item.get("summary", "")), fallback.summary)
        suggestion_core = _clean_text(str(ai_item.get("suggestion_core", "")), "无明确建议")
        primary_category = _clean_text(str(ai_item.get("primary_category", "")), fallback.primary_category)
        secondary_category = _clean_text(str(ai_item.get("secondary_category", "")), fallback.secondary_category)
        sentiment_score = _safe_score(ai_item.get("sentiment_score"), fallback.sentiment_score)
        return AnalyzedPost(
            post=post,
            short_title=short_title,
            summary=summary,
            primary_category=primary_category,
            secondary_category=secondary_category,
            sentiment_score=sentiment_score,
            heat_score=heat_score(post),
            suggestion_core=suggestion_core,
        )
    except Exception as exc:
        return _fallback_with_error(fallback, f"AI item invalid: {exc}")


def _clean_short_title(value: str, fallback: str) -> str:
    title = _clean_text(value, fallback)
    for word in FORBIDDEN_TITLE_WORDS:
        title = title.replace(word, "")
    title = title.strip(" ：:，,。；;")
    if not title or any(word in title for word in FORBIDDEN_TITLE_WORDS):
        return fallback
    return title[:12]


def _clean_text(value: str, fallback: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned or cleaned.lower() in {"none", "null", "n/a"}:
        return fallback
    return cleaned


def _safe_score(value: Any, fallback: int) -> int:
    try:
        return max(1, min(10, int(float(value))))
    except (TypeError, ValueError):
        return fallback


def _fallback_with_error(item: AnalyzedPost, error: str) -> AnalyzedPost:
    item.analysis_error = error
    if not item.suggestion_core:
        item.suggestion_core = "无明确建议"
    return item


def _chat_completions_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return f"{base}/chat/completions"


def _chunks(values: list[CollectedPost], size: int) -> list[list[CollectedPost]]:
    return [values[index : index + size] for index in range(0, len(values), size)]
