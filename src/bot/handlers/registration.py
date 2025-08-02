from collections.abc import Callable

from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from loguru import logger

from services.user_registration import RegistrationService, messages
from src.database import db


class RegistrationFieldHandler:
    """Handler generator for registration fields."""

    def __init__(self, field_name: str, next_state: State, normalize: Callable | None = None):
        self.field_name = field_name
        self.next_state = next_state
        self.normalize = normalize

    async def __call__(self, message: Message, _, dialog_manager: DialogManager):
        telegram_id = message.from_user.id
        value = message.text.strip()
        if self.normalize:
            value = self.normalize(value)

        async with db.get_session() as session:
            registration_service = RegistrationService(session)
            validation = registration_service.validate_field(
                field_name=self.field_name,
                value=value,
                telegram_id=telegram_id,
                username=message.from_user.username,
            )
        if not validation.is_valid:
            await message.answer(f"❌ {validation.error_message}")
            return

        dialog_manager.dialog_data[self.field_name] = getattr(validation, "cleaned_value", value)
        if self.field_name == "first_name":
            dialog_manager.dialog_data["username"] = message.from_user.username

        logger.info(f"✅ {self.field_name} saved for user {telegram_id}")
        await dialog_manager.switch_to(self.next_state)


async def skip_phone_handler(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    telegram_id = callback.from_user.id
    dialog_manager.dialog_data["phone"] = None
    logger.info(f"📱 Phone skipped for user {telegram_id}")
    await dialog_manager.next()


async def save_registration_data(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    telegram_id = callback.from_user.id
    data = dialog_manager.dialog_data
    try:
        async with db.get_session() as session:
            registration_service = RegistrationService(session)
            exists, status_message = await registration_service.check_existing_user(telegram_id)
            if exists:
                await callback.message.answer(f"⚠️ {status_message}")
                await dialog_manager.done()
                return

            is_valid, error_message, registration_data = (
                registration_service.validate_full_registration(
                    telegram_id=telegram_id,
                    username=data["username"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    email=data["email"],
                    phone=data["phone"],
                    from_whom=data["from_whom"],
                )
            )
            if not is_valid:
                await callback.message.answer(f"❌ {error_message}")
                return

            success = await registration_service.save_registration(
                registration_data=registration_data
            )
            if success:
                await callback.message.answer(messages.registration_success)
                logger.info(f"✅ Registration completed for user {telegram_id}")
            else:
                await callback.message.answer(messages.registration_error)
            await dialog_manager.done()
    except Exception as e:
        logger.error(f"❌ Error in registration for telegram_id: {telegram_id}: {e}")
        await callback.message.answer(messages.registration_error)
