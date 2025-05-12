import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os
import time

from database.connection import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize the database and create tables"""
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        return

    logger.info(f"Connecting to database: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)

    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            break
        except Exception as e:
            logger.error(f"Attempt {attempt}: Error creating database tables: {e}")
            if attempt == max_retries:
                logger.error("Max retries reached. Exiting.")
                raise
            time.sleep(3)  # wait before retrying
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
