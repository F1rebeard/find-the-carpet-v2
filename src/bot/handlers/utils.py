from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput

from services.user_registration import messages


async def reject_non_text(
    message: Message, message_input: MessageInput, dialog_manager: DialogManager
):
    """Handle non-text messages."""
    await message.answer(messages.non_text_error)


async def data_getter(dialog_manager: DialogManager, **kwargs):
    """Get data from a dialog manager."""
    return dialog_manager.dialog_data
