from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from core_settings import base_settings
from services.user_registration import messages


async def reject_non_text(
    message: Message, message_input: MessageInput, dialog_manager: DialogManager
):
    """Handle non-text messages."""
    await message.answer(messages.non_text_error)


async def data_getter(dialog_manager: DialogManager, **kwargs):
    """Get data from a dialog manager."""
    return dialog_manager.dialog_data


async def is_admin_message(message: Message) -> bool:
    """Check if user is an admin."""
    return message.from_user.id in base_settings.ADMIN_IDS


async def is_admin_callback(callback: CallbackQuery) -> bool:
    """Check if user is an admin."""
    return callback.from_user.id in base_settings.ADMIN_IDS


async def skip_optional_field(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Skip optional field."""
    field_name = button.widget_id.replace("skip_", "")
    dialog_manager.dialog_data[field_name] = None
    await dialog_manager.next()
