from __future__ import annotations

from pathlib import Path

from ..config import Settings
from ..models import WeeklyReport
from .cli_user import FeishuCliUserClient, validate_cli_user_fields
from .client import FeishuClient
from .post_records import post_to_bitable_record, upsert_post_records, validate_post_detail_fields


def feishu_receive_id_type(settings: Settings) -> str:
    return settings.feishu_receive_id_type or "chat_id"


def feishu_receive_id(settings: Settings) -> str:
    return settings.feishu_receive_id or settings.feishu_chat_id


async def publish_weekly_posts(*, settings: Settings, report: WeeklyReport, markdown_path: Path) -> None:
    _validate_settings(settings)
    if settings.feishu_write_mode == "cli_user":
        await _publish_with_cli_user(settings=settings, report=report)
        return
    if settings.feishu_write_mode != "bot":
        raise ValueError("FEISHU_WRITE_MODE must be 'bot' or 'cli_user'.")
    client = FeishuClient(app_id=settings.feishu_app_id, app_secret=settings.feishu_app_secret)
    token = await client.tenant_access_token()
    await validate_post_detail_fields(
        client=client,
        token=token,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
    )
    records = [post_to_bitable_record(item) for item in report.posts]
    await upsert_post_records(
        client=client,
        token=token,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
        records=records,
    )
    if feishu_receive_id(settings):
        await client.send_interactive_card(
            token=token,
            receive_id_type=feishu_receive_id_type(settings),
            receive_id=feishu_receive_id(settings),
            card=_card_for_report(settings.feishu_report_title_prefix, report, markdown_path),
        )


async def _publish_with_cli_user(*, settings: Settings, report: WeeklyReport) -> None:
    client = FeishuCliUserClient(cli_path=settings.lark_cli_path)
    await client.require_user_auth()
    await validate_cli_user_fields(
        client=client,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
    )
    await client.upsert_records(
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
        records=[post_to_bitable_record(item) for item in report.posts],
    )


def _validate_settings(settings: Settings) -> None:
    missing = [
        name
        for name, value in [
            ("FEISHU_BITABLE_APP_TOKEN", settings.feishu_bitable_app_token),
            ("FEISHU_BITABLE_TABLE_ID", settings.feishu_bitable_table_id),
        ]
        if not value
    ]
    if settings.feishu_write_mode != "cli_user":
        for name, value in [
            ("FEISHU_APP_ID", settings.feishu_app_id),
            ("FEISHU_APP_SECRET", settings.feishu_app_secret),
        ]:
            if not value:
                missing.append(name)
    if missing:
        raise ValueError(f"ENABLE_FEISHU=1 requires: {', '.join(missing)}")


def _card_for_report(title_prefix: str, report: WeeklyReport, markdown_path: Path) -> dict:
    top_posts = sorted(report.posts, key=lambda item: item.heat_score, reverse=True)[:5]
    lines = [f"周期：{report.start_at:%Y-%m-%d} 到 {report.end_at:%Y-%m-%d}", f"写入帖子：{len(report.posts)}", ""]
    lines.extend(f"**{index}. {item.short_title}**：热度 {item.heat_score}，参与 {item.post.participant_count}" for index, item in enumerate(top_posts, start=1))
    lines.extend(["", f"本地报告：{markdown_path}"])
    return {
        "config": {"wide_screen_mode": True},
        "header": {"template": "blue", "title": {"tag": "plain_text", "content": f"{title_prefix} - {report.week_label}"}},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}}],
    }
