from __future__ import annotations

import asyncio
import logging

from .ai_analyzer import analyze_posts
from .collector import collect_posts, collect_text_messages
from .config import Settings
from .date_range import previous_full_week
from .discord_client import ReportDiscordClient, run_with_client
from .feishu.publisher import publish_weekly_posts
from .filters import filter_posts
from .logging_setup import setup_logging
from .models import WeeklyReport
from .paths import ensure_output_paths
from .report_writer import write_outputs
from .topic_filter import build_topic_report
from .topic_report_writer import write_topic_outputs
from .topics import default_topics_path, load_topics

logger = logging.getLogger(__name__)


async def _run() -> None:
    setup_logging()
    settings = Settings.from_env()
    week = previous_full_week(timezone=settings.timezone)
    paths = ensure_output_paths(settings.output_dir, week.label)
    topics = load_topics(default_topics_path(settings.output_dir), settings.active_topic_keys)

    async def callback(client: ReportDiscordClient) -> None:
        logger.info("Collecting Discord posts for %s.", week.label)
        raw_posts = await collect_posts(
            client=client,
            guild_id=settings.discord_guild_id,
            forum_channel_ids=settings.discord_forum_channel_ids,
            thread_channel_ids=settings.discord_thread_channel_ids,
            week=week,
            max_messages_per_thread=settings.max_messages_per_thread,
        )
        filtered_posts = filter_posts(raw_posts)
        analyzed_posts = await analyze_posts(filtered_posts, settings)
        report = WeeklyReport(
            week_label=week.label,
            start_at=week.start_at,
            end_at=week.end_at,
            total_posts=len(filtered_posts),
            successful_analyses=sum(1 for item in analyzed_posts if not item.analysis_error),
            failed_analyses=sum(1 for item in analyzed_posts if item.analysis_error),
            posts=analyzed_posts,
        )
        write_outputs(paths, raw_posts, report)
        logger.info("Wrote local reports for %s.", week.label)

        if topics:
            text_messages = await collect_text_messages(
                client=client,
                channel_ids=settings.discord_text_channel_ids,
                week=week,
                max_messages_per_channel=settings.max_text_messages_per_channel,
            )
            for topic in topics:
                topic_report = build_topic_report(
                    topic=topic,
                    week_label=week.label,
                    start_at=week.start_at,
                    end_at=week.end_at,
                    posts=analyzed_posts,
                    messages=text_messages,
                    default_context_before=settings.text_message_context_before,
                    default_context_after=settings.text_message_context_after,
                )
                write_topic_outputs(
                    data_dir=paths.topics_data_dir,
                    reports_dir=paths.topics_reports_dir,
                    topic_report=topic_report,
                )
        if settings.enable_feishu:
            try:
                await publish_weekly_posts(settings=settings, report=report, markdown_path=paths.markdown)
                logger.info("Published post detail records to Feishu.")
            except Exception:
                logger.exception("Failed to publish to Feishu; local files were kept.")

    await run_with_client(
        settings.discord_bot_token,
        callback,
        message_content_intent=settings.discord_message_content_intent,
    )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
