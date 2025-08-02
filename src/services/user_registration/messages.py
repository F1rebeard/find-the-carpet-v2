import dataclasses

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@dataclasses.dataclass
class UserRegistrationMessages:
    """Centralized messages for a registration process."""

    # Dialog step messages
    welcome_message: str = "👋 Добро пожаловать в регистрацию!\n\n👤 Введите ваше <b>имя</b>:"
    first_name_prompt: str = "👤 Введите ваше <b>имя</b>:"
    last_name_prompt: str = "👤 Теперь введите вашу <b>фамилию</b>:"
    email_prompt: str = "📧 Введите ваш <b>email</b>:"
    phone_prompt: str = (
        "📱 Введите ваш <b>номер телефона</b>:\n\n" "🔹 Формат: +7XXXXXXXXXX или 8XXXXXXXXXX\n"
    )
    from_whom_prompt: str = (
        "💡 <b>Откуда вы узнали</b> о нашем боте?\n\n"
        "Например канал в телеграмме, от коллег, сами нашли?"
    )
    confirmation_prompt: str = "📋 <b>Проверьте введённые данные:</b>\n\n"
    confirmation_text = (
        "👤 <b>Имя:</b> {dialog_data[first_name]}\n"
        "👤 <b>Фамилия:</b> {dialog_data[last_name]}\n"
        "📧 <b>Email:</b> {dialog_data[email]}\n"
        "📱 <b>Телефон:</b> {dialog_data[phone]}\n"
        "💡 <b>Откуда узнали:</b> {dialog_data[from_whom]}\n\n"
        "❓ Всё корректно?"
    )
    # Validation messages
    non_text_error: str = "❌ Пожалуйста, отправьте текстовое сообщение"

    # Success/Error messages
    registration_success: str = (
        "✅ Регистрация успешно отправлена!\n\n"
        "⏳ Ваша заявка рассматривается администратором.\n"
        "📱 Мы уведомим вас о результате в ближайшее время, спасибо!"
    )
    registration_error: str = "❌ Произошла ошибка при сохранении регистрации. Попробуйте позже."
    validation_error: str = (
        "❌ Ошибка валидации данных. Пожалуйста, проверьте введённую информацию."
    )

    # Status messages
    already_registered: str = "✅ Вы уже зарегистрированы в системе"
    already_pending: str = "⏳ Ваша заявка уже отправлена и рассматривается"
    user_banned: str = "🚫 Ваш аккаунт заблокирован. Обратитесь в поддержку."

    # Button texts
    start_registration_button: str = "📝 Начать регистрацию"
    confirm_button: str = "✅ Подтвердить"
    back_button: str = "⬅️ Назад"
    cancel_button: str = "❌ Отмена"
    edit_button: str = "⬅️ Изменить"
    skip_button: str = "⏭️ Пропустить"

    @staticmethod
    def get_start_keyboard() -> InlineKeyboardMarkup:
        """Get a keyboard for starting registration."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Начать регистрацию", callback_data="start_registration"
                    )
                ]
            ]
        )


messages = UserRegistrationMessages()
