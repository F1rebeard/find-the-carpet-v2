from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from loguru import logger

from src.bot.handlers.utils import is_admin_callback, is_admin_message
from src.services.admin import states
from src.services.admin.messages import messages as admin_messages

admin_menu_router = Router()


@admin_menu_router.message(Command("admin"), is_admin_message)
async def show_admin_menu(message: Message, dialog_manager: DialogManager):
    """Show admin menu with inline keyboard."""
    try:
        await dialog_manager.reset_stack()
        logger.debug(f"🔄 Admin {message.from_user.id} reset to admin menu")
        await message.answer(
            text=admin_messages.admin_welcome,
            reply_markup=admin_messages.get_admin_menu_keyboard(),
        )
        logger.debug(f"👑 Admin menu shown to {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Error showing admin menu: {e}")
        await message.answer("❌ Ошибка отображения админ-меню")


@admin_menu_router.callback_query(F.data == "admin_main_menu", is_admin_callback)
async def back_to_admin_menu(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Show admin menu with inline keyboard."""
    try:
        await dialog_manager.reset_stack()
        logger.debug(f"🔄 Admin {callback.from_user.id} reset to admin menu")
        await callback.message.answer(
            text=admin_messages.admin_welcome,
            reply_markup=admin_messages.get_admin_menu_keyboard(),
        )
        await callback.answer()
        logger.debug(f"👑 Admin menu shown to {callback.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Error showing admin menu: {e}")
        await callback.message.answer("❌ Ошибка отображения админ-меню")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_pending_users", is_admin_callback)
async def start_pending_users_dialog(callback: CallbackQuery, dialog_manager: DialogManager):
    """Start pending users managment dialog."""
    try:
        await dialog_manager.start(
            state=states.PendingUsersStatesGroup.users_list,
            mode=StartMode.RESET_STACK,
        )
        await callback.answer()
        logger.debug(f"📋 Admin {callback.from_user.id} started pending users dialog")
    except Exception as e:
        logger.error(f"❌ Error starting pending users dialog: {e}")
        await callback.message.answer("❌ Ошибка запуска диалога заявок")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_add_user", is_admin_callback)
async def start_add_user_dialog(callback: CallbackQuery, dialog_manager: DialogManager):
    """Start  manual add user dialog."""
    try:
        await dialog_manager.start(
            state=states.AddUserStatesGroup.telegram_id,
            mode=StartMode.RESET_STACK,
        )
        await callback.answer()
        logger.debug(f"➕ Admin {callback.from_user.id} started add user dialog")
    except Exception as e:
        logger.error(f"❌ Error starting add user dialog: {e}")
        await callback.message.answer("❌ Ошибка запуска диалога добавления пользователя")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_ban_user", is_admin_callback)
async def start_ban_user_dialog(callback: CallbackQuery, dialog_manager: DialogManager):
    """Start ban user dialog."""
    try:
        await dialog_manager.start(
            state=states.BanUserStatesGroup.telegram_id, mode=StartMode.RESET_STACK
        )
        await callback.answer()
        logger.info(f"🚫 Admin {callback.from_user.id} started ban user dialog")
    except Exception as e:
        logger.error(f"❌ Error starting ban user dialog: {e}")
        await callback.message.answer("❌ Ошибка запуска диалога блокировки пользователя")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_broadcast", is_admin_callback)
async def start_broadcast_dialog(callback: CallbackQuery, dialog_manager: DialogManager):
    """Start broadcast dialog."""
    try:
        await dialog_manager.start(
            state=states.BroadcastStatesGroup.message, mode=StartMode.RESET_STACK
        )
        await callback.answer()
        logger.info(f"📢 Admin {callback.from_user.id} started broadcast dialog")
    except Exception as e:
        logger.error(f"❌ Error starting broadcast dialog: {e}")
        await callback.message.answer("❌ Ошибка запуска диалога рассылки")
        await callback.answer()
