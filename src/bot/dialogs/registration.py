from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from src.bot.handlers.registration import (
    RegistrationFieldHandler,
    save_registration_data,
    skip_phone_handler,
)
from src.bot.handlers.utils import data_getter, reject_non_text
from src.database import db
from src.services.user_registration import RegistrationService, RegistrationStatesGroup, messages
from src.services.user_registration.models import DialogStructure, DialogWindowData

registration_router = Router()


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


DIALOG_STRUCTURE = DialogStructure(
    fields=[
        DialogWindowData(
            field="first_name",
            prompt=messages.welcome_message,
            next_state=RegistrationStatesGroup.last_name,
        ),
        DialogWindowData(
            field="last_name",
            prompt=messages.last_name_prompt,
            next_state=RegistrationStatesGroup.email,
        ),
        DialogWindowData(
            field="email",
            prompt=messages.email_prompt,
            next_state=RegistrationStatesGroup.phone,
            normalize=str.lower,
        ),
        DialogWindowData(
            field="phone",
            prompt=messages.phone_prompt,
            next_state=RegistrationStatesGroup.from_whom,
            skip_button=True,
        ),
        DialogWindowData(
            field="from_whom",
            prompt=messages.from_whom_prompt,
            next_state=RegistrationStatesGroup.confirmation,
        ),
    ]
)

dialogs_windows = []
for window_data in DIALOG_STRUCTURE.fields:
    handler = RegistrationFieldHandler(
        field_name=window_data.field,
        next_state=window_data.next_state,
        normalize=window_data.normalize,
    )
    buttons = [
        Back(Const(messages.back_button)),
        Cancel(Const(messages.cancel_button)),
    ]
    if window_data.skip_button:
        buttons.insert(
            0,
            Button(
                Const(messages.skip_button),
                id=f"skip_{window_data.field}",
                on_click=skip_phone_handler,
            ),
        )
    win = Window(
        Const(window_data.prompt),
        MessageInput(handler, content_types=[ContentType.TEXT]),
        MessageInput(reject_non_text),
        Row(*buttons),
        state=getattr(RegistrationStatesGroup, window_data.field),
    )
    dialogs_windows.append(win)

confirmation_window = Window(
    Const(messages.confirmation_prompt),
    Format(messages.confirmation_text),
    Row(
        Button(
            Const(messages.confirm_button),
            id="confirm_registration",
            on_click=save_registration_data,
        ),
    ),
    Row(
        Back(Const(messages.edit_button)),
        Cancel(Const(messages.cancel_button)),
    ),
    state=RegistrationStatesGroup.confirmation,
    getter=data_getter,
)

registration_dialog = Dialog(*dialogs_windows, confirmation_window)
