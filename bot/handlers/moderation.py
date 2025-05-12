import asyncio
import time
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, FloodWait
from pyrogram.types import Message, ChatPermissions
from sqlalchemy.future import select

from bot.utils import is_owner, get_target_user, bot_is_admin, log_action, check_cooldown, is_admin
from database.connection import get_db
from database.models import Warning, GroupConfig


@Client.on_message(filters.command("kick") & filters.group)
async def kick(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "kick"):
        return await message.reply("Please wait before using this command again.")

    # Check if bot is admin
    if not await bot_is_admin(client, message.chat.id):
        return await message.reply("I need admin rights.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    try:
        # Check if target user is an admin
        target_member = await client.get_chat_member(message.chat.id, user_id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("Cannot kick an admin.")

        # Kick the user
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)

        # Log the action
        async for db in get_db():
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                "kick"
            )

        await message.reply(f"User kicked.")
    except UserAdminInvalid:
        await message.reply("Cannot kick this user; they may be an admin.")
    except ChatAdminRequired:
        await message.reply("I need admin rights to perform this action.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None


@Client.on_message(filters.command("ban") & filters.group)
async def ban(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "ban"):
        return await message.reply("Please wait before using this command again.")

    # Check if bot is admin
    if not await bot_is_admin(client, message.chat.id):
        return await message.reply("I need admin rights.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    try:
        # Check if target user is an admin
        target_member = await client.get_chat_member(message.chat.id, user_id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("Cannot ban an admin.")

        # Ban the user
        await client.ban_chat_member(message.chat.id, user_id)

        # Delete user's messages
        if message.reply_to_message:
            try:
                await message.reply_to_message.delete()
            except Exception:
                pass

        # Log the action
        async for db in get_db():
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                "ban"
            )

        await message.reply(f"User banned.")
        return None
    except UserAdminInvalid:
        await message.reply("Cannot ban this user; they may be an admin.")
        return None
    except ChatAdminRequired:
        await message.reply("I need admin rights to perform this action.")
        return None
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
        return None
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
        return None


@Client.on_message(filters.command("mute") & filters.group)
async def mute(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "mute"):
        return await message.reply("Please wait before using this command again.")

    # Check if bot is admin
    if not await bot_is_admin(client, message.chat.id):
        return await message.reply("I need admin rights.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    # Parse duration
    duration = 3600  # Default duration: 1 hour
    if len(message.command) > 2:
        try:
            duration = int(message.command[2])
        except ValueError:
            return await message.reply("Invalid duration. Please provide a number in seconds.")

    try:
        # Check if target user is an admin
        target_member = await client.get_chat_member(message.chat.id, user_id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("Cannot mute an admin.")

        # Calculate until_date as a datetime object
        until_date = datetime.fromtimestamp(time.time() + duration)

        # Mute the user
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(),
            until_date=until_date
        )

        # Log the action
        async for db in get_db():
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                f"mute for {duration} seconds"
            )

        await message.reply(f"User muted for {duration} seconds.")
    except UserAdminInvalid:
        await message.reply("Cannot mute this user; they may be an admin.")
    except ChatAdminRequired:
        await message.reply("I need admin rights to perform this action.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None

@Client.on_message(filters.command("unmute") & filters.group)
async def unmute(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "unmute"):
        return await message.reply("Please wait before using this command again.")

    # Check if bot is admin
    if not await bot_is_admin(client, message.chat.id):
        return await message.reply("I need admin rights.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    try:
        # Unmute the user by giving back all permissions
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_invite_users=True
            )
        )

        # Log the action
        async for db in get_db():
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                "unmute"
            )

        await message.reply("User unmuted.")
    except UserAdminInvalid:
        await message.reply("Cannot unmute this user; they may be an admin.")
    except ChatAdminRequired:
        await message.reply("I need admin rights to perform this action.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None

@Client.on_message(filters.command("unban") & filters.group)
async def unban(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "unban"):
        return await message.reply("Please wait before using this command again.")

    # Check if bot is admin
    if not await bot_is_admin(client, message.chat.id):
        return await message.reply("I need admin rights.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    try:
        # Unban the user
        await client.unban_chat_member(message.chat.id, user_id)

        # Log the action
        async for db in get_db():
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                "unban"
            )

        await message.reply("User unbanned.")
    except UserAdminInvalid:
        await message.reply("Cannot unban this user; they may be an admin.")
    except ChatAdminRequired:
        await message.reply("I need admin rights to perform this action.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None

@Client.on_message(filters.command("warn") & filters.group)
async def warn(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "warn"):
        return await message.reply("Please wait before using this command again.")

    # Check if bot is admin
    if not await bot_is_admin(client, message.chat.id):
        return await message.reply("I need admin rights.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    # Get reason (if provided)
    reason = None
    if len(message.command) > 2:
        reason = " ".join(message.command[2:])

    try:
        # Check if target user is an admin
        target_member = await client.get_chat_member(message.chat.id, user_id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("Cannot warn an admin.")

        # Add warning to database
        async for db in get_db():
            # Get group config for warn limit
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            # Default warn limit is 3 if no config exists
            warn_limit = 3
            if group_config:
                warn_limit = group_config.warn_limit

            # Add warning
            warning = Warning(
                group_id=message.chat.id,
                user_id=user_id,
                admin_id=message.from_user.id,
                reason=reason
            )
            db.add(warning)
            await db.commit()

            # Count warnings
            warnings = await db.execute(
                select(Warning).where(
                    Warning.group_id == message.chat.id,
                    Warning.user_id == user_id
                )
            )
            warnings = warnings.scalars().all()
            warning_count = len(warnings)

            # Log the action
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                f"warn ({warning_count}/{warn_limit})" + (f": {reason}" if reason else "")
            )

            # Check if user should be banned
            if warning_count >= warn_limit:
                # Ban the user
                await client.ban_chat_member(message.chat.id, user_id)

                # Log the ban
                await log_action(
                    client, 
                    db, 
                    message.chat.id, 
                    user_id, 
                    message.from_user.id, 
                    f"auto-ban after {warning_count} warnings"
                )

                return await message.reply(f"User has reached {warning_count}/{warn_limit} warnings and has been banned.")

            # Reply with warning count
            return await message.reply(f"User warned ({warning_count}/{warn_limit})." + (f" Reason: {reason}" if reason else ""))
    except UserAdminInvalid:
        await message.reply("Cannot warn this user; they may be an admin.")
    except ChatAdminRequired:
        await message.reply("I need admin rights to perform this action.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None

@Client.on_message(filters.command("unwarn") & filters.group)
async def unwarn(client: Client, message: Message):
    # Check if user is admin or owner
    if not await is_admin(client, message.chat.id, message.from_user.id) and not await is_owner(message):
        return await message.reply("You need to be an admin to use this command.")

    # Check cooldown
    if not await check_cooldown(message.from_user.id, "unwarn"):
        return await message.reply("Please wait before using this command again.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    try:
        # Remove the most recent warning
        async for db in get_db():
            # Get the most recent warning
            warning = await db.execute(
                select(Warning).where(
                    Warning.group_id == message.chat.id,
                    Warning.user_id == user_id
                ).order_by(Warning.created_at.desc())
            )
            warning = warning.scalar_one_or_none()

            if not warning:
                return await message.reply("This user has no warnings to remove.")

            # Delete the warning
            await db.delete(warning)
            await db.commit()

            # Count remaining warnings
            warnings = await db.execute(
                select(Warning).where(
                    Warning.group_id == message.chat.id,
                    Warning.user_id == user_id
                )
            )
            warnings = warnings.scalars().all()
            warning_count = len(warnings)

            # Log the action
            await log_action(
                client, 
                db, 
                message.chat.id, 
                user_id, 
                message.from_user.id, 
                f"unwarn (remaining: {warning_count})"
            )

            # Reply with warning count
            return await message.reply(f"Warning removed. User now has {warning_count} warnings.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None

@Client.on_message(filters.command("warnings") & filters.group)
async def warnings(client: Client, message: Message):
    # Check cooldown
    if not await check_cooldown(message.from_user.id, "warnings"):
        return await message.reply("Please wait before using this command again.")

    # Get target user
    user_id = await get_target_user(client, message)
    if not user_id:
        return await message.reply("Please reply to a message or provide a username.")

    try:
        # Get user's warnings
        async for db in get_db():
            # Get group config for warn limit
            group_config = await db.execute(
                select(GroupConfig).where(GroupConfig.group_id == message.chat.id)
            )
            group_config = group_config.scalar_one_or_none()

            # Default warn limit is 3 if no config exists
            warn_limit = 3
            if group_config:
                warn_limit = group_config.warn_limit

            # Get warnings
            warnings = await db.execute(
                select(Warning).where(
                    Warning.group_id == message.chat.id,
                    Warning.user_id == user_id
                ).order_by(Warning.created_at.desc())
            )
            warnings = warnings.scalars().all()
            warning_count = len(warnings)

            if warning_count == 0:
                return await message.reply("This user has no warnings.")

            # Format warnings
            user = await client.get_users(user_id)
            warning_list = f"**Warnings for {user.first_name}** ({warning_count}/{warn_limit}):\n\n"

            for i, warning in enumerate(warnings, 1):
                admin = await client.get_users(warning.admin_id)
                warning_time = warning.created_at.strftime("%Y-%m-%d %H:%M:%S")
                reason = f": {warning.reason}" if warning.reason else ""
                warning_list += f"{i}. By {admin.first_name} on {warning_time}{reason}\n"

            return await message.reply(warning_list)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply(f"Rate limited. Please try again in {e.value} seconds.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")
    return None
