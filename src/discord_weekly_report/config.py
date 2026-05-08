from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


def _split_ids(value: str | None, *, env_name: str) -> list[int]:
    if not value:
        return []
    ids: list[int] = []
    for item in value.split(","):
        text = item.strip()
        if not text:
            continue
        try:
            ids.append(int(text))
        except ValueError as exc:
            raise ValueError(
                f"{env_name} must be Discord numeric channel IDs separated by commas; "
                f"got {text!r}. Put topic names like 'arena' in ACTIVE_TOPIC_KEYS instead."
            ) from exc
    return ids


def _split_strings(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    discord_guild_id: int
    discord_forum_channel_ids: list[int]
    discord_thread_channel_ids: list[int]
    discord_text_channel_ids: list[int]
    timezone: ZoneInfo
    output_dir: Path
    max_messages_per_thread: int = 200
    max_text_messages_per_channel: int = 1000
    discord_message_content_intent: bool = True
    active_topic_keys: list[str] = field(default_factory=list)
    text_message_context_before: int = 2
    text_message_context_after: int = 2
    enable_feishu: bool = False
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_bitable_app_token: str = ""
    feishu_bitable_table_id: str = ""
    feishu_write_mode: str = "bot"
    lark_cli_path: str = ""
    feishu_report_title_prefix: str = "Discord 舆情周报"
    top_issues_limit: int = 5
    feishu_receive_id_type: str = ""
    feishu_receive_id: str = ""
    feishu_chat_id: str = ""
    enable_ai_analysis: bool = False
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""
    ai_batch_size: int = 20

    @classmethod
    def from_env(
        cls,
        *,
        require_sources: bool = True,
        require_discord_token: bool = True,
    ) -> "Settings":
        load_dotenv()
        required = ["DISCORD_BOT_TOKEN"] if require_discord_token else []
        if require_sources:
            required.append("DISCORD_GUILD_ID")
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        forum_ids = _split_ids(
            os.getenv("DISCORD_FORUM_CHANNEL_IDS"),
            env_name="DISCORD_FORUM_CHANNEL_IDS",
        )
        thread_ids = _split_ids(
            os.getenv("DISCORD_THREAD_CHANNEL_IDS"),
            env_name="DISCORD_THREAD_CHANNEL_IDS",
        )
        if require_sources and not forum_ids and not thread_ids:
            raise ValueError("Set DISCORD_FORUM_CHANNEL_IDS or DISCORD_THREAD_CHANNEL_IDS.")

        return cls(
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
            discord_guild_id=int(os.getenv("DISCORD_GUILD_ID", "0") or "0"),
            discord_forum_channel_ids=forum_ids,
            discord_thread_channel_ids=thread_ids,
            discord_text_channel_ids=_split_ids(
                os.getenv("DISCORD_TEXT_CHANNEL_IDS"),
                env_name="DISCORD_TEXT_CHANNEL_IDS",
            ),
            timezone=ZoneInfo(os.getenv("TIMEZONE", "Asia/Shanghai")),
            output_dir=Path(os.getenv("OUTPUT_DIR", ".")).resolve(),
            max_messages_per_thread=int(os.getenv("MAX_MESSAGES_PER_THREAD", "200")),
            max_text_messages_per_channel=int(os.getenv("MAX_TEXT_MESSAGES_PER_CHANNEL", "1000")),
            discord_message_content_intent=os.getenv("DISCORD_MESSAGE_CONTENT_INTENT", "1") == "1",
            active_topic_keys=_split_strings(os.getenv("ACTIVE_TOPIC_KEYS", "arena")),
            text_message_context_before=int(os.getenv("TEXT_MESSAGE_CONTEXT_BEFORE", "2")),
            text_message_context_after=int(os.getenv("TEXT_MESSAGE_CONTEXT_AFTER", "2")),
            enable_feishu=os.getenv("ENABLE_FEISHU", "0") == "1",
            feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            feishu_bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", ""),
            feishu_bitable_table_id=os.getenv("FEISHU_BITABLE_TABLE_ID", ""),
            feishu_write_mode=os.getenv("FEISHU_WRITE_MODE", "bot").strip().casefold() or "bot",
            lark_cli_path=os.getenv("LARK_CLI_PATH", ""),
            feishu_report_title_prefix=os.getenv("FEISHU_REPORT_TITLE_PREFIX", "Discord 舆情周报"),
            top_issues_limit=int(os.getenv("TOP_ISSUES_LIMIT", "5")),
            feishu_receive_id_type=os.getenv("FEISHU_RECEIVE_ID_TYPE", ""),
            feishu_receive_id=os.getenv("FEISHU_RECEIVE_ID", ""),
            feishu_chat_id=os.getenv("FEISHU_CHAT_ID", ""),
            enable_ai_analysis=os.getenv("ENABLE_AI_ANALYSIS", "0") == "1",
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_base_url=os.getenv("AI_BASE_URL", ""),
            ai_model=os.getenv("AI_MODEL", ""),
            ai_batch_size=max(1, int(os.getenv("AI_BATCH_SIZE", "20"))),
        )
