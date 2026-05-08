from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Settings
from .feishu.cli_user import FeishuCliUserClient, validate_cli_user_fields
from .feishu.client import FeishuClient
from .feishu.post_records import (
    POST_DETAIL_FIELDS,
    find_existing_post_record,
    upsert_post_records,
    validate_post_detail_fields,
)


VERIFY_POST_URL = "https://discord-weekly-report.local/__verify__"


async def _run() -> None:
    settings = Settings.from_env(require_sources=False, require_discord_token=False)
    for line in await verify_feishu(settings=settings):
        print(line)


async def verify_feishu(*, settings: Settings) -> list[str]:
    _validate(settings)
    if settings.feishu_write_mode == "cli_user":
        return await _verify_cli_user(settings)
    if settings.feishu_write_mode != "bot":
        raise ValueError("FEISHU_WRITE_MODE must be 'bot' or 'cli_user'.")
    client = FeishuClient(app_id=settings.feishu_app_id, app_secret=settings.feishu_app_secret)
    lines = ["1. 获取 tenant_access_token ..."]
    token = await client.tenant_access_token()
    lines.append("   OK: token 可获取")
    lines.append("2. 检查帖子级明细表字段 ...")
    fields = await validate_post_detail_fields(
        client=client,
        token=token,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
    )
    lines.append(f"   OK: 必需字段齐全，共读取到 {len(fields)} 个字段")
    lines.append("3. 检查测试记录写入/更新/查询 ...")
    record = _verification_record()
    await upsert_post_records(
        client=client,
        token=token,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
        records=[record],
    )
    existing = await find_existing_post_record(
        client=client,
        token=token,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
        post_url=VERIFY_POST_URL,
    )
    if not existing:
        raise RuntimeError("Feishu verification record was not found after upsert.")
    lines.append("   OK: __verify__ 测试记录可写入/更新/查询")
    return lines


async def _verify_cli_user(settings: Settings) -> list[str]:
    client = FeishuCliUserClient(cli_path=settings.lark_cli_path)
    lines = ["1. 检查 lark-cli 用户登录态 ..."]
    await client.require_user_auth()
    lines.append("   OK: lark-cli user token 可用")
    lines.append("2. 检查帖子级明细表字段 ...")
    fields = await validate_cli_user_fields(
        client=client,
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
    )
    lines.append(f"   OK: 必需字段齐全，共读取到 {len(fields)} 个字段")
    lines.append("3. 检查测试记录写入/更新/查询 ...")
    await client.upsert_records(
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
        records=[_verification_record()],
    )
    existing = await client.list_existing_post_links(
        app_token=settings.feishu_bitable_app_token,
        table_id=settings.feishu_bitable_table_id,
    )
    if VERIFY_POST_URL not in existing:
        raise RuntimeError("Feishu verification record was not found after CLI upsert.")
    lines.append("   OK: __verify__ 测试记录可写入/更新/查询")
    return lines


def _verification_record() -> dict:
    return {
        "AI短标题": "__verify__",
        "帖子链接": {"text": "__verify__", "link": VERIFY_POST_URL},
        "模块分类": "未分类",
        "二级分类": "待人工确认",
        "状态": "新发现",
        "满意度": 0,
        "热度分": 0,
        "回复数": 0,
        "AI核心总结": "飞书多维表格写入验证记录，可保留或手动删除。",
        "日期": int(datetime.now(tz=ZoneInfo("Asia/Shanghai")).timestamp() * 1000),
        "具体建议": "无需处理。",
        "参与人数": 0,
    }


def _validate(settings: Settings) -> None:
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
        raise ValueError(f"verify_feishu requires: {', '.join(missing)}")
    if not POST_DETAIL_FIELDS:
        raise RuntimeError("POST_DETAIL_FIELDS is unexpectedly empty.")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
