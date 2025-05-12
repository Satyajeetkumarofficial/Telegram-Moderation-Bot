import os
import logging
from pyrogram import Client, idle
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Telegram API credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# Log configuration (without sensitive data)
logger.info("Bot configuration loaded")
logger.info(f"OWNER_ID: {OWNER_ID}")
logger.info(f"API_ID: {'Set' if API_ID else 'Not set'}")
logger.info(f"API_HASH: {'Set' if API_HASH else 'Not set'}")
logger.info(f"BOT_TOKEN: {'Set' if BOT_TOKEN else 'Not set'}")

# Validate configuration
if not API_ID or not API_HASH or not BOT_TOKEN:
    logger.error("Missing required Telegram API credentials. Please check your .env file.")
    raise ValueError("Missing required Telegram API credentials")

if OWNER_ID == 0:
    logger.warning("OWNER_ID is not set or is set to 0. Bot will not respond to owner commands.")

# Create Pyrogram client
logger.info("Initializing Pyrogram client")
bot = Client(
    "telegram_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="bot.plugins")
)

# Override start and stop to include logging
async def start_bot():
    await bot.start()
    logger.info("Bot connected to Telegram servers")
    await idle()

async def stop_bot():
    await bot.stop()
    logger.warning("Bot disconnected from Telegram servers")

__all__ = ["bot", "OWNER_ID", "start_bot", "stop_bot"]