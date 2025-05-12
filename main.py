import os
from fastapi import FastAPI
from dotenv import load_dotenv
from bot.client import start_bot
from api.routes import router as api_router

load_dotenv()
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await start_bot()

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Telegram Manager Bot API is running"}
