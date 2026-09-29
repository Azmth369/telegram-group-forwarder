import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


load_dotenv()


async def main() -> None:
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    if not api_id or not api_hash:
        raise RuntimeError("Set API_ID and API_HASH in .env before running this script.")

    client = TelegramClient(StringSession(), int(api_id), api_hash)

    print("Telegram login starting...")
    print("Use your Telegram phone number, login code, and 2FA password if enabled.")

    await client.start()

    session_string = client.session.save()

    print("\nSESSION_STRING:")
    print(session_string)
    print("\nKeep this value secret.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
