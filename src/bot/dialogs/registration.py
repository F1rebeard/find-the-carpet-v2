from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const
from loguru import logger

from src.database import db
from src.services.user_registration import RegistrationService, RegistrationStatesGroup, messages

registration_router = Router()


async def reject_non_text(
    message: Message, message_input: MessageInput, dialog_manager: DialogManager
):
    """Handle non-text messages."""
    await message.answer(messages.non_text_error)


async def first_name_handler(
    message: Message, message_input: MessageInput, dialog_manager: DialogManager
):
    """Handle and validate first name input."""
    telegram_id = message.from_user.id
    username = message.from_user.username

    async with db.get_session() as session:
        registration_service = RegistrationService(session)
        validation = registration_service.validate_field(
            field_name="first_name",
            value=message.text.strip(),
            telegram_id=telegram_id,
            username=username,
        )

    if not validation.is_valid:
        await message.answer(f"❌ {validation.error_message}")
        return

    dialog_manager.dialog_data["first_name"] = message.text.strip()
    logger.info(f"👤 First name saved for user {telegram_id}")
    await dialog_manager.switch_to(RegistrationStatesGroup.last_name)


async def data_getter(dialog_manager: DialogManager, **kwargs):
    """Get data from a dialog manager."""
    return {"dialog_data": dialog_manager.dialog_data}


@registration_router.callback_query(F.data == "start_registration")
async def start_registration_dialog(callback: CallbackQuery, dialog_manager: DialogManager):
    try:
        telegram_id = callback.from_user.id
        logger.info(f"🚀 Starting registration for user {telegram_id}")
        async with db.get_session() as session:
            registration_service = RegistrationService(session)
            exists, status_message = await registration_service.check_existing_user(telegram_id)
            if exists:
                await callback.message.answer(f"⚠️ {status_message}")
                return

        await dialog_manager.start(
            state=RegistrationStatesGroup.first_name, mode=StartMode.RESET_STACK
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error starting registration dialog for {telegram_id}: {e}")
        await callback.message.answer("⚠️ Произошла ошибка при запуске регистрации")
        await callback.answer()


registration_dialog = Dialog(
    Window(
        Const(messages.welcome_message),
        MessageInput(first_name_handler, content_types=[ContentType.TEXT]),
        MessageInput(reject_non_text),
        Cancel(Const(messages.cancel_button)),
        state=RegistrationStatesGroup.first_name,
        getter=data_getter,
    ),
)
