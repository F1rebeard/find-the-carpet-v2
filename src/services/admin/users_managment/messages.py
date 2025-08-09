import dataclasses

from src.schemas.users import UserRegistrationInput


@dataclasses.dataclass
class UsersManagementMessages:
    """Centralized messages for user management."""

    not_in_pending_list: str = "Пользователь не найден в списке ожидающих"
    user_not_found: str = "Пользователь не найден"
    already_pending: str = "Пользователь есть в списке ожидающих. Используйте команду одобрения"
    already_registered: str = "Пользователь уже зарегистрирован"
    already_banned: str = "Пользователь заблокирован. Сначала разблокируйте его."
    error_in_approval_process: str = "❌ Ошибка при одобрении регистрации пользователя"
    error_in_reject_process: str = "❌ Ошибка при отклонении регистрации пользователя"
    error_in_banning_process: str = "❌ Ошибка при блокировке пользователя"
    user_added_manually: str = (
        "✅ Администратор добавил ваc!\n\n"
        "Теперь у вас есть доступ к боту.\n\n"
        "Используйте /start для начала работы."
    )
    user_approve: str = (
        "✅ <b>Регистрация одобрена!</b>\n\n"
        "Добро пожаловать! Теперь у вас есть доступ к боту.\n\n"
        "Используйте /start для начала работы."
    )

    @staticmethod
    def user_rejected(reason: str | None = None) -> str:
        message = (
            "❌ <b>Регистрация отклонена</b>\n\n"
            "К сожалению, ваша заявка на регистрацию была отклонена.\n\n"
        )
        if reason:
            message += f"Причина: {reason}\n\n"
        return message

    @staticmethod
    def user_banned(reason: str | None = None) -> str:
        message = "🚫 <b>Ваш аккаунт заблокирован</b>\n\n" "Ваш доступ к боту был ограничен.\n\n"
        if reason:
            message += f"Причина: {reason}\n\n"
        return message

    @staticmethod
    def admin_reject_message(reason: str | None = None) -> str:
        message = f"Регистрация отклонена, причина: {reason}" if reason else "Регистрация отклонена"
        return message

    @staticmethod
    def admin_approve_message(role: str) -> str:
        return f"Пользователь одобрен с ролью: {role}"

    @staticmethod
    def admin_ban_message(reason: str | None = None) -> str:
        message = (
            f"Пользователь заблокирован, причина: {reason}"
            if reason
            else ("Пользователь " "заблокирован")
        )
        return message

    @staticmethod
    def notify_admin_about_registration(user_data: UserRegistrationInput) -> str:
        message = (
            "🆕 <b>Новая заявка на регистрацию!</b>\n\n"
            f"👤 <b>Имя:</b> {user_data.first_name} {user_data.last_name or ''}\n"
            f"🆔 <b>Telegram ID:</b> <code>{user_data.telegram_id}</code>\n"
            f"👤 <b>Username:</b> @{user_data.username or 'не указан'}\n"
            f"📧 <b>Email:</b> {user_data.email or 'не указан'}\n"
            f"📱 <b>Телефон:</b> {user_data.phone or 'не указан'}\n"
            f"💡 <b>Откуда узнал:</b> {user_data.from_whom}\n\n"
            "Используйте команды администратора для одобрения или отклонения заявки."
        )
        return message


messages = UsersManagementMessages()
