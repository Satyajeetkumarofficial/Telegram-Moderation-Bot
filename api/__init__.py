from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API token from environment variables
API_TOKEN = os.getenv("API_TOKEN")

# Create API key header
api_key_header = APIKeyHeader(name="X-API-Key")

# Create FastAPI app
app = FastAPI(
    title="Telegram Moderation Bot API",
    description="API for the Telegram Moderation Bot",
    version="1.0.0"
)

# API key dependency
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return api_key