from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus
from sqlalchemy.future import select
from database.connection import get_db
from database.models import GroupConfig
from bot.utils import log_action, check_cooldown, is_admin, is_owner
import asyncio

@Client.on_message(filters.command("ping"))
async def ping(client: Client, message: Message):
    await message.reply("Pong! 🏓")

@Client.on_chat_member_updated()
async def handle_member_update(client: Client, chat_member: ChatMemberUpdated):
    # Only process group chats
    if not chat_member.chat.type.name.startswith("SUPER") and not chat_member.chat.type.name.startswith("GROUP"):
        return

    # Get the old and new status
    old_status = chat_member.old_chat_member.status if chat_member.old_chat_member else None
    new_status = chat_member.new_chat_member.status if chat_member.new_chat_member else None

    # User joined the group
    if (old_status is None or old_status == ChatMemberStatus.LEFT or old_status == ChatMemberStatus.BANNED) and \
       (new_status == ChatMemberStatus.MEMBER or new_status == ChatMemberStatus.ADMINISTRATOR or new_status == ChatMemberStatus.OWNER):
        await handle_user_join(client, chat_member)

    # User left the group
    elif (old_status == ChatMemberStatus.MEMBER or old_status == ChatMemberStatus.ADMINISTRATOR or old_status == ChatMemberStatus.OWNER) and \
         (new_status == ChatMemberStatus.LEFT or new_status == ChatMemberStatus.BANNED):
        await handle_user_leave(client, chat_member)

async def handle_user_join(client: Client, chat_member: ChatMemberUpdated):
    try:
        # Get group config
        async for db in get_db():
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == chat_member.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            # If no config or no welcome message, use default
            welcome_message = "Welcome to the group, {user}!"
            if group_config and group_config.welcome_message:
                welcome_message = group_config.welcome_message

            # Format the message
            user = chat_member.new_chat_member.user
            formatted_message = welcome_message.format(
                user=user.mention,
                first_name=user.first_name,
                last_name=user.last_name or "",
                username=f"@{user.username}" if user.username else "",
                group=chat_member.chat.title
            )

            # Send the welcome message
            await client.send_message(chat_member.chat.id, formatted_message)

            # Log the action
            await log_action(
                client,
                db,
                chat_member.chat.id,
                user.id,
                0,  # No admin for this action
                "joined the group"
            )
    except Exception as e:
        print(f"Error in handle_user_join: {e}")

async def handle_user_leave(client: Client, chat_member: ChatMemberUpdated):
    try:
        # Get group config
        async for db in get_db():
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == chat_member.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            # If no config or no goodbye message, use default
            goodbye_message = "Goodbye, {user}!"
            if group_config and group_config.goodbye_message:
                goodbye_message = group_config.goodbye_message

            # Format the message
            user = chat_member.old_chat_member.user
            formatted_message = goodbye_message.format(
                user=user.mention,
                first_name=user.first_name,
                last_name=user.last_name or "",
                username=f"@{user.username}" if user.username else "",
                group=chat_member.chat.title
            )

            # Send the goodbye message
            await client.send_message(chat_member.chat.id, formatted_message)

            # Log the action
            action = "left the group"
            if chat_member.new_chat_member and chat_member.new_chat_member.status == ChatMemberStatus.BANNED:
                action = "was banned from the group"

            await log_action(
                client,
                db,
                chat_member.chat.id,
                user.id,
                0,  # No admin for this action
                action
            )
    except Exception as e:
        print(f"Error in handle_user_leave: {e}")

@Client.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "setwelcome"):
        return await message.reply("Please wait before using this command again.")

    # Get welcome message
    if len(message.command) < 2:
        return await message.reply(
            "Please provide a welcome message. You can use the following placeholders:\n"
            "{user} - User mention\n"
            "{first_name} - User's first name\n"
            "{last_name} - User's last name\n"
            "{username} - User's username\n"
            "{group} - Group name"
        )

    welcome_message = " ".join(message.command[1:])

    try:
        # Update group config
        async for db in get_db():
            # Get or create group config
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            if group_config:
                group_config.welcome_message = welcome_message
            else:
                group_config = GroupConfig(
                    group_id=message.chat.id,
                    welcome_message=welcome_message
                )
                db.add(group_config)

            await db.commit()

            # Log the action
            await log_action(
                client,
                db,
                message.chat.id,
                message.from_user.id,
                message.from_user.id,
                "set welcome message"
            )

            await message.reply("Welcome message set successfully.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@Client.on_message(filters.command("setgoodbye") & filters.group)
async def set_goodbye(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "setgoodbye"):
        return await message.reply("Please wait before using this command again.")

    # Get goodbye message
    if len(message.command) < 2:
        return await message.reply(
            "Please provide a goodbye message. You can use the following placeholders:\n"
            "{user} - User mention\n"
            "{first_name} - User's first name\n"
            "{last_name} - User's last name\n"
            "{username} - User's username\n"
            "{group} - Group name"
        )

    goodbye_message = " ".join(message.command[1:])

    try:
        # Update group config
        async for db in get_db():
            # Get or create group config
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            if group_config:
                group_config.goodbye_message = goodbye_message
            else:
                group_config = GroupConfig(
                    group_id=message.chat.id,
                    goodbye_message=goodbye_message
                )
                db.add(group_config)

            await db.commit()

            # Log the action
            await log_action(
                client,
                db,
                message.chat.id,
                message.from_user.id,
                message.from_user.id,
                "set goodbye message"
            )

            await message.reply("Goodbye message set successfully.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@Client.on_message(filters.command("setwarnlimit") & filters.group)
async def set_warn_limit(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "setwarnlimit"):
        return await message.reply("Please wait before using this command again.")

    # Get warn limit
    if len(message.command) < 2:
        return await message.reply("Please provide a warn limit (number of warnings before ban).")

    try:
        warn_limit = int(message.command[1])
        if warn_limit < 1:
            return await message.reply("Warn limit must be at least 1.")
    except ValueError:
        return await message.reply("Warn limit must be a number.")

    try:
        # Update group config
        async for db in get_db():
            # Get or create group config
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            if group_config:
                group_config.warn_limit = warn_limit
            else:
                group_config = GroupConfig(
                    group_id=message.chat.id,
                    warn_limit=warn_limit
                )
                db.add(group_config)

            await db.commit()

            # Log the action
            await log_action(
                client,
                db,
                message.chat.id,
                message.from_user.id,
                message.from_user.id,
                f"set warn limit to {warn_limit}"
            )

            await message.reply(f"Warn limit set to {warn_limit}.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@Client.on_message(filters.command("rules") & filters.group)
async def rules(client: Client, message: Message):
    # Check cooldown
    if not await check_cooldown(message.from_user.id, "rules"):
        return await message.reply("Please wait before using this command again.")

    try:
        # Get group config
        async for db in get_db():
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            if not group_config or not group_config.rules:
                return await message.reply("No rules have been set for this group.")

            await message.reply(f"**Group Rules:**\n\n{group_config.rules}")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@Client.on_message(filters.command("setrules") & filters.group)
async def set_rules(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "setrules"):
        return await message.reply("Please wait before using this command again.")

    # Get rules
    if len(message.command) < 2:
        return await message.reply("Please provide the rules for the group.")

    rules_text = " ".join(message.command[1:])

    try:
        # Update group config
        async for db in get_db():
            # Get or create group config
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            if group_config:
                group_config.rules = rules_text
            else:
                group_config = GroupConfig(
                    group_id=message.chat.id,
                    rules=rules_text
                )
                db.add(group_config)

            await db.commit()

            # Log the action
            await log_action(
                client,
                db,
                message.chat.id,
                message.from_user.id,
                message.from_user.id,
                "set group rules"
            )

            await message.reply("Group rules set successfully.")
            return None
        return None
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
        return None
