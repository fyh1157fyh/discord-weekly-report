from __future__ import annotations

import logging
import asyncio
from datetime import datetime

import discord

from .date_range import WeekRange
from .models import CollectedMessage, CollectedPost, ReactionStats, SourceType
from .scoring import reaction_stats_from_pairs

logger = logging.getLogger(__name__)
RETRYABLE_DISCORD_ERRORS = (
    discord.DiscordServerError,
    discord.HTTPException,
)


async def collect_posts(
    *,
    client: discord.Client,
    guild_id: int,
    forum_channel_ids: list[int],
    thread_channel_ids: list[int],
    week: WeekRange,
    max_messages_per_thread: int,
) -> list[CollectedPost]:
    guild = client.get_guild(guild_id)
    if guild is None:
        guild = await client.fetch_guild(guild_id)

    collected: list[CollectedPost] = []
    seen_thread_ids: set[int] = set()
    for channel_id in forum_channel_ids:
        channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
        if not isinstance(channel, discord.ForumChannel):
            logger.warning("Channel %s is not a forum channel; skipping.", channel_id)
            continue
        for thread in await _forum_threads(channel, week):
            await _append_thread(collected, seen_thread_ids, thread, "forum", channel.name, week, max_messages_per_thread)

    for channel_id in thread_channel_ids:
        channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            logger.warning("Channel %s is not a text channel; skipping.", channel_id)
            continue
        for thread in await _text_channel_threads(channel, week):
            await _append_thread(collected, seen_thread_ids, thread, "thread", channel.name, week, max_messages_per_thread)
    return collected


async def collect_text_messages(
    *,
    client: discord.Client,
    channel_ids: list[int],
    week: WeekRange,
    max_messages_per_channel: int,
) -> list[CollectedMessage]:
    collected: list[CollectedMessage] = []
    for channel_id in channel_ids:
        channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            logger.warning("Channel %s is not a text channel; skipping.", channel_id)
            continue
        messages = await _history_with_retry(
            channel,
            limit=max_messages_per_channel,
            after=week.start_at,
            before=week.end_at,
            oldest_first=True,
            label=f"text channel {channel.id}",
        )
        for message in messages:
            if message.author.bot or not message.content.strip():
                continue
            collected.append(
                CollectedMessage(
                    message_id=message.id,
                    channel_id=channel.id,
                    channel_name=channel.name,
                    author=message.author.display_name,
                    content=message.content,
                    created_at=message.created_at.astimezone(week.start_at.tzinfo),
                    url=message.jump_url,
                    author_id=message.author.id,
                )
            )
    return collected


async def _append_thread(
    collected: list[CollectedPost],
    seen_thread_ids: set[int],
    thread: discord.Thread,
    source_type: SourceType,
    parent_name: str,
    week: WeekRange,
    max_messages: int,
) -> None:
    if thread.id in seen_thread_ids:
        return
    seen_thread_ids.add(thread.id)
    post = await _thread_to_post(thread, source_type, parent_name, week, max_messages)
    if post:
        collected.append(post)


async def _forum_threads(channel: discord.ForumChannel, week: WeekRange) -> list[discord.Thread]:
    threads = list(channel.threads)
    threads.extend(await _archived_threads(channel, week.end_at))
    return [thread for thread in threads if _in_week(thread.created_at, week)]


async def _text_channel_threads(channel: discord.TextChannel, week: WeekRange) -> list[discord.Thread]:
    threads = list(channel.threads)
    threads.extend(await _archived_threads(channel, week.end_at))
    return [thread for thread in threads if _in_week(thread.created_at, week)]


async def _archived_threads(channel: discord.ForumChannel | discord.TextChannel, before: datetime) -> list[discord.Thread]:
    threads: list[discord.Thread] = []
    try:
        async for thread in channel.archived_threads(limit=100, before=before):
            threads.append(thread)
    except discord.Forbidden:
        logger.warning("Missing permission to read archived threads for channel %s.", channel.id)
    return threads


async def _thread_to_post(
    thread: discord.Thread,
    source_type: SourceType,
    parent_name: str,
    week: WeekRange,
    max_messages: int,
) -> CollectedPost | None:
    history = await _history_with_retry(
        thread,
        limit=max_messages,
        oldest_first=True,
        label=f"thread {thread.id}",
    )
    messages = [message for message in history if not message.author.bot]
    if not messages:
        return None
    starter = messages[0]
    if not _in_week(starter.created_at, week) and not _in_week(thread.created_at, week):
        return None
    participant_ids = sorted({message.author.id for message in messages})
    participant_names = {message.author.display_name for message in messages}
    conversation = [
        f"{message.author.display_name}: {message.content}"
        for message in messages
        if message.content.strip()
    ]
    return CollectedPost(
        post_id=thread.id,
        source_type=source_type,
        channel_name=parent_name,
        title=thread.name,
        author=starter.author.display_name,
        starter_content=starter.content or "",
        reply_count=max(len(messages) - 1, 0),
        message_count=len(messages),
        reaction_stats=_message_reactions(starter),
        participant_count=len(participant_ids or participant_names),
        created_at=thread.created_at.astimezone(week.start_at.tzinfo),
        archived=thread.archived,
        url=starter.jump_url,
        conversation=conversation,
        author_id=starter.author.id,
        participant_ids=participant_ids,
    )


def _message_reactions(message: discord.Message) -> ReactionStats:
    return reaction_stats_from_pairs([(str(reaction.emoji), reaction.count) for reaction in message.reactions])


async def _history_with_retry(target, *, label: str, attempts: int = 3, **kwargs) -> list[discord.Message]:
    for attempt in range(1, attempts + 1):
        try:
            return [message async for message in target.history(**kwargs)]
        except RETRYABLE_DISCORD_ERRORS as exc:
            if attempt >= attempts:
                raise
            wait_seconds = attempt * 2
            logger.warning("Discord history read failed for %s; retrying in %ss: %s", label, wait_seconds, exc)
            await asyncio.sleep(wait_seconds)
    return []


def _in_week(value: datetime, week: WeekRange) -> bool:
    return week.start_at.astimezone(value.tzinfo) <= value < week.end_at.astimezone(value.tzinfo)
