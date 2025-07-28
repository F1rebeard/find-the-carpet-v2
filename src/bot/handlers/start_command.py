from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from src.database import db
from src.services.start_command import (
    StartCommandAction,
    StartCommandResponse,
    StartCommandService,
    messages,
)

start_command_router = Router()


async def _send_response_by_action(message: Message, response: StartCommandResponse):
    """Send response based on action type."""

    match response.action:
        case StartCommandAction.SHOW_REGISTRATION:
            await message.answer(
                text=messages.get_full_message(response.message, messages.new_user_instructions),
                reply_markup=messages.get_registration_keyboard(),
            )

        case StartCommandAction.SHOW_ADMIN_PANEL:
            await message.answer(messages.get_full_message(response.message, messages.admin_menu))

        case StartCommandAction.SHOW_MAIN_MENU:
            await message.answer(messages.get_full_message(response.message, messages.main_menu))

        case StartCommandAction.SHOW_PENDING_STATUS:
            await message.answer(messages.get_full_message(response.message, messages.pending_info))

        case StartCommandAction.SHOW_BANNED_MESSAGE:
            await message.answer(
                messages.get_full_message(response.message, messages.support_contact)
            )

        case StartCommandAction.ERROR:
            await message.answer(response.message)

        case _:
            logger.warning(f"🤔 Unknown action type: {response.action}")
            await message.answer(messages.unknown_error)


@start_command_router.message(CommandStart())
async def handle_start_command(message: Message):
    """Handle /start command with a user type determination and appropriate response."""

    telegram_id = message.from_user.id
    logger.info(f"🚀 Start command received from user: {telegram_id}")

    try:
        async with db.get_session() as session:
            start_service = StartCommandService(session)
            response = await start_service.process_start_command(telegram_id)
            await _send_response_by_action(message, response)

    except Exception as e:
        logger.error(f"❌ Error processing start command for {telegram_id}: {e}")
        await message.answer(messages.processing_error)
