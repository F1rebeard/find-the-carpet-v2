from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Row, Select
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from src.bot.handlers.admin_menu import back_to_admin_menu
from src.bot.handlers.utils import reject_non_text
from src.core_settings import bot
from src.database import db
from src.services.admin.states import BanUserStatesGroup
from src.services.admin.users_managment import AdminUserManagementService


async def on_ban_reason_input(message: Message, _, dialog_manager: DialogManager):
    """Handle ban reason input."""
    reason = message.text.strip() if message.text else None
    dialog_manager.dialog_data["reason"] = reason
    await dialog_manager.next()


async def skip_ban_reason(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Skip ban reason."""
    dialog_manager.dialog_data["reason"] = None
    await dialog_manager.next()


async def confirm_ban_user(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Confirm and ban user."""
    try:
        data = dialog_manager.dialog_data
        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            success, message = await service.ban_user(
                telegram_id=data["telegram_id"], reason=data.get("reason")
            )
            if success:
                await callback.message.answer(f"🚫 {message}")
                logger.info(f"🚫 Admin {callback.from_user.id} banned user {data['telegram_id']}")
            else:
                await callback.message.answer(f"❌ {message}")
        await dialog_manager.done()
        await back_to_admin_menu(callback, button, dialog_manager)

    except Exception as e:
        logger.error(f"❌ Error banning user: {e}")
        await callback.message.answer("❌ Ошибка блокировки пользователя")
        await dialog_manager.done()


async def on_user_selected_for_ban(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str
):
    """Handle user selection for banning."""
    telegram_id = int(item_id.split("_")[1])
    dialog_manager.dialog_data["telegram_id"] = telegram_id
    try:
        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            chosen_user = await service.user_dao.get_registered_user_by_id(telegram_id)
        if chosen_user:
            user_data = [
                chosen_user.first_name,
                chosen_user.last_name if chosen_user.last_name else "",
                chosen_user.username if chosen_user.username else "",
            ]
            user_data_to_show = " ".join(user_data)
            dialog_manager.dialog_data["user_data"] = user_data_to_show
    except Exception as e:
        logger.warning(f"Selected user with id {telegram_id} not found: {e}")
        dialog_manager.dialog_data["user_display"] = None

    await dialog_manager.switch_to(BanUserStatesGroup.reason)


async def ban_user_data_getter(dialog_manager: DialogManager, **kwargs):
    """Get ban user dialog data."""
    data = dialog_manager.dialog_data.copy()
    data["reason"] = data.get("reason") or "не указана"
    return {"dialog_data": data}


async def get_registered_users_data(dialog_manager: DialogManager, **kwargs) -> dict:
    """Get registered users with pagination."""
    try:
        search_query = dialog_manager.dialog_data.get("search_query", "")
        current_page = dialog_manager.dialog_data.get("current_page", 0)

        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            if search_query:
                users, total_count, total_pages = await service.search_registered_users(
                    search_query, page=current_page
                )
            else:
                users, total_count, total_pages = await service.get_all_registered_users_paginated(
                    page=current_page
                )
            if total_count > 0:
                return {
                    "users": users,
                    "has_users": total_count > 0,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "users_count": total_count,
                    "has_prev": current_page > 0,
                    "has_next": current_page < total_pages - 1,
                    "page_info": f"Страница {current_page + 1} из {total_pages}",
                }
            else:
                await bot.send_message(
                    chat_id=dialog_manager.event.from_user.id,
                    text="Нету пользователь с такими данными, попробуй ещё раз",
                )
                await dialog_manager.switch_to(BanUserStatesGroup.user_list)
                return {
                    "users": users,
                    "has_users": total_count > 0,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "users_count": total_count,
                    "has_prev": current_page > 0,
                    "has_next": current_page < total_pages - 1,
                    "page_info": f"Страница {current_page + 1} из {total_pages}",
                }

    except Exception as e:
        logger.error(f"❌ Error getting users: {e}")
        return {"users": [], "has_users": False, "total_pages": 0}


async def next_page(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Paginate to the next page."""
    current_page = dialog_manager.dialog_data.get("current_page", 0)
    dialog_manager.dialog_data["current_page"] = current_page + 1
    await dialog_manager.update({})


async def prev_page(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Go to a previous page."""
    current_page = dialog_manager.dialog_data.get("current_page", 0)
    dialog_manager.dialog_data["current_page"] = max(0, current_page - 1)
    await dialog_manager.update({})


async def on_search_input(message: Message, _, dialog_manager: DialogManager):
    """Handle search query input."""
    search_query = message.text.strip()
    dialog_manager.dialog_data["search_query"] = search_query
    await dialog_manager.switch_to(BanUserStatesGroup.user_selection)


async def show_all_users(callback: CallbackQuery, button, dialog_manager: DialogManager):
    """Show all registered users."""
    dialog_manager.dialog_data["search_query"] = ""
    await dialog_manager.switch_to(BanUserStatesGroup.user_selection)


user_search_window = Window(
    Const("🚫 <b>Блокировка пользователя</b>\n\n" "Выберите способ поиска пользователя:"),
    Button(Const("👥 Показать всех пользователей"), id="show_all_users", on_click=show_all_users),
    Button(Const("🔍 Найти по имени/email"), id="search_users", on_click=lambda c, b, d: d.next()),
    Button(
        text=Const("🔙 Вернуться в меню"),
        id="admin_main_menu",
        on_click=back_to_admin_menu,
    ),
    state=BanUserStatesGroup.user_search,
)

search_input_window = Window(
    Const("🔍 <b>Поиск пользователя</b>\n\n" "Введите имя, фамилию, username или email:"),
    MessageInput(on_search_input, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Back(Const("⬅️ Назад")),
    state=BanUserStatesGroup.user_list,
)

user_selection_window = Window(
    Format("👥 <b>Найденные пользователи ({users_count}):</b>\n"),
    Column(
        Select(
            Format("👤 {item.first_name} {item.last_name} (@{item.username})"),
            items="users",
            item_id_getter=lambda item: f"user_{item.telegram_id}",
            id="select_user_for_ban",
            on_click=on_user_selected_for_ban,
        ),
    ),
    Row(
        Button(Const("⬅️ Пред"), id="prev_page", on_click=prev_page, when="has_prev"),
        Button(Const("След ➡️"), id="next_page", on_click=next_page, when="has_next"),
    ),
    Button(
        Const("⬅️ Назад к поиску"),
        id="back_to_search",
        on_click=lambda c, b, d: d.switch_to(BanUserStatesGroup.user_search),
    ),
    state=BanUserStatesGroup.user_selection,
    getter=get_registered_users_data,
)

reason_window = Window(
    Const("📝 Введите причину блокировки (или пропустите):"),
    MessageInput(on_ban_reason_input, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Row(
        Button(Const("⏭️ Пропустить"), id="skip_ban_reason", on_click=skip_ban_reason),
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=BanUserStatesGroup.reason,
)

confirmation_window = Window(
    Format(
        "⚠️ <b>Подтвердите блокировку пользователя:</b>\n\n"
        "👤 <b>Пользователь:</b> {dialog_data[user_data]}\n"
        "📝 <b>Причина:</b> {dialog_data[reason]}\n\n"
        "❗️ Пользователь будет заблокирован и уведомлен об этом."
    ),
    Row(
        Button(Const("🚫 Заблокировать"), id="confirm_ban_user", on_click=confirm_ban_user),
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=BanUserStatesGroup.confirmation,
    getter=ban_user_data_getter,
)

ban_user_dialog = Dialog(
    user_search_window,
    search_input_window,
    user_selection_window,
    reason_window,
    confirmation_window,
)
