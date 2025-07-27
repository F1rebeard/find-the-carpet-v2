import msgspec
from loguru import logger
from sqlalchemy import Sequence, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.users import BannedUser, PendingUser, RegisteredUser
from src.schemas.users import UserRegistrationInput


class UserDAO:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_registered_user_by_id(self, telegram_id: int) -> RegisteredUser | None:
        try:
            return await self.session.get(RegisteredUser, telegram_id)
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to get user by id: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    async def get_banned_user_by_id(self, telegram_id: int) -> BannedUser | None:
        try:
            return await self.session.get(BannedUser, telegram_id)
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to get user by id: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    async def search_registered_user(self, search_text: str) -> Sequence[RegisteredUser]:
        stmt = select(RegisteredUser).where(
            or_(
                RegisteredUser.username.ilike(f"%{search_text}%"),
                RegisteredUser.last_name.ilike(f"%{search_text}%"),
                RegisteredUser.email.ilike(f"%{search_text}%"),
                RegisteredUser.phone.ilike(f"%{search_text}%"),
            )
        )
        found_users = await self.session.execute(stmt)
        return found_users.scalars().all()

    async def get_pending_user_by_id(self, telegram_id: int) -> PendingUser | None:
        try:
            return await self.session.get(PendingUser, telegram_id)
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to get pending user by id: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    async def add_pending_user(self, user_data: UserRegistrationInput):
        try:
            self.session.add(PendingUser(msgspec.to_builtins(user_data)))
            logger.info(f"User {user_data.telegram_id} added to pending users")
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to add pending user by id: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    async def approve_user(self, telegram_id: int, chosen_role: str):
        pending_user = await self.get_pending_user_by_id(telegram_id)
        if not pending_user:
            logger.warning(f"No pending user found for id {telegram_id}")
            return

        self.session.add(
            RegisteredUser(
                telegram_id=pending_user.telegram_id,
                username=pending_user.username,
                first_name=pending_user.first_name,
                last_name=pending_user.last_name,
                email=pending_user.email,
                role=chosen_role,
            )
        )
        await self.session.delete(pending_user)
        logger.info(f"User {telegram_id} approved with role {chosen_role}")

    async def ban_user(self, telegram_id: int) -> bool:
        user_to_ban = await self.get_registered_user_by_id(telegram_id)
        if not user_to_ban:
            logger.warning(f"No user found with id: {telegram_id}")
            return False

        banned_user = BannedUser(
            telegram_id=user_to_ban.telegram_id,
            username=user_to_ban.username,
            first_name=user_to_ban.first_name,
            last_name=user_to_ban.last_name,
            email=user_to_ban.email,
        )
        try:
            self.session.add(banned_user)
            await self.session.delete(user_to_ban)
            logger.info(f"User with id: {telegram_id} banned")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to get banned user by id: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise
