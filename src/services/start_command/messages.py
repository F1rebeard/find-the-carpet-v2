import dataclasses

from aiogram.types import InlineKeyboardMarkup

from src.services.user_registration.messages import messages as reg_messages


@dataclasses.dataclass
class StartCommandMessages:
    """Centralized messages for start command responses."""

    welcome_new_user: str = (
        "🎉 Добро пожаловать! Пожалуйста, завершите регистрацию для продолжения."
    )
    welcome_admin: str = "👑 С возвращением, Администратор"
    welcome_registered: str = "✅ С возвращением"
    pending_status: str = (
        "⏳ Ваша регистрация ожидает подтверждения. Пожалуйста, дождитесь подтверждения администратора."
    )
    banned_message: str = "🚫 Ваш аккаунт заблокирован."
    error_message: str = "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
    new_user_instructions: str = "📝 Используйте кнопку ниже для начала процесса регистрации."
    admin_menu: str = (
        "🛠 Команды администратора:\n"
        "👨‍💼 /admin - Панель администратора\n"
        "👥 /users - Управление пользователями\n"
        "⏳ /pending - Заявки на регистрацию"
    )
    main_menu: str = (
        "📋 Доступные команды:\n"
        "🔍 /search - Поиск ковров\n"
        "❤️ /favorites - Избранные\n"
        "👤 /profile - Профиль"
    )
    pending_info: str = "📄 Ваши данные регистрации отправлены и находятся на рассмотрении."
    unknown_error: str = "⚠️ Что-то пошло не так. Пожалуйста, попробуйте снова."
    processing_error: str = "⚠️ Что-то пошло не так. Попробуйте позже"

    def get_welcome_registered_with_name(self, name: str) -> str:
        """Get a registered user welcome message with name."""
        return f"{self.welcome_registered}, {name}!"

    @staticmethod
    def get_registration_keyboard() -> InlineKeyboardMarkup:
        """Get inline keyboard for new user registration."""
        return reg_messages.get_start_keyboard()

    @staticmethod
    def get_full_message(base_message: str, additional_info: str = "") -> str:
        """Combine a base message with additional information."""
        if additional_info:
            return f"{base_message}\n\n{additional_info}"
        return base_message


messages = StartCommandMessages()
