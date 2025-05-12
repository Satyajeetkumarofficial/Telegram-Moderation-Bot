import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

from database.connection import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize the database and create tables"""
    # Load environment variables
    load_dotenv()

    # Get database URL from environment variables
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        return

    logger.info(f"Connecting to database: {DATABASE_URL}")

    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=True)

    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
    finally:
        # Close engine
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())