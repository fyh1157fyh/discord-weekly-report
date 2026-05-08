from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

import discord

logger = logging.getLogger(__name__)


class ReportDiscordClient(discord.Client):
    def __init__(
        self,
        on_ready_callback: Callable[["ReportDiscordClient"], Awaitable[None]],
        *,
        message_content_intent: bool = True,
    ) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = message_content_intent
        intents.reactions = True
        super().__init__(intents=intents)
        self._on_ready_callback = on_ready_callback
        self.callback_error: BaseException | None = None

    async def on_ready(self) -> None:
        logger.info("Logged in as %s", self.user)
        try:
            await self._on_ready_callback(self)
        except BaseException as exc:
            self.callback_error = exc
            logger.exception("Discord ready callback failed.")
        finally:
            await self.close()


async def run_with_client(
    token: str,
    callback: Callable[[ReportDiscordClient], Awaitable[None]],
    *,
    message_content_intent: bool = True,
) -> None:
    client = ReportDiscordClient(callback, message_content_intent=message_content_intent)
    await client.start(token)
    if client.callback_error:
        raise client.callback_error
