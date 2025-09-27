import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from loguru import logger

from src.bot.handlers.utils import is_admin_callback, is_admin_message
from src.core_settings import base_settings
from src.database import db
from src.services.admin import states
from src.services.admin.messages import messages as admin_messages
from src.services.google_sheets.carpets_service import GoogleSheetsCarpetService
from src.services.google_sheets.sales_service import GoogleSheetsSalesService

admin_menu_router = Router()


async def spinning_sync_animation(message):
    """Show spinning animation with cycling status messages."""
    statuses = [
        "🔄 Синхронизация",
        "🔄 Синхронизация.",
        "🔄 Синхронизация..",
        "🔄 Синхронизация...",
    ]

    index = 0
    try:
        while True:
            await message.edit_text(text=statuses[index % len(statuses)])
            await asyncio.sleep(0.5)
            index += 1
    except asyncio.CancelledError:
        pass


async def perform_sync_with_animation(
    callback, service_class, sync_method, spreadsheet_id, worksheet_title, table_name
):
    """Perform Google Sheets sync with animation for any table."""
    try:
        await callback.answer()
        await callback.message.edit_text(
            text="🔄 Инициализация синхронизации...",
            reply_markup=None,
        )

        async def perform_actual_sync():
            async with db.get_session() as session:
                service = service_class(session=session)
                sync_func = getattr(service, sync_method)
                result = await sync_func(
                    spreadsheet_id=spreadsheet_id,
                    worksheet_title=worksheet_title,
                )
                return result

        animation_task = asyncio.create_task(spinning_sync_animation(callback.message))
        sync_task = asyncio.create_task(perform_actual_sync())
        done, pending = await asyncio.wait([sync_task], return_when=asyncio.FIRST_COMPLETED)
        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass

        result = await done.pop()
        if result.invalid_report:
            message_text = admin_messages.sync_completed_with_errors.format(
                total_rows=result.total_rows,
                inserted=result.inserted,
                updated=result.updated,
                skipped=result.skipped,
                bad_data=result.bad_data,
                invalid_report=result.invalid_report,
            )
        else:
            message_text = admin_messages.sync_completed.format(
                total_rows=result.total_rows,
                inserted=result.inserted,
                updated=result.updated,
                bad_data=result.bad_data,
                skipped=result.skipped,
            )
        await callback.message.edit_text(
            text=message_text,
            reply_markup=admin_messages.get_admin_menu_keyboard(),
        )
        logger.info(
            f"✅ {table_name} sync completed by admin {callback.from_user.id}: "
            f"total={result.total_rows}, inserted={result.inserted}, "
            f"updated={result.updated}, skipped={result.skipped}, bad_data={result.bad_data}"
        )

    except Exception as e:
        logger.error(f"❌ Error during {table_name} sync: {e}")
        error_message = admin_messages.sync_error.format(error=str(e))
        await callback.message.edit_text(
            text=error_message,
            reply_markup=admin_messages.get_admin_menu_keyboard(),
        )


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
    """Show admin menu with inline keyboard from aiogram-dialog context."""
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


@admin_menu_router.callback_query(F.data == "admin_back_to_menu", is_admin_callback)
async def back_to_admin_menu_regular(callback: CallbackQuery):
    """Show admin menu with inline keyboard from regular callback context."""
    try:
        await callback.message.edit_text(
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
            state=states.BanUserStatesGroup.user_search, mode=StartMode.RESET_STACK
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


@admin_menu_router.callback_query(F.data == "admin_sync_google_sheets", is_admin_callback)
async def start_google_sheets_sync(callback: CallbackQuery, dialog_manager: DialogManager):
    """Show table selection for Google Sheets sync."""
    try:
        await callback.message.edit_text(
            text=admin_messages.sync_choose_table_prompt,
            reply_markup=admin_messages.get_table_selection_keyboard(),
        )
        await callback.answer()
        logger.info(f"🔄 Admin {callback.from_user.id} started Google Sheets table selection")
    except Exception as e:
        logger.error(f"❌ Error starting Google Sheets sync: {e}")
        await callback.message.answer("❌ Ошибка запуска синхронизации")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_sync_table_carpets", is_admin_callback)
async def start_carpets_sync_confirmation(callback: CallbackQuery, dialog_manager: DialogManager):
    """Show carpets sync confirmation."""
    try:
        await callback.message.edit_text(
            text=admin_messages.sync_carpets_prompt,
            reply_markup=admin_messages.get_confirmation_keyboard("sync_carpets"),
        )
        await callback.answer()
        logger.info(f"🧿 Admin {callback.from_user.id} started carpets sync confirmation")
    except Exception as e:
        logger.error(f"❌ Error starting carpets sync: {e}")
        await callback.message.answer("❌ Ошибка запуска синхронизации ковров")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_sync_table_sales", is_admin_callback)
async def start_sales_sync_confirmation(callback: CallbackQuery, dialog_manager: DialogManager):
    """Show sales sync confirmation."""
    try:
        await callback.message.edit_text(
            text=admin_messages.sync_sales_prompt,
            reply_markup=admin_messages.get_confirmation_keyboard("sync_sales"),
        )
        await callback.answer()
        logger.info(f"💰 Admin {callback.from_user.id} started sales sync confirmation")
    except Exception as e:
        logger.error(f"❌ Error starting sales sync: {e}")
        await callback.message.answer("❌ Ошибка запуска синхронизации продаж")
        await callback.answer()


@admin_menu_router.callback_query(F.data == "admin_confirm_sync_carpets", is_admin_callback)
async def confirm_carpets_sync(callback: CallbackQuery, dialog_manager: DialogManager):
    """Execute carpets sync with spinning animation."""
    await perform_sync_with_animation(
        callback=callback,
        service_class=GoogleSheetsCarpetService,
        sync_method="sync_carpets",
        spreadsheet_id=base_settings.GOOGLE_SPREADSHEET_ID,
        worksheet_title=base_settings.GOOGLE_CARPETS_SHEET_TITLE,
        table_name="Carpets",
    )


@admin_menu_router.callback_query(F.data == "admin_confirm_sync_sales", is_admin_callback)
async def confirm_sales_sync(callback: CallbackQuery, dialog_manager: DialogManager):
    """Execute sales sync with spinning animation."""
    await perform_sync_with_animation(
        callback=callback,
        service_class=GoogleSheetsSalesService,
        sync_method="sync_sales",
        spreadsheet_id=base_settings.GOOGLE_SPREADSHEET_ID,
        worksheet_title=base_settings.GOOGLE_SALES_SHEET_TITLE,
        table_name="Sales",
    )


@admin_menu_router.callback_query(F.data == "admin_cancel", is_admin_callback)
async def cancel_admin_operation(callback: CallbackQuery, dialog_manager: DialogManager):
    """Cancel admin operation and return to main menu."""
    try:
        await callback.message.edit_text(
            text=admin_messages.admin_welcome,
            reply_markup=admin_messages.get_admin_menu_keyboard(),
        )
        await callback.answer()
        logger.debug(f"❌ Admin {callback.from_user.id} cancelled operation")
    except Exception as e:
        logger.error(f"❌ Error cancelling operation: {e}")
        await callback.message.answer("❌ Ошибка отмены операции")
        await callback.answer()
