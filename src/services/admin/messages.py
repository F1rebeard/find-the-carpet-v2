import dataclasses
from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database.models.users import PendingUser


@dataclasses.dataclass
class AdminMessages:
    """Centralized messages for admin functionality."""

    # Main menu
    admin_welcome: str = "👑 <b>Панель администратора</b>\n\n" "Выбери действие:"

    # Pending users
    pending_users_title: str = "⏳ <b>Заявки на регистрацию</b>\n\n"
    no_pending_users: str = "✅ Нет заявок на рассмотрение"

    pending_user_details = (
        "👤 <b>Данные пользователя:</b>\n\n"
        "🆔 <b>ID:</b> <code>{telegram_id}</code>\n"
        "👤 <b>Имя:</b> {first_name} {last_name}\n"
        "📧 <b>Email:</b> {email}\n"
        "📱 <b>Телефон:</b> {phone}\n"
        "💡 <b>Откуда узнал:</b> {from_whom}\n"
        "📅 <b>Дата заявки:</b> {created_at}\n\n"
        "Выберите действие:"
    )

    approve_role_prompt: str = (
        "✅ <b>Одобрить пользователя</b>\n\n" "Выберите роль для пользователя:"
    )

    decline_reason_prompt: str = (
        "❌ <b>Отклонить заявку</b>\n\n" "Введите причину отклонения (необязательно):"
    )

    # Manual user addition
    manual_add_prompt: str = "➕ <b>Добавить пользователя вручную</b>\n\n"
    manual_add_telegram_id: str = "🆔 Введите Telegram ID пользователя:"
    manual_add_first_name: str = "👤 Введите имя пользователя:"
    manual_add_last_name: str = "👤 Введите фамилию пользователя (или пропустите):"
    manual_add_username: str = "📝 Введите username пользователя (или пропустите):"
    manual_add_email: str = "📧 Введите email пользователя (или пропустите):"
    manual_add_role: str = "🎭 Выберите роль пользователя:"

    manual_add_confirmation = (
        "📋 <b>Подтвердите добавление пользователя:</b>\n\n"
        "🆔 <b>ID:</b> <code>{telegram_id}</code>\n"
        "👤 <b>Имя:</b> {first_name} {last_name}\n"
        "📝 <b>Username:</b> @{username}\n"
        "📧 <b>Email:</b> {email}\n"
        "🎭 <b>Роль:</b> {role}\n\n"
        "Подтвердить добавление?"
    )

    # User banning
    ban_user_prompt: str = "🚫 <b>Заблокировать пользователя</b>\n\n"
    ban_telegram_id: str = "🆔 Введите Telegram ID пользователя для блокировки:"
    ban_reason_prompt: str = "📝 Введите причину блокировки (необязательно):"
    ban_confirmation = (
        "⚠️ <b>Подтвердите блокировку пользователя:</b>\n\n"
        "🆔 <b>ID:</b> <code>{telegram_id}</code>\n"
        "📝 <b>Причина:</b> {reason}\n\n"
        "❗️ Пользователь будет заблокирован и уведомлен об этом."
    )

    # Google Sheets sync
    sync_choose_table_prompt: str = (
        "🔄 <b>Синхронизация Google Таблиц</b>\n\n"
        "📊 Выберите таблицу для синхронизации:\n\n"
        "🔗 <b>Источник:</b> Google Spreadsheet"
    )

    sync_carpets_prompt: str = (
        "🔄 <b>Синхронизация Google Таблиц</b>\n\n"
        "📊 <b>Таблица:</b> Ковры\n"
        "🔗 <b>Источник:</b> Google Spreadsheet\n\n"
        "⚠️ Синхронизация обновит данные о коврах в базе данных.\n"
        "Продолжить?"
    )

    sync_sales_prompt: str = (
        "🔄 <b>Синхронизация Google Таблиц</b>\n\n"
        "📊 <b>Таблица:</b> Продажи\n"
        "🔗 <b>Источник:</b> Google Spreadsheet\n\n"
        "⚠️ Синхронизация обновит данные о продажах в базе данных.\n"
        "Продолжить?"
    )

    sync_starting: str = "🔄 Запуск синхронизации..."
    sync_fetching: str = "📥 Загрузка данных из Google Таблиц..."
    sync_processing: str = "⚙️ Обработка данных..."
    sync_saving: str = "💾 Сохранение в базу данных..."

    sync_completed = (
        "✅ <b>Синхронизация завершена</b>\n\n"
        "📊 <b>Статистика:</b>\n"
        "• Всего строк: {total_rows}\n"
        "• Добавлено: {inserted}\n"
        "• Обновлено: {updated}\n"
        "• Ошибка в данных: {bad_data}\n"
        "• Пропущено: {skipped}\n"
    )

    sync_completed_with_errors = (
        "⚠️ <b>Синхронизация завершена с ошибками</b>\n\n"
        "📊 <b>Статистика:</b>\n"
        "• Всего строк: {total_rows}\n"
        "• Добавлено: {inserted}\n"
        "• Обновлено: {updated}\n"
        "• Ошибка в данных: {bad_data}\n"
        "• Пропущено: {skipped}\n\n"
        "❌ <b>Ошибки валидации:</b>\n{invalid_report}"
    )

    sync_error: str = "❌ Ошибка при синхронизации: {error}"

    # Broadcasting
    broadcast_prompt: str = (
        "📢 <b>Рассылка сообщения</b>\n\n" "Введите сообщение для отправки всем пользователям:"
    )

    broadcast_confirmation = (
        "📢 <b>Подтвердите рассылку:</b>\n\n"
        "📝 <b>Сообщение:</b>\n{message}\n\n"
        "👥 <b>Получатели:</b> Все зарегистрированные пользователи\n\n"
        "Отправить сообщение?"
    )

    # Success/Error messages
    user_approved: str = "✅ Пользователь одобрен"
    user_declined: str = "❌ Заявка отклонена"
    user_added: str = "✅ Пользователь добавлен"
    user_banned: str = "🚫 Пользователь заблокирован"
    broadcast_completed: str = "📢 Рассылка завершена: {sent} отправлено, {failed} ошибок"

    operation_cancelled: str = "❌ Операция отменена"
    invalid_telegram_id: str = "❌ Некорректный Telegram ID"
    user_not_found: str = "❌ Пользователь не найден"
    operation_error: str = "❌ Произошла ошибка при выполнении операции"

    # Button texts
    btn_pending_users: str = "⏳ Заявки на регистрацию"
    btn_add_user: str = "➕ Добавить пользователя"
    btn_ban_user: str = "🚫 Заблокировать пользователя"
    btn_broadcast: str = "📢 Рассылка"
    btn_sync_google_sheets: str = "🔄 Синхронизация Google Таблиц"
    btn_back: str = "⬅️ Назад"
    btn_cancel: str = "❌ Отмена"
    btn_approve: str = "✅ Одобрить"
    btn_decline: str = "❌ Отклонить"
    btn_confirm: str = "✅ Подтвердить"
    btn_skip: str = "⏭️ Пропустить"

    # Role buttons
    btn_role_user: str = "👤 Пользователь"
    btn_role_moderator: str = "👮 Модератор"
    btn_role_admin: str = "👑 Администратор"

    # Table sync buttons
    btn_sync_carpets: str = "🧿 Ковры"
    btn_sync_sales: str = "💰 Продажи"

    @staticmethod
    def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
        """Get main admin menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏳ Заявки на регистрацию", callback_data="admin_pending_users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Добавить пользователя", callback_data="admin_add_user"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚫 Заблокировать пользователя", callback_data="admin_ban_user"
                    )
                ],
                [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
                [
                    InlineKeyboardButton(
                        text="🔄 Синхронизация Google Таблиц",
                        callback_data="admin_sync_google_sheets",
                    )
                ],
            ]
        )

    @staticmethod
    def get_pending_users_keyboard(users: List[PendingUser]) -> InlineKeyboardMarkup:
        """Get keyboard with a pending users list."""
        buttons = []
        for user in users:
            display_name = f"{user.first_name} {user.last_name or ''}".strip()
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"👤 {display_name} (ID: {user.telegram_id})",
                        callback_data=f"admin_pending_user_{user.telegram_id}",
                    )
                ]
            )

        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_menu")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def get_pending_user_actions_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
        """Get keyboard for pending user actions."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить", callback_data=f"admin_approve_{telegram_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отклонить", callback_data=f"admin_decline_{telegram_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад к списку", callback_data="admin_pending_users"
                    )
                ],
            ]
        )

    @staticmethod
    def get_role_selection_keyboard() -> InlineKeyboardMarkup:
        """Get role selection keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 Пользователь", callback_data="admin_role_user")],
                [InlineKeyboardButton(text="👮 Модератор", callback_data="admin_role_moderator")],
                [InlineKeyboardButton(text="👑 Администратор", callback_data="admin_role_admin")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")],
            ]
        )

    @staticmethod
    def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
        """Get confirmation keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить", callback_data=f"admin_confirm_{action}"
                    )
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")],
            ]
        )

    @staticmethod
    def get_skip_keyboard() -> InlineKeyboardMarkup:
        """Get skip keyboard for optional fields."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="admin_skip")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")],
            ]
        )

    @staticmethod
    def get_table_selection_keyboard() -> InlineKeyboardMarkup:
        """Get a table selection keyboard for Google Sheets sync."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🧿 Ковры", callback_data="admin_sync_table_carpets")],
                [InlineKeyboardButton(text="💰 Продажи", callback_data="admin_sync_table_sales")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_menu")],
            ]
        )


messages = AdminMessages()
