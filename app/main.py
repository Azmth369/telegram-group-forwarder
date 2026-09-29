import asyncio
import logging
import os

from telegram import Update
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from app.config import (
    BOT_TOKEN,
    DESTINATION_CHANNEL_ID,
    SOURCE_GROUP_ID,
)
from app.logger import setup_logging


setup_logging()
logger = logging.getLogger("telegram-group-forwarder")

album_buffers: dict[str, set[int]] = {}
album_tasks: dict[str, asyncio.Task] = {}


async def forward_with_retry(bot, message_ids: list[int]) -> None:
    while True:
        try:
            await bot.forward_messages(
                chat_id=DESTINATION_CHANNEL_ID,
                from_chat_id=SOURCE_GROUP_ID,
                message_ids=message_ids,
            )
            return
        except RetryAfter as exc:
            logger.warning(
                "Telegram rate limit: sleeping %s seconds",
                exc.retry_after,
            )
            await asyncio.sleep(exc.retry_after)
        except (TimedOut, NetworkError):
            logger.warning("Telegram network error while forwarding; retrying")
            await asyncio.sleep(5)


async def flush_album(media_group_id: str, bot) -> None:
    try:
        await asyncio.sleep(1.5)

        message_ids = sorted(album_buffers.pop(media_group_id, set()))
        if not message_ids:
            return

        await forward_with_retry(bot, message_ids)

        logger.info(
            "Forwarded album %s (%d message(s))",
            media_group_id,
            len(message_ids),
        )
    except BadRequest as exc:
        logger.error(
            "Could not forward album %s: %s",
            media_group_id,
            exc,
        )
    except Exception:
        logger.exception("Failed to forward album %s", media_group_id)
    finally:
        album_tasks.pop(media_group_id, None)


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    chat = update.effective_chat

    logger.info(
        "Received update %s: type=%s chat_id=%s chat_type=%s chat_title=%s message_id=%s",
        update.update_id,
        type(update).__name__,
        chat.id if chat else None,
        chat.type if chat else None,
        chat.title if chat else None,
        message.message_id if message else None,
    )

    if message is None or chat is None:
        logger.info("Ignoring update %s: no effective message/chat", update.update_id)
        return

    if chat.id != SOURCE_GROUP_ID:
        logger.info(
            "Ignoring update %s: chat_id %s does not match SOURCE_GROUP_ID %s",
            update.update_id,
            chat.id,
            SOURCE_GROUP_ID,
        )
        return

    if message.from_user and message.from_user.is_bot:
        logger.info("Ignoring bot message %s", message.message_id)
        return

    media_group_id = message.media_group_id

    if media_group_id:
        album_buffers.setdefault(media_group_id, set()).add(message.message_id)

        task = album_tasks.get(media_group_id)
        if task is None or task.done():
            task = asyncio.create_task(
                flush_album(media_group_id, context.bot)
            )
            album_tasks[media_group_id] = task

        return

    try:
        await forward_with_retry(context.bot, [message.message_id])
        logger.info("Forwarded message %s", message.message_id)
    except BadRequest as exc:
        logger.error(
            "Could not forward message %s: %s",
            message.message_id,
            exc,
        )
    except Exception:
        logger.exception(
            "Failed to forward message %s",
            message.message_id,
        )


async def post_init(application: Application) -> None:
    bot = application.bot
    me = await bot.get_me()

    source = await bot.get_chat(SOURCE_GROUP_ID)
    destination = await bot.get_chat(DESTINATION_CHANNEL_ID)

    logger.info("Logged in as bot: @%s", me.username or me.first_name)
    logger.info(
        "Source group: %s (%s)",
        source.title or SOURCE_GROUP_ID,
        SOURCE_GROUP_ID,
    )
    logger.info(
        "Destination channel: %s (%s)",
        destination.title or DESTINATION_CHANNEL_ID,
        DESTINATION_CHANNEL_ID,
    )
    logger.info("Forwarder is ready")


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    logger.error(
        "Unhandled Telegram update error: %s",
        context.error,
        exc_info=context.error,
    )


def main() -> None:
    logger.info("Starting Telegram Bot Group Forwarder")

    port = int(os.getenv("PORT", "10000"))
    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if not render_url:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL is missing. This deployment is intended for a Render Web Service."
        )

    webhook_url = f"{render_url.rstrip('/')}/telegram"

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(
        MessageHandler(filters.ALL, message_handler)
    )
    application.add_error_handler(error_handler)

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram",
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        secret_token=BOT_TOKEN.split(":")[0],
    )


if __name__ == "__main__":
    main()
