import asyncio

from aiogram import Bot
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core_settings import base_settings
from src.core_settings import dp as dispatcher
from src.dao.user import UserDAO
from src.database.models import PendingUser, RegisteredUser
from src.services.admin.users_managment.messages import messages
from src.services.admin.users_managment.models import RegisteredUserRole, UserReviewStatus
from src.services.user_registration.models import RegistrationData


class AdminUserManagementService:
    """Service for admin user management operations."""

    def __init__(self, session: AsyncSession, bot: Bot):
        self.user_dao = UserDAO(session)
        self.session = session
        self.bot = bot

    async def get_pending_users(self) -> list[PendingUser]:
        """Get all pending users for admin reviews."""
        try:
            statement = select(PendingUser).order_by(PendingUser.created_at.desc())
            result = await self.session.execute(statement)
            pending_users = result.scalars().all()
            logger.info(f"📋 Retrieved {len(pending_users)} pending users")
            return list(pending_users)
        except Exception as e:
            logger.error(f"❌ Error getting pending users: {e}")
            raise e

    async def approve_pending_user(
        self, telegram_id: int, role: str = RegisteredUserRole.UNDEFINED.value
    ) -> tuple[bool, str]:
        """Approve a pending user and move to registered users.

        Args:
            telegram_id: Pending user's telegram ID
            role: Role to assign to the user

        Returns:
            Tuple of (success, a message)
        """
        try:
            pending_user = await self.user_dao.get_pending_user_by_id(telegram_id)
            if not pending_user:
                return False, messages.not_in_pending_list

            existing_user = await self.user_dao.get_registered_user_by_id(telegram_id)
            if existing_user:
                return False, messages.user_already_registered

            await self.user_dao.approve_user(telegram_id, role)
            await self._notify_user(telegram_id, UserReviewStatus.APPROVED)
            logger.info(f"✅ User {telegram_id} approved with role {role}")
            return True, messages.admin_approve_message(role)

        except Exception as e:
            logger.error(f"❌ Error approving pending user {telegram_id}: {e}")
            return False, messages.error_in_approval_process

    async def reject_pending_user(
        self, telegram_id: int, reason: str | None = None
    ) -> tuple[bool, str]:
        """Reject a pending user registration.

        Args:
            telegram_id: User's telegram ID
            reason: Optional reason for reject

        Returns:
            Tuple of (success, a message)
        """
        try:
            pending_user = await self.user_dao.get_pending_user_by_id(telegram_id)
            if not pending_user:
                return False, messages.not_in_pending_list

            await self.session.delete(pending_user)
            await self._notify_user(telegram_id, UserReviewStatus.REJECTED, reason)
            logger.info(
                f"⚠️ User {telegram_id} registration recjected successfully. Reason: {reason}"
            )
            return True, messages.admin_reject_message(reason)

        except Exception as e:
            logger.error(f"❌ Error rejecting pending user {telegram_id}: {e}")
            return False, messages.error_in_reject_process

    async def add_user_manually(
        self,
        telegram_id: int,
        username: str,
        first_name: str,
        last_name: str | None = None,
        email: str | None = None,
        role: str = RegisteredUserRole.UNDEFINED.value,
    ) -> tuple[bool, str]:
        """Manually add a user to registered users.

        Args:
            telegram_id: User's telegram ID
            first_name: User's first name
            last_name: User's last name
            username: User's telegram username
            email: User's email
            role: User's role

        Returns:
            Tuple of (success, a message)
        """
        try:
            existing_user = await self.user_dao.get_registered_user_by_id(telegram_id)
            if existing_user:
                return False, messages.user_already_registered

            pending_user = await self.user_dao.get_pending_user_by_id(telegram_id)
            if pending_user:
                return False, messages.user_already_pending

            banned_user = await self.user_dao.get_banned_user_by_id(telegram_id)
            if banned_user:
                return False, messages.already_banned

            new_user = RegisteredUser(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
            )
            self.session.add(new_user)
            await self._notify_user(telegram_id, UserReviewStatus.ADDED_MANUALLY)
            logger.info(f"✅ User {telegram_id} manually added with role {role}")
            return True, f"Пользователь добавлен с ролью: {role}"

        except Exception as e:
            logger.error(f"❌ Error manually adding user {telegram_id}: {e}")
            return False, "Ошибка при добавлении пользователя"

    async def ban_user(self, telegram_id: int, reason: str | None = None) -> tuple[bool, str]:
        """Ban a registered user.

        Args:
            telegram_id: User's telegram ID
            reason: Optional reason for a ban

        Returns:
            Tuple of (success, a message)
        """
        try:
            success = await self.user_dao.ban_user(telegram_id)
            if not success:
                return False, messages.user_not_found

            await self._clear_user_state(telegram_id)
            await self._notify_user(telegram_id, UserReviewStatus.BANNED, reason)
            logger.info(f"🚫 User {telegram_id} banned")
            return True, messages.admin_ban_message(reason)

        except Exception as e:
            logger.error(f"❌ Error banning user {telegram_id}: {e}")
            return False, messages.error_in_ban_process

    async def get_all_registered_users_paginated(
        self, page: int = 0, page_size: int = base_settings.INLINE_ROWS_PER_PAGE
    ) -> tuple[list[RegisteredUser], int, int]:
        """Get all registered users with pagination."""

        offset = page * page_size
        users, total_count = await self.user_dao.get_all_registered_users_paginated(
            limit=page_size, offset=offset
        )
        total_pages = (total_count + page_size - 1) // page_size
        return users, total_count, total_pages

    async def search_registered_users(
        self,
        search_query: str,
        page: int = 0,
        page_size: int = base_settings.INLINE_ROWS_PER_PAGE,
    ) -> tuple[list[RegisteredUser], int, int]:
        """Search for registered users based on a search query."""

        try:
            offset = page * page_size
            users, total_count = await self.user_dao.search_registered_users(
                search_query, page_size, offset
            )
            total_pages = (total_count + page_size - 1) // page_size
            return users, total_count, total_pages
        except Exception as e:
            logger.error(f"❌ Error getting users: {e}")
            raise

    async def broadcast_message_to_registered_users(self, message: str) -> tuple[int, int]:
        """Send a message to all registered users.

        Args:
            message: Message to broadcast

        Returns:
            Tuple of (successful_sends, failed_sends)
        """
        registered_users = await self.user_dao.get_all_registered_users()
        if not registered_users:
            return 0, 0

        logger.info(f"📢 Broadcasting message to {len(registered_users)} users")
        successful_sends = 0
        failed_sends = 0

        # Process users in batches of 30 (Telegram's rate limit is 30 messages per second)
        batch_size = 30
        try:
            for i in range(0, len(registered_users), batch_size):
                batch = registered_users[i : i + batch_size]
                tasks = [
                    self.bot.send_message(text=message, chat_id=user.telegram_id) for user in batch
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        failed_sends += 1
                    elif result:
                        successful_sends += 1
                    else:
                        failed_sends += 1
                if i + batch_size < len(registered_users):
                    await asyncio.sleep(1)
            logger.info(f"📢 Broadcast completed: {successful_sends} sent, {failed_sends} failed")
            return successful_sends, failed_sends

        except Exception as e:
            logger.error(f"❌ Error broadcasting message: {e}")
            raise e

    async def notify_admins_new_registration(
        self, user_data: RegistrationData, admin_ids: list[int]
    ):
        """Notify all admins about new user registration."""
        tasks = [
            self.bot.send_message(
                chat_id=admin_id,
                text=messages.notify_admin_about_registration(user_data),
                parse_mode="HTML",
            )
            for admin_id in admin_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful_notifications = sum(1 for result in results if result is True) + 1
        logger.info(
            f"📬 Notified {successful_notifications}/{len(admin_ids)} admins"
            f" about new registration"
        )

    async def _notify_user(
        self, telegram_id: int, decision: UserReviewStatus, reason: str | None = None
    ):
        """"""
        try:
            text = None
            match decision:
                case UserReviewStatus.APPROVED:
                    text = messages.user_approve
                case UserReviewStatus.REJECTED:
                    text = messages.user_rejected(reason)
                case UserReviewStatus.ADDED_MANUALLY:
                    text = messages.user_added_manually
                case UserReviewStatus.BANNED:
                    text = messages.user_banned(reason)
            await self.bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send message to user {telegram_id}: {e}")

    async def _clear_user_state(self, telegram_id: int):
        """Clear the user's FSM state and dialog history."""
        try:
            fsm_context = dispatcher.fsm.get_context(
                bot=self.bot, user_id=telegram_id, chat_id=telegram_id
            )
            await fsm_context.clear()
            logger.debug(f"🧹 Cleared state for banned user {telegram_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clear state for user {telegram_id}: {e}")
