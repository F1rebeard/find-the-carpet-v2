import asyncio
import dataclasses
import enum

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core_settings import base_settings as settings
from src.dao.user import UserDAO
from src.database.models import BannedUser, PendingUser, RegisteredUser
from src.services.start_command.messages import messages


class UserType(str, enum.Enum):
    """User type for /start command logic."""

    NEW_USER = "new_user"
    ADMIN = "admin"
    REGISTERED_USER = "registered_user"
    PENDING_USER = "pending_user"
    BANNED_USER = "banned_user"


class StartCommandAction(str, enum.Enum):
    """Actions for start command responses."""

    SHOW_REGISTRATION = "show_registration"
    SHOW_ADMIN_PANEL = "show_admin_panel"
    SHOW_MAIN_MENU = "show_main_menu"
    SHOW_PENDING_STATUS = "show_pending_status"
    SHOW_BANNED_MESSAGE = "show_banned_message"
    ERROR = "error"


@dataclasses.dataclass
class UserInfo:
    """User information container."""

    user_type: UserType
    telegram_id: int
    user_data: RegisteredUser | PendingUser | BannedUser | None = None
    is_admin: bool = False


@dataclasses.dataclass
class StartCommandResponse:
    """Response container for /start command processing."""

    action: StartCommandAction
    message: str
    user_type: str
    show_registration_form: bool = False
    show_admin_menu: bool = False
    show_main_menu: bool = False
    show_pending_info: bool = False
    show_support_contact: bool = False
    user_data: dict | None = None


class StartCommandService:
    """Service for handling /start command user determination logic."""

    def __init__(self, session: AsyncSession, admins_ids: list[int] = settings.ADMIN_IDS):
        self.user_dao = UserDAO(session)
        self.admins_ids = admins_ids

    async def determine_user_type(self, telegram_id: int) -> UserInfo:
        """
        Determine a user type based on telegram_id and return the appropriate UserInfo.

        Args:
            telegram_id: Telegram user ID

        Returns:
            UserInfo: Container with user type and data

        Raises:
            Exception: If database operation fails
        """

        logger.debug(f"🔍 Determining user type for telegram_id: {telegram_id}")
        try:
            if telegram_id in self.admins_ids:
                logger.info(f"👑 Admin user detected: {telegram_id}")
                return UserInfo(
                    user_type=UserType.ADMIN,
                    telegram_id=telegram_id,
                    user_data=None,
                    is_admin=True,
                )

            banned_user, registered_user, pending_user = await asyncio.gather(
                self.user_dao.get_banned_user_by_id(telegram_id),
                self.user_dao.get_registered_user_by_id(telegram_id),
                self.user_dao.get_pending_user_by_id(telegram_id),
                return_exceptions=True,
            )
            if banned_user and not isinstance(banned_user, Exception):
                logger.warning(f"🚫 Banned user attempted access: {telegram_id}")
                return UserInfo(
                    user_type=UserType.BANNED_USER, telegram_id=telegram_id, user_data=banned_user
                )

            if registered_user and not isinstance(registered_user, Exception):
                logger.info(f"✅ Registered user found: {telegram_id}")
                return UserInfo(
                    user_type=UserType.REGISTERED_USER,
                    telegram_id=telegram_id,
                    user_data=registered_user,
                )

            if pending_user and not isinstance(pending_user, Exception):
                logger.info(f"⏳ Pending user found: {telegram_id}")
                return UserInfo(
                    user_type=UserType.PENDING_USER, telegram_id=telegram_id, user_data=pending_user
                )

            logger.info(f"🆕 New user detected: {telegram_id}")
            return UserInfo(user_type=UserType.NEW_USER, telegram_id=telegram_id)

        except Exception as e:
            logger.error(f"❌ Failed to determine user type for {telegram_id}: {e}")
            raise

    async def process_start_command(self, telegram_id: int) -> StartCommandResponse:
        """Process /start command based on a user type.

        Args:
            telegram_id: Telegram user ID

        Returns:
            StartCommandResponse: Response data with appropriate action and message and user data
        """
        user_info = await self.determine_user_type(telegram_id)
        match user_info.user_type:
            case UserType.NEW_USER:
                return await self._handle_new_user(user_info)
            case UserType.ADMIN:
                return await self._handle_admin(user_info)
            case UserType.REGISTERED_USER:
                return await self._handle_registered_user(user_info)
            case UserType.PENDING_USER:
                return await self._handle_pending_user(user_info)
            case UserType.BANNED_USER:
                return await self._handle_banned_user(user_info)

    @staticmethod
    async def _handle_new_user(user_info: UserInfo) -> StartCommandResponse:
        """Handle a new user."""

        logger.info(f"🎉 Handling new user: {user_info.telegram_id}")
        return StartCommandResponse(
            action=StartCommandAction.SHOW_REGISTRATION,
            message=messages.welcome_new_user,
            user_type=user_info.user_type.value,
            show_registration_form=True,
        )

    @staticmethod
    async def _handle_admin(user_info: UserInfo) -> StartCommandResponse:
        """Handle an admin user."""
        logger.info(f"👑 Handling admin user: {user_info.telegram_id}")
        return StartCommandResponse(
            action=StartCommandAction.SHOW_ADMIN_PANEL,
            message=messages.welcome_admin,
            user_type=user_info.user_type.value,
            show_admin_menu=True,
            user_data=user_info.user_data.to_dict() if user_info.user_data else None,
        )

    @staticmethod
    async def _handle_registered_user(user_info: UserInfo) -> StartCommandResponse:
        """Handle registered user logic."""
        logger.info(f"✅ Handling registered user: {user_info.telegram_id}")
        user_name = user_info.user_data.first_name if user_info.user_data.first_name else ""
        return StartCommandResponse(
            action=StartCommandAction.SHOW_MAIN_MENU,
            message=messages.get_welcome_registered_with_name(name=user_name),
            user_type=user_info.user_type.value,
            show_main_menu=True,
            user_data=user_info.user_data.to_dict(),
        )

    @staticmethod
    async def _handle_pending_user(user_info: UserInfo) -> StartCommandResponse:
        """Handle pending user logic."""
        logger.info(f"⏳ Handling pending user: {user_info.telegram_id}")
        return StartCommandResponse(
            action=StartCommandAction.SHOW_PENDING_STATUS,
            message=messages.pending_status,
            user_type=user_info.user_type.value,
            show_pending_info=True,
            user_data=user_info.user_data.to_dict(),
        )

    @staticmethod
    async def _handle_banned_user(user_info: UserInfo) -> StartCommandResponse:
        """Handle banned user logic."""
        logger.warning(f"🚫 Handling banned user: {user_info.telegram_id}")
        return StartCommandResponse(
            action=StartCommandAction.SHOW_BANNED_MESSAGE,
            message=messages.banned_message,
            user_type=user_info.user_type.value,
            show_support_contact=True,
        )
