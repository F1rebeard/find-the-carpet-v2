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
        "📱 Введите ваш <b>номер телефона</b>:\n\n"
        "🔹 Формат: +7XXXXXXXXXX или 8XXXXXXXXXX\n"
        "🔹 Или напишите 'пропустить' для пропуска"
    )
    from_whom_prompt: str = (
        "💡 <b>Откуда вы узнали</b> о нашем сервисе?\n\n"
        "(Например: от друзей, из рекламы, в интернете)"
    )
    confirmation_prompt: str = "📋 <b>Проверьте введённые данные:</b>\n"

    # Validation messages
    non_text_error: str = "❌ Пожалуйста, отправьте текстовое сообщение"

    # Success/Error messages
    registration_success: str = (
        "✅ Регистрация успешно отправлена!\n"
        "⏳ Ваша заявка рассматривается администратором.\n"
        "📱 Мы уведомим вас о результате в ближайшее время."
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

    def get_confirmation_text(self, data: dict) -> str:
        """Format confirmation text with user data."""
        phone_text = data.get("phone", "Не указан")

        return (
            f"{self.confirmation_prompt}\n"
            f"👤 <b>Имя:</b> {data['first_name']}\n"
            f"👤 <b>Фамилия:</b> {data['last_name']}\n"
            f"📧 <b>Email:</b> {data['email']}\n"
            f"📱 <b>Телефон:</b> {phone_text}\n"
            f"💡 <b>Откуда узнали:</b> {data['from_whom']}\n\n"
            f"❓ Всё корректно?"
        )

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
