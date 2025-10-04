from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from loguru import logger

from src.bot.handlers.utils import is_admin_callback
from src.database import db
from src.services.admin.messages import messages as admin_messages
from src.services.carpet_search.states import CarpetSearchStatesGroup
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
            await message.answer(
                text=response.message,
                reply_markup=messages.get_admin_start_menu_keyboard(),
            )
        case StartCommandAction.SHOW_MAIN_MENU:
            await message.answer(
                text=response.message,
                reply_markup=messages.get_main_menu_keyboard(),
            )
        case StartCommandAction.SHOW_PENDING_STATUS:
            await message.answer(messages.get_full_message(response.message, messages.pending_info))
        case StartCommandAction.SHOW_BANNED_MESSAGE:
            await message.answer(
                messages.get_full_message(response.message, messages.support_contact)
            )
        case StartCommandAction.ERROR:
            await message.answer(response.message)


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


@start_command_router.callback_query(F.data == "admin_panel", is_admin_callback)
async def handle_admin_panel_redirect(callback: CallbackQuery):
    """Redirect admin to the full admin panel."""
    try:
        await callback.message.edit_text(
            text=admin_messages.admin_welcome,
            reply_markup=admin_messages.get_admin_menu_keyboard(),
        )
        await callback.answer()
        logger.info(f"👑 Admin {callback.from_user.id} redirected to admin panel")
    except Exception as e:
        logger.error(f"❌ Error redirecting to admin panel: {e}")
        await callback.answer("❌ Ошибка перехода в админ-панель")


@start_command_router.callback_query(F.data == "find_carpets")
async def handle_find_carpets(callback: CallbackQuery, dialog_manager: DialogManager):
    """Handle find carpets button click - launch carpet search dialog."""
    try:
        await dialog_manager.start(
            state=CarpetSearchStatesGroup.main_menu, mode=StartMode.RESET_STACK
        )
        await callback.answer()
        logger.info(f"🔍 User {callback.from_user.id} started carpet search")
    except Exception as e:
        logger.error(f"❌ Error launching carpet search for {callback.from_user.id}: {e}")
        await callback.answer("❌ Ошибка запуска поиска ковров")


@start_command_router.callback_query(F.data == "favorites")
async def handle_favorites(callback: CallbackQuery):
    """Handle favorites button click."""
    try:
        await callback.answer("❤️ Функция избранного будет реализована позже")
        logger.info(f"❤️ User {callback.from_user.id} clicked favorites")
    except Exception as e:
        logger.error(f"❌ Error handling favorites: {e}")
        await callback.answer("❌ Ошибка")


@start_command_router.callback_query(F.data == "create_pdf")
async def handle_create_pdf(callback: CallbackQuery):
    """Handle create PDF button click."""
    try:
        await callback.answer("📄 Функция создания PDF будет реализована позже")
        logger.info(f"📄 User {callback.from_user.id} clicked create PDF")
    except Exception as e:
        logger.error(f"❌ Error handling create PDF: {e}")
        await callback.answer("❌ Ошибка")
