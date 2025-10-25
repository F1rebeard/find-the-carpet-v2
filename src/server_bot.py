import asyncio
import contextlib

from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs
from loguru import logger

from src.bot.dialogs.admin.add_user import add_user_dialog
from src.bot.dialogs.admin.ban_user import ban_user_dialog
from src.bot.dialogs.admin.pending_users import pending_users_dialog
from src.bot.dialogs.carpet_search import carpet_search_dialog
from src.bot.dialogs.registration import registration_dialog, registration_router
from src.bot.handlers.admin_menu import admin_menu_router
from src.bot.handlers.start_command import start_command_router
from src.core_settings import base_settings, bot, dp
from src.database import db
from src.logger import setup_logger


async def clear_commands_for_user(user_id: int):
    """Clear commands for a specific user."""
    try:
        await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=user_id))
        logger.info(f"🧹 Cleared commands for user: {user_id}")
    except Exception as e:
        logger.debug(f"⚠️ Could not clear commands for user {user_id}: {e}")


async def set_commands():
    """Set bot commands depending on user type: an admin or a regular user."""
    # Clear all existing commands first to ensure clean state
    try:
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
        logger.info("🧹 Cleared default commands")
    except Exception as e:
        logger.debug(f"⚠️ Could not clear default commands: {e}")

    # Default commands for all users
    default_commands = [
        BotCommand(command="start", description="🚀 Главное меню"),
    ]
    await bot.set_my_commands(
        commands=default_commands,
        scope=BotCommandScopeDefault(),
    )
    logger.info("✅ Set default commands for all users")

    # Admin-specific commands (includes both start and admin)
    if len(base_settings.ADMIN_IDS) > 0:
        admin_commands = [
            BotCommand(command="start", description="🚀 Главное меню"),
            BotCommand(command="admin", description="👑 Панель администратора"),
        ]
        for admin_id in base_settings.ADMIN_IDS:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
            logger.info(f"✅ Set admin commands for admin: {admin_id}")
    else:
        logger.info("ℹ️ No admins configured, skipping admin command setup")


def register_routers():
    dp.include_router(start_command_router)
    dp.include_router(admin_menu_router)
    dp.include_router(registration_router)
    logger.info("🔗 Routers registered")


def register_dialogs():
    setup_dialogs(dp)
    dp.include_router(registration_dialog)
    dp.include_router(pending_users_dialog)
    dp.include_router(ban_user_dialog)
    dp.include_router(add_user_dialog)
    dp.include_router(carpet_search_dialog)
    logger.info("🔗 Dialogs registered")


@contextlib.asynccontextmanager
async def app_lifecycle():
    """Application lifecycle manager."""
    logger.info("🚀 Starting telegram-bot...")
    setup_logger()
    register_routers()
    register_dialogs()
    await set_commands()
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
        await dp.start_polling(telegram_bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Graceful shutdown requested by user (KeyboardInterrupt)")
