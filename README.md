# Telegram Group Forwarder

Personal-use Telegram group-to-channel forwarder built with Python and Telethon.

It listens to one private Telegram group using a Telegram user account and natively forwards messages from human members to one private Telegram channel.

## Features

- Text
- Photos
- Videos
- Documents/files
- Audio
- Voice messages
- GIFs/animations
- Stickers
- Video notes
- Media albums
- Other message types Telegram permits the account to forward
- Native Telegram forwarding; no download/re-upload pipeline
- Bot messages ignored
- Album messages forwarded as albums
- Group edits do not modify the channel copy
- Group deletions do not delete the channel copy
- No database or duplicate tracking in this initial version
- No Postman required

Telegram's own restrictions still apply. This project does not bypass protected-content or other Telegram restrictions.

## Local setup

1. Create Telegram API credentials at:
   https://my.telegram.org

2. Clone this repository.

3. Create a virtual environment:

    python -m venv .venv

   Windows:

    .venv\Scripts\activate

4. Install dependencies:

    pip install -r requirements.txt

5. Copy .env.example to .env.

6. Put API_ID and API_HASH into .env.

7. Generate a StringSession:

    python scripts/generate_session.py

   Complete Telegram login. If two-step verification is enabled, enter the password when requested.

8. Put the printed SESSION_STRING into .env.

9. Set the source group and destination channel IDs:

    SOURCE_GROUP_ID=-1001234567890
    DESTINATION_CHANNEL_ID=-1009876543210

10. Run:

    python -m app.main

11. Send test content in the source group and verify it appears in the destination channel.

## Render deployment

The repository includes render.yaml and a Dockerfile.

Use a Render Background Worker. Set these environment variables in Render:

- API_ID
- API_HASH
- SESSION_STRING
- SOURCE_GROUP_ID
- DESTINATION_CHANNEL_ID

LOG_LEVEL can remain INFO.

The authenticated Telegram account must have access to both the source group and destination channel.

A Background Worker is used because the application maintains a long-running Telegram connection and does not need an HTTP server.

## Security

Never commit .env, SESSION_STRING, Telegram API credentials, or .session files.

Treat SESSION_STRING as a secret credential.

## Postman

Postman is not required. The initial architecture has no REST API endpoint.

## Troubleshooting

If messages do not forward, verify:

1. The user account is a member of the source group.
2. The user account can post in the destination channel.
3. The numeric IDs are correct.
4. Telegram has not restricted forwarding for the content.
5. Render logs contain "Forwarder is ready".

If the Telegram session becomes invalid, generate a fresh StringSession locally and update the Render SESSION_STRING environment variable.

If Telegram returns FloodWait, the application waits for the requested period and retries the forward.

## Architecture

    Private Telegram Group
             |
             v
    Telegram User Account
           Telethon
             |
             v
    Native Telegram Forward
             |
             v
    Private Telegram Channel
