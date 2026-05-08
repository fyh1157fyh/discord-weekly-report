from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Settings
from .feishu.client import FeishuClient
from .feishu.publisher import feishu_receive_id, feishu_receive_id_type


async def _run() -> None:
    settings = Settings.from_env(require_sources=False, require_discord_token=False)
    for line in await verify_feishu_message(settings=settings):
        print(line)


async def verify_feishu_message(*, settings: Settings) -> list[str]:
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET are required.")
    if not feishu_receive_id(settings):
        raise ValueError("FEISHU_RECEIVE_ID or FEISHU_CHAT_ID is required.")
    client = FeishuClient(app_id=settings.feishu_app_id, app_secret=settings.feishu_app_secret)
    lines = ["1. 获取 tenant_access_token ..."]
    token = await client.tenant_access_token()
    lines.append("   OK: token 可获取")
    lines.append("2. 发送飞书测试卡片 ...")
    await client.send_interactive_card(
        token=token,
        receive_id_type=feishu_receive_id_type(settings),
        receive_id=feishu_receive_id(settings),
        card=_message_test_card(settings.feishu_report_title_prefix),
    )
    lines.append("   OK: 测试卡片已发送")
    return lines


def _message_test_card(title_prefix: str) -> dict:
    now = datetime.now(tz=ZoneInfo("Asia/Shanghai"))
    return {
        "config": {"wide_screen_mode": True},
        "header": {"template": "green", "title": {"tag": "plain_text", "content": f"{title_prefix} - 私聊发送测试"}},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**飞书消息发送测试**\n时间：{now:%Y-%m-%d %H:%M:%S}\n这不是正式周报。",
                },
            }
        ],
    }


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
