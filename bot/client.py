import os
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

bot = Client(
    "manager_bot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    plugins=dict(root="bot.handlers")
)

async def start_bot():
    await bot.start()
