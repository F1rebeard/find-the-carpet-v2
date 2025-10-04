#!/usr/bin/env python3
"""
One-time script to clear cached admin commands for a specific user.
Run this to fix the command menu display issue.
"""

import asyncio

from aiogram.types import BotCommandScopeChat

from src.core_settings import bot


async def clear_user_commands(user_id: int):
    """Clear commands for a specific user ID."""
    try:
        await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=user_id))
        print(f"✅ Cleared commands for user {user_id}")
    except Exception as e:
        print(f"❌ Error clearing commands for user {user_id}: {e}")


async def main():
    """Main function to clear commands for the specified user."""
    # Your Telegram ID - replace with your actual ID if different
    your_telegram_id = 368362025

    print(f"🧹 Clearing cached admin commands for user: {your_telegram_id}")
    await clear_user_commands(your_telegram_id)

    print("✅ Done! Now restart your bot and the command menu should show only /start")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
