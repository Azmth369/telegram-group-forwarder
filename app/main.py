import asyncio
import logging

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

from app.config import (
    API_HASH,
    API_ID,
    DESTINATION_CHANNEL_ID,
    SESSION_STRING,
    SOURCE_GROUP_ID,
)
from app.logger import setup_logging


setup_logging()
logger = logging.getLogger("telegram-group-forwarder")

client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH,
    connection_retries=None,
    retry_delay=5,
)


async def is_human_message(message) -> bool:
    try:
        sender = await message.get_sender()

        if sender is None:
            return True

        return not bool(getattr(sender, "bot", False))
    except Exception:
        logger.exception("Could not inspect sender for message %s", message.id)
        return True


async def forward_with_retry(messages) -> None:
    try:
        await client.forward_messages(
            entity=DESTINATION_CHANNEL_ID,
            messages=messages,
            from_peer=SOURCE_GROUP_ID,
        )
    except FloodWaitError as exc:
        logger.warning("Telegram FloodWait: sleeping %s seconds", exc.seconds)
        await asyncio.sleep(exc.seconds)
        await client.forward_messages(
            entity=DESTINATION_CHANNEL_ID,
            messages=messages,
            from_peer=SOURCE_GROUP_ID,
        )


@client.on(events.Album(chats=SOURCE_GROUP_ID))
async def album_handler(event) -> None:
    messages = [
        message
        for message in event.messages
        if await is_human_message(message)
    ]

    if not messages:
        logger.info("Ignoring album %s: no human messages", event.grouped_id)
        return

    try:
        await forward_with_retry(messages)
        logger.info(
            "Forwarded album %s (%d message(s))",
            event.grouped_id,
            len(messages),
        )
    except Exception:
        logger.exception("Failed to forward album %s", event.grouped_id)


@client.on(events.NewMessage(chats=SOURCE_GROUP_ID))
async def message_handler(event) -> None:
    message = event.message

    # Albums are handled by Album above.
    if message.grouped_id:
        return

    if not await is_human_message(message):
        logger.info("Ignoring bot message %s", message.id)
        return

    try:
        await forward_with_retry(message)
        logger.info("Forwarded message %s", message.id)
    except Exception:
        logger.exception("Failed to forward message %s", message.id)


async def startup() -> None:
    logger.info("Starting Telegram Group Forwarder")

    await client.start()

    me = await client.get_me()
    account = (
        f"@{me.username}"
        if me.username
        else (me.first_name or "") + (" " + me.last_name if me.last_name else "")
    ).strip()

    source = await client.get_entity(SOURCE_GROUP_ID)
    destination = await client.get_entity(DESTINATION_CHANNEL_ID)

    logger.info("Logged in as: %s", account)
    logger.info("Source group: %s", getattr(source, "title", SOURCE_GROUP_ID))
    logger.info(
        "Destination channel: %s",
        getattr(destination, "title", DESTINATION_CHANNEL_ID),
    )
    logger.info("Forwarder is ready")


async def main() -> None:
    await startup()

    try:
        await client.run_until_disconnected()
    finally:
        await client.disconnect()
        logger.info("Telegram client disconnected")


if __name__ == "__main__":
    asyncio.run(main())
