import os
import time
from datetime import datetime
from typing import Dict, Tuple

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ModerationLog

# Command cooldown: user_id -> (command, timestamp)
command_cooldowns: Dict[int, Tuple[str, float]] = {}

async def is_owner(message: Message):
    return message.from_user.id == int(os.getenv("OWNER_ID"))

async def get_target_user(client: Client, message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        return (await client.get_users(message.command[1])).id
    return None

async def bot_is_admin(client: Client, chat_id):
    me = await client.get_me()
    member = await client.get_chat_member(chat_id, me.id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

async def check_cooldown(user_id: int, command: str) -> bool:
    """
    Check if a user is on cooldown for a command.
    Returns True if the user can execute the command, False otherwise.
    """
    cooldown_time = 2.0  # 2 seconds cooldown
    current_time = time.time()

    if user_id in command_cooldowns:
        last_command, last_time = command_cooldowns[user_id]
        if current_time - last_time < cooldown_time:
            return False

    # Update the cooldown
    command_cooldowns[user_id] = (command, current_time)
    return True

async def log_action(
    client: Client,
    db_session: AsyncSession,
    group_id: int,
    user_id: int,
    admin_id: int,
    action: str
):
    """
    Log a moderation action to the database and owner's private chat.
    """
    # Log to database
    log_entry = ModerationLog(
        group_id=group_id,
        user_id=user_id,
        admin_id=admin_id,
        action=action
    )
    db_session.add(log_entry)
    await db_session.commit()

    # Log to owner's private chat
    owner_id = int(os.getenv("OWNER_ID"))
    try:
        group = await client.get_chat(group_id)
        user = await client.get_users(user_id)
        admin = await client.get_users(admin_id)

        log_message = (
            f"🛡 **Moderation Action** 🛡\n"
            f"**Group:** {group.title} (`{group_id}`)\n"
            f"**User:** {user.first_name} (`{user_id}`)\n"
            f"**Admin:** {admin.first_name} (`{admin_id}`)\n"
            f"**Action:** {action}\n"
            f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await client.send_message(owner_id, log_message)
    except Exception as e:
        print(f"Error sending log to owner: {e}")

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """
    Check if a user is an admin in a chat.
    """
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False
