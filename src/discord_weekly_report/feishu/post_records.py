from __future__ import annotations

from typing import Any

from ..models import AnalyzedPost
from .client import FeishuClient


POST_DETAIL_FIELDS = [
    "AI短标题",
    "帖子链接",
    "模块分类",
    "二级分类",
    "状态",
    "满意度",
    "热度分",
    "回复数",
    "AI核心总结",
    "日期",
    "具体建议",
    "参与人数",
]


def post_to_bitable_record(item: AnalyzedPost) -> dict[str, Any]:
    post = item.post
    return {
        "AI短标题": item.short_title,
        "帖子链接": _url_value(post.url),
        "模块分类": item.primary_category,
        "二级分类": item.secondary_category,
        "状态": "新发现",
        "满意度": item.sentiment_score,
        "热度分": item.heat_score,
        "回复数": post.reply_count,
        "AI核心总结": item.summary,
        "日期": int(post.created_at.timestamp() * 1000),
        "具体建议": item.suggestion_core or post.starter_content or post.title,
        "参与人数": post.participant_count,
    }


def _url_value(url: str) -> dict[str, str]:
    return {"text": "查看原帖", "link": url}


async def validate_post_detail_fields(
    *,
    client: FeishuClient,
    token: str,
    app_token: str,
    table_id: str,
) -> set[str]:
    existing = await client.list_table_field_names(token=token, app_token=app_token, table_id=table_id)
    missing = [field for field in POST_DETAIL_FIELDS if field not in existing]
    if missing:
        raise ValueError(f"Feishu Bitable missing required post detail fields: {', '.join(missing)}")
    return existing


async def upsert_post_records(
    *,
    client: FeishuClient,
    token: str,
    app_token: str,
    table_id: str,
    records: list[dict[str, Any]],
) -> None:
    existing_links = await list_existing_post_links(
        client=client,
        token=token,
        app_token=app_token,
        table_id=table_id,
    )
    creates: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    for record in records:
        url = _extract_url(record["帖子链接"])
        existing_id = existing_links.get(url)
        if existing_id:
            updates.append({"record_id": existing_id, "fields": record})
        else:
            creates.append(record)

    for chunk in _chunks(creates, 100):
        await client.batch_create_records(token=token, app_token=app_token, table_id=table_id, records=chunk)
    for chunk in _chunks(updates, 100):
        await client.batch_update_records(token=token, app_token=app_token, table_id=table_id, records=chunk)


async def list_existing_post_links(
    *,
    client: FeishuClient,
    token: str,
    app_token: str,
    table_id: str,
) -> dict[str, str]:
    records = await client.list_records(token=token, app_token=app_token, table_id=table_id)
    result: dict[str, str] = {}
    for record in records:
        record_id = record.get("record_id")
        fields = record.get("fields", {})
        if not isinstance(record_id, str) or not isinstance(fields, dict):
            continue
        url = _extract_url(fields.get("帖子链接"))
        if url:
            result[url] = record_id
    return result


async def find_existing_post_record(
    *,
    client: FeishuClient,
    token: str,
    app_token: str,
    table_id: str,
    post_url: str,
) -> str | None:
    links = await list_existing_post_links(client=client, token=token, app_token=app_token, table_id=table_id)
    return links.get(post_url)


def _extract_url(value: Any) -> str:
    if isinstance(value, dict):
        link = value.get("link")
        return link if isinstance(link, str) else ""
    if isinstance(value, list):
        for item in value:
            url = _extract_url(item)
            if url:
                return url
        return ""
    return str(value) if value else ""


def _chunks(values: list[Any], size: int) -> list[list[Any]]:
    return [values[index : index + size] for index in range(0, len(values), size)]
