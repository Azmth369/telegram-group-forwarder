# Telegram Group Forwarder

Personal-use Telegram group-to-channel forwarder built with Python and the Telegram Bot API.

The bot listens to one private Telegram group and natively forwards human-member messages to one private Telegram channel.

## Features
- Text, photos, videos, documents/files, audio, voice, GIFs, stickers, video notes, and other forwardable message types
- Native Telegram forwarding; no download/re-upload pipeline
- Album grouping preserved
- Bot messages ignored
- Source edits/deletions do not modify already-forwarded messages
- No database or duplicate tracking
- No user-account session or StringSession
- No Postman required

Telegram restrictions still apply. Protected-content messages cannot be forwarded by the Bot API.

## Bot setup
1. Create the bot with @BotFather.
2. Keep the bot token secret.
3. Add the bot to the source group.
4. Make the bot an administrator in the source group so it receives all group messages.
5. Add the bot to the destination channel and give it permission to post.
6. Disable source-chat content protection if you need those messages forwarded.

## Environment variables
Create .env from .env.example:

    BOT_TOKEN=1234567890:your_bot_token
    SOURCE_GROUP_ID=-1001234567890
    DESTINATION_CHANNEL_ID=-1009876543210
    LOG_LEVEL=INFO

Never commit .env or the bot token.

## Local setup
1. Create a virtual environment: python -m venv .venv
2. Windows: .venv\\Scripts\\activate
3. Install dependencies: python -m pip install -r requirements.txt
4. Fill in .env.
5. Run: python -m app.main

## Render deployment
Use the Render Background Worker defined in render.yaml.
Set BOT_TOKEN, SOURCE_GROUP_ID, DESTINATION_CHANNEL_ID, and LOG_LEVEL in Render.
The worker uses long-running Bot API polling and does not need an HTTP server.

## Security
The bot token is a secret credential. If it is exposed, revoke/regenerate it with @BotFather and update Render.

## Troubleshooting
- Confirm the bot is an administrator in the source group.
- Confirm it can post in the destination channel.
- Confirm both numeric IDs are correct.
- Confirm source content is not protected.
- Check Render logs for Forwarder is ready.
- Send a new test message after the worker starts.

## Architecture
Private Telegram Group -> Telegram Bot -> Bot API -> Native Telegram Forward -> Private Telegram Channel
