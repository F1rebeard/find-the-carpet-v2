from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Row
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger
from pydantic import ValidationError

from src.bot.handlers.admin_menu import back_to_admin_menu
from src.bot.handlers.utils import reject_non_text, skip_optional_field
from src.core_settings import bot
from src.database import db
from src.services.admin.manual_registration.models import ManualUserRegistrationData
from src.services.admin.manual_registration.service import ValidateManualRegistrationService
from src.services.admin.states import AddUserStatesGroup
from src.services.admin.users_managment import AdminUserManagementService
from src.services.admin.users_managment.models import RegisteredUserRole


class AddUserFieldHandler:
    def __init__(self, field_name: str, optional: bool = False):
        self.field_name = field_name
        self.optional = optional

    async def __call__(self, message: Message, _, dialog_manager: DialogManager):
        value = message.text.strip()

        if self.optional and not value:
            dialog_manager.dialog_data[self.field_name] = None
            await dialog_manager.next()
            return

        result = ValidateManualRegistrationService.validate_field(
            field_name=self.field_name, value=value
        )

        if not result.is_valid:
            await message.answer(f"❌ {result.error_message}")
            return

        dialog_manager.dialog_data[self.field_name] = result.cleaned_value
        logger.debug(f"📝 Add user field '{self.field_name}' saved: {result.cleaned_value}")
        await dialog_manager.next()


async def on_role_selection(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handle role selection."""
    role_map = {
        "role_colleague": RegisteredUserRole.COLLEAGUE.value,
        "role_designer": RegisteredUserRole.DESIGNER.value,
        "role_undefined": RegisteredUserRole.UNDEFINED.value,
    }
    role = role_map.get(button.widget_id, RegisteredUserRole.UNDEFINED.value)
    dialog_manager.dialog_data["role"] = role
    await dialog_manager.next()


async def confirm_add_user(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Confirm and add user."""
    try:
        data = dialog_manager.dialog_data

        try:
            manual_registration_data = ManualUserRegistrationData(
                telegram_id=int(data["telegram_id"]),
                username=data.get("username", None),
                first_name=data.get("first_name", None),
                last_name=data.get("last_name", "Не заполнено"),
                email=data.get("email", "Не заполнено"),
                from_whom="Добавлен администратором",
            )
            strict = manual_registration_data.to_strict_registration()

        except ValidationError as e:
            error_messages = [f"• {err['loc'][-1]}: {err['msg']}" for err in e.errors()]
            logger.error("❌ Validation error:\n" + "\n".join(error_messages))
            await callback.message.answer("❌ Ошибки валидации:\n" + "\n".join(error_messages))
            return

        async with db.get_session() as session:
            service = AdminUserManagementService(session, bot)
            success, message = await service.add_user_manually(
                telegram_id=strict.telegram_id,
                username=strict.username,
                first_name=strict.first_name,
                last_name=strict.last_name,
                email=strict.email,
                role=data["role"],
            )
            if success:
                await callback.message.answer(f"✅ {message}")
                logger.info(
                    f"✅ Admin {callback.from_user.id} manually added user {strict.telegram_id}"
                )
            else:
                await callback.message.answer(f"❌ {message}")

            await dialog_manager.done()

    except Exception as e:
        logger.error(f"❌ Error adding user manually: {e}")
        await callback.message.answer("❌ Ошибка добавления пользователя")
        await dialog_manager.done()


async def add_user_data_getter(dialog_manager: DialogManager, **kwargs):
    """Get add user dialog data for display."""
    data = dialog_manager.dialog_data.copy()
    data["username"] = data.get("username") or "не указан"
    data["last_name"] = data.get("last_name") or "не указана"
    data["email"] = data.get("email") or "не указан"
    return {"dialog_data": data}


async def on_role_selected(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Handle user selection role."""

    role_map = {
        "role_colleague": RegisteredUserRole.COLLEAGUE.value,
        "role_designer": RegisteredUserRole.DESIGNER.value,
        "role_undefined": RegisteredUserRole.UNDEFINED.value,
    }
    role = role_map.get(button.widget_id, RegisteredUserRole.UNDEFINED.value)
    dialog_manager.dialog_data["role"] = role
    await dialog_manager.next()


telegram_id_handler = AddUserFieldHandler("telegram_id")
username_handler = AddUserFieldHandler("username", optional=True)
first_name_handler = AddUserFieldHandler("first_name")
last_name_handler = AddUserFieldHandler("last_name", optional=True)
email_handler = AddUserFieldHandler("email", optional=True)


telegram_id_window = Window(
    Const("🆔 <b>Добавление пользователя</b>\n\nВведите Telegram ID пользователя:"),
    MessageInput(telegram_id_handler, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Button(
        text=Const("🔙 Вернуться в меню"),
        id="admin_main_menu",
        on_click=back_to_admin_menu,
    ),
    state=AddUserStatesGroup.telegram_id,
)

username_window = Window(
    Const("📝 Введите username пользователя (или пропустите):"),
    MessageInput(username_handler, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Row(
        Button(Const("⏭️ Пропустить"), id="skip_username", on_click=skip_optional_field),
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=AddUserStatesGroup.username,
)

first_name_window = Window(
    Const("👤 Введите имя пользователя:"),
    MessageInput(first_name_handler, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Row(
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=AddUserStatesGroup.first_name,
)

last_name_window = Window(
    Const("👤 Введите фамилию пользователя (или пропустите):"),
    MessageInput(last_name_handler, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Row(
        Button(Const("⏭️ Пропустить"), id="skip_last_name", on_click=skip_optional_field),
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=AddUserStatesGroup.last_name,
)

email_window = Window(
    Const("📧 Введите email пользователя (или пропустите):"),
    MessageInput(email_handler, content_types=[ContentType.TEXT]),
    MessageInput(reject_non_text),
    Row(
        Button(Const("⏭️ Пропустить"), id="skip_email", on_click=skip_optional_field),
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=AddUserStatesGroup.email,
)

role_window = Window(
    Const("🎭 Выберите роль пользователя:"),
    Column(
        Button(Const("👨‍💼 Коллега"), id="role_colleague", on_click=on_role_selected),
        Button(Const("🎨 Дизайнер"), id="role_designer", on_click=on_role_selected),
        Button(Const("❓ Неопределенная"), id="role_undefined", on_click=on_role_selected),
    ),
    Row(
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=AddUserStatesGroup.role,
)

confirmation_window = Window(
    Format(
        "📋 <b>Подтвердите добавление пользователя:</b>\n\n"
        "🆔 <b>ID:</b> <code>{dialog_data[telegram_id]}</code>\n"
        "📝 <b>Username:</b> @{dialog_data[username]}\n"
        "👤 <b>Имя:</b> {dialog_data[first_name]} {dialog_data[last_name]}\n"
        "📧 <b>Email:</b> {dialog_data[email]}\n"
        "🎭 <b>Роль:</b> {dialog_data[role]}\n\n"
        "Подтвердить добавление?"
    ),
    Row(
        Button(Const("✅ Подтвердить"), id="confirm_add_user", on_click=confirm_add_user),
        Back(Const("⬅️ Назад")),
        Cancel(Const("❌ Отмена")),
    ),
    state=AddUserStatesGroup.confirmation,
    getter=add_user_data_getter,
)

add_user_dialog = Dialog(
    telegram_id_window,
    username_window,
    first_name_window,
    last_name_window,
    email_window,
    role_window,
    confirmation_window,
)
