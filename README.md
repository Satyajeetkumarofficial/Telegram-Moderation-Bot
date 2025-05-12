# Telegram Moderation Bot

A powerful admin assistant for Telegram group chats, inspired by the "Miss Rose" bot. This bot provides moderation commands that can be used by the bot owner and group admins.

## Features

### Core Features

- **Bot Framework**: Uses Pyrogram for handling Telegram interactions.
- **API Backend**: Uses FastAPI to expose an admin dashboard and provide endpoints for moderation logs and stats.
- **Database**: Uses PostgreSQL to store user warnings, moderation logs, and group configurations.
- **Moderation Commands**:
  - `/kick`, `/ban`, `/unban`, `/mute`, `/unmute`, `/warn`, `/unwarn`, `/warnings` commands
  - Usable by the OWNER_ID and group admins
  - Work on both replies and @username mentions
  - Mute duration (optional) via arguments (e.g., `/mute @user 3600` for 1 hour)
  - Logs all moderation actions to the owner via private message and in the database
  - Warning system with auto-ban after 3 warnings (configurable)
  - Message deletion for banned users

### Permissions & Safety

- Restricts command access to OWNER_ID and group admins
- Handles exceptions gracefully:
  - Bot lacks admin rights
  - Target user not found
  - Target user is an admin
  - Rate limiting (FloodWait)
- Flood control and cooldown on commands to prevent abuse (1 command per 2 seconds)
- Comprehensive error handling and logging

### Dashboard API (FastAPI)

- Admin-only endpoints (secured with a token):
  - `/api/logs`: View recent moderation actions with filtering options
  - `/api/warns/{user_id}`: Get warnings for a user with details
  - `/api/groups`: List groups the bot is in with their configurations
  - `/api/stats`: Get overall statistics about the bot's usage

### Group Configuration

- **Welcome Messages**: Customizable welcome messages for new members
  - `/setwelcome` - Set a custom welcome message
- **Goodbye Messages**: Customizable goodbye messages for members who leave
  - `/setgoodbye` - Set a custom goodbye message
- **Group Rules**: Set and display group rules
  - `/setrules` - Set the rules for the group
  - `/rules` - Display the group rules
- **Warning Limit**: Configure the number of warnings before a ban
  - `/setwarnlimit` - Set the warning limit for the group
- **Join/Leave Notifications**: Automatically welcome new members and say goodbye to those who leave

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Telegram API credentials (API_ID, API_HASH, BOT_TOKEN)

### Environment Variables

Create a `.env` file with the following variables:

```
# Telegram API credentials
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Bot configuration
OWNER_ID=your_telegram_user_id

# Database configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost/telegram_bot

# API configuration
API_TOKEN=your_api_token
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-moderation-bot.git
cd telegram-moderation-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
uvicorn main:app --reload
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

## API Documentation

Once the application is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage

### Basic Commands

- `/ping` - Check if the bot is alive

### Moderation Commands (Admin & Owner)

- `/kick` - Kick a user from the group
- `/ban` - Ban a user from the group
- `/unban` - Unban a user from the group
- `/mute [duration]` - Mute a user in the group (duration in seconds)
- `/unmute` - Unmute a user in the group
- `/warn [reason]` - Warn a user with an optional reason
- `/unwarn` - Remove a warning from a user
- `/warnings` - Check warnings for a user

### Group Configuration Commands (Admin & Owner)

- `/setwelcome [message]` - Set a custom welcome message
- `/setgoodbye [message]` - Set a custom goodbye message
- `/setrules [rules]` - Set the rules for the group
- `/rules` - Display the group rules
- `/setwarnlimit [number]` - Set the warning limit for the group

### Message Placeholders

For welcome and goodbye messages, you can use these placeholders:
- `{user}` - User mention
- `{first_name}` - User's first name
- `{last_name}` - User's last name
- `{username}` - User's username
- `{group}` - Group name

## License

This project is licensed under the MIT License - see the LICENSE file for details.
