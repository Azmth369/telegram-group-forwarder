import os

from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


BOT_TOKEN = required("BOT_TOKEN")
SOURCE_GROUP_ID = int(required("SOURCE_GROUP_ID"))
DESTINATION_CHANNEL_ID = int(required("DESTINATION_CHANNEL_ID"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
