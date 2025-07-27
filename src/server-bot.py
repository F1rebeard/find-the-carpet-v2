import asyncio
import contextlib

from loguru import logger

from src.database import db
from src.logger import setup_logger
from src.settings import bot, dp


def register_routers():
    """Register all bot routers."""

    from src.bot.handlers.start_command import start_command_router

    dp.include_router(start_command_router)
    logger.info("🔗 Routers registered")


@contextlib.asynccontextmanager
async def app_lifecycle():
    setup_logger()
    logger.info("🚀 Starting...")
    register_routers()

    await db.connect()
    try:
        yield {"telegram_bot": bot}
    finally:
        await db.disconnect()
        await bot.session.close()
        logger.info("🛑 Shutting down...")


async def main():
    async with app_lifecycle() as lifecycle:
        telegram_bot = lifecycle["telegram_bot"]
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(telegram_bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Graceful shutdown requested by user (KeyboardInterrupt)")
