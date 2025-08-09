from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.common import Actionable
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Row, Select
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from src.bot.handlers.admin_menu import back_to_admin_menu
from src.bot.handlers.utils import reject_non_text
from src.core_settings import bot
from src.database import db
from src.database.models import PendingUser
from src.services.admin.states import PendingUsersStatesGroup
from src.services.admin.users_managment import AdminUserManagementService
from src.services.admin.users_managment.models import RegisteredUserRole


async def pending_users_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    """Get pending users data from a database."""
    try:
        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            pending_users = await service.get_pending_users()
            return {
                "pending_users": pending_users,
                "has_pending_users": len(pending_users) > 0,
                "pending_users_count": len(pending_users),
            }

    except Exception as e:
        logger.error(f"❌ Error getting pending users: {e}")
        return {"pending_users": [], "has_pending_users": False, "pending_users_count": 0}


async def pending_users_details_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    """Get selected pending user details."""
    try:
        selected_user_id = dialog_manager.dialog_data.get("selected_user_id")
        if not selected_user_id:
            return {}

        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            pending_users = await service.get_pending_users()
            user: PendingUser = next(
                (u for u in pending_users if u.telegram_id == selected_user_id), None
            )
            if not user:
                return {}

            return {
                "user": user,  # TODO Do i need it?
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "last_name": user.last_name or "не указана",
                "email": user.email or "не указан",
                "phone": user.phone or "не указан",
                "username": user.username or "не указан",
                "from_whom": user.from_whom,
                "created_at": user.created_at.strftime("%d.%m.%Y %H:%M"),
            }
    except Exception as e:
        logger.error(f"❌ Error getting user details: {e}")
        return {}


async def on_user_selected(
    callback: CallbackQuery,
    widget: Actionable,
    dialog_manager: DialogManager,
    item_id: str,
):
    """Handle user selection."""
    try:
        telegram_id = int(item_id.split("_")[1])
        dialog_manager.dialog_data["selected_user_id"] = telegram_id
        await dialog_manager.switch_to(PendingUsersStatesGroup.user_details)
    except Exception as e:
        logger.error(f"❌ Error selecting user: {e}")
        await callback.message.answer("❌ Ошибка выбора пользователя")


async def on_approve_user(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handle user approval button."""
    await dialog_manager.switch_to(PendingUsersStatesGroup.approve_role)


async def on_decline_user(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handle user decline button."""
    await dialog_manager.switch_to(PendingUsersStatesGroup.decline_reason)


async def on_role_selected(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handle user role selection."""
    try:
        role_map = {
            "role_colleague": RegisteredUserRole.COLLEAGUE.value,
            "role_designer": RegisteredUserRole.DESIGNER.value,
            "role_undefined": RegisteredUserRole.UNDEFINED.value,
        }
        role = role_map.get(button.widget_id, RegisteredUserRole.UNDEFINED.value)
        telegram_id = dialog_manager.dialog_data["selected_user_id"]

        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            success, message = await service.approve_pending_user(telegram_id, role)
            if success:
                await callback.message.answer(f"✅ {message}")
                logger.info(f"✅ Admin {callback.from_user.id} approved user {telegram_id}")
            else:
                await callback.message.answer(f"❌ {message}")
        await dialog_manager.done()

    except Exception as e:
        logger.error(f"❌ Error approving user: {e}")
        await callback.message.answer("❌ Ошибка одобрения пользователя")
        await dialog_manager.done()


async def on_decline_reason_input(message: Message, _: Actionable, dialog_manager: DialogManager):
    """Handle decline reason input."""
    try:
        reason = message.text.strip() if message.text else None
        telegram_id = dialog_manager.dialog_data["selected_user_id"]
        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            success, response_message = await service.reject_pending_user(telegram_id, reason)
            if success:
                await message.answer(f"❌ {response_message}")
                logger.info(f"❌ Admin {message.from_user.id} declined user {telegram_id}")
            else:
                await message.answer(f"❌ {response_message}")
        await dialog_manager.done()

    except Exception as e:
        logger.error(f"❌ Error declining user: {e}")
        await message.answer("❌ Ошика отклонения заявки")
        await dialog_manager.done()


async def skip_decline_reason(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Skip decline reasone and decline user."""
    try:
        telegram_id = dialog_manager.dialog_data["selected_user_id"]
        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            success, message = await service.reject_pending_user(telegram_id, None)
            if success:
                await callback.message.answer(f"❌ {message}")
                logger.info(f"❌ Admin {callback.from_user.id} declined user {telegram_id}")
            else:
                await callback.message.answer(f"❌ {message}")
        await dialog_manager.done()

    except Exception as e:
        logger.error(f"❌ Error declining user: {e}")
        await callback.message.answer("❌ Ошибка отклонения заявки")
        await dialog_manager.done()


users_list_window = Window(
    Const("⏳ <b>Заявки на регистрацию</b>\n\n"),
    Format("📊 Всего заявок: {pending_users_count}"),
    Select(
        Format("👤 {item.first_name} {item.last_name} (ID: {item.telegram_id})"),
        items="pending_users",
        item_id_getter=lambda item: f"user_{item.telegram_id}",
        id="select_pending_user",
        on_click=on_user_selected,
    ),
    Button(
        text=Const("🔙 Вернуться в меню"),
        id="admin_main_menu",
        on_click=back_to_admin_menu,
    ),
    state=PendingUsersStatesGroup.users_list,
    getter=pending_users_getter,
)

user_details_window = Window(
    Format(
        "👤 <b>Данные пользователя:</b>\n\n"
        "🆔 <b>ID:</b> <code>{telegram_id}</code>\n"
        "👤 <b>Имя:</b> {first_name} {last_name}\n"
        "📝 <b>Username:</b> @{username}\n"
        "📧 <b>Email:</b> {email}\n"
        "📱 <b>Телефон:</b> {phone}\n"
        "💡 <b>Откуда узнал:</b> {from_whom}\n"
        "📅 <b>Дата заявки:</b> {created_at}\n\n"
        "Выберите действие:"
    ),
    Row(
        Button(Const("✅ Одобрить"), id="approve_user", on_click=on_approve_user),
        Button(Const("❌ Отклонить"), id="decline_user", on_click=on_decline_user),
    ),
    Button(
        Const("⬅️ Назад к списку"),
        id="back_to_list",
        on_click=lambda c, b, d: d.switch_to(PendingUsersStatesGroup.users_list),
    ),
    state=PendingUsersStatesGroup.user_details,
    getter=pending_users_details_getter,
)

approve_role_window = Window(
    Const("✅ <b>Выберите роль для пользователя:</b>\n"),
    Column(
        Button(Const("👨‍💼 Коллега"), id="role_colleague", on_click=on_role_selected),
        Button(Const("🎨 Дизайнер"), id="role_designer", on_click=on_role_selected),
        Button(Const("❓ Неопределенная"), id="role_undefined", on_click=on_role_selected),
    ),
    Button(
        Const("⬅️ Назад"),
        id="back_to_details",
        on_click=lambda c, b, d: d.switch_to(PendingUsersStatesGroup.user_details),
    ),
    state=PendingUsersStatesGroup.approve_role,
)

decline_reason_window = Window(
    Const("❌ <b>Введите причину отклонения</b> (или пропустите):\n"),
    MessageInput(on_decline_reason_input, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Row(
        Button(Const("⏭️ Пропустить"), id="skip_reason", on_click=skip_decline_reason),
        Button(
            Const("⬅️ Назад"),
            id="back_to_details",
            on_click=lambda c, b, d: d.switch_to(PendingUsersStatesGroup.user_details),
        ),
    ),
    state=PendingUsersStatesGroup.decline_reason,
)

pending_users_dialog = Dialog(
    users_list_window,
    user_details_window,
    approve_role_window,
    decline_reason_window,
)
