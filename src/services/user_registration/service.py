from typing import Optional, Tuple

from loguru import logger
from pydantic_core import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao.user import UserDAO
from src.services.user_registration.models import RegistrationData, ValidationResult


class RegistrationService:
    """Service for handling user registration logic."""

    def __init__(self, session: AsyncSession):
        self.user_dao = UserDAO(session)

    def validate_field(
        self, field_name: str, value: str, telegram_id: int, username: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate individual registration field.

        Args:
            field_name: Name of the field to validate
            value: Value to validate
            telegram_id: User's telegram ID
            username: User's telegram username

        Returns:
            ValidationResult with validation status and error message if applicable
        """
        try:
            # Create temporary registration data with minimal required fields
            temp_data = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": "Test" if field_name != "first_name" else value,
                "last_name": "Test" if field_name != "last_name" else value,
                "email": "test@example.com" if field_name != "email" else value,
                "from_whom": "test source" if field_name != "from_whom" else value,
            }

            # Add a phone number if provided
            if field_name == "phone":
                temp_data["phone"] = value

            # Validate using Pydantic
            registration_data = RegistrationData(**temp_data)

            # Return cleaned value for specific fields
            cleaned_value = getattr(registration_data, field_name, None)

            return ValidationResult(
                is_valid=True,
                cleaned_value=str(cleaned_value) if cleaned_value is not None else None,
            )

        except ValidationError as e:
            field_errors = [error for error in e.errors() if error["loc"] == (field_name,)]
            if field_errors:
                error_message = field_errors[0]["msg"]
            else:
                error_message = "Ошибка валидации"

            return ValidationResult(is_valid=False, error_message=error_message)

        except Exception as e:
            logger.error(f"❌ Unexpected validation error for {field_name}: {e}")
            return ValidationResult(
                is_valid=False, error_message="Произошла неожиданная ошибка валидации"
            )

    def validate_full_registration(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str],
        from_whom: str,
    ) -> Tuple[bool, Optional[str], Optional[RegistrationData]]:
        """
        Validate complete registration data.

        Returns:
            Tuple of (is_valid, error_message, registration_data)
        """
        try:
            registration_data = RegistrationData(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                from_whom=from_whom,
            )
            return True, None, registration_data

        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                message = error["msg"]
                error_messages.append(f"• {message}")

            full_error = "Ошибки валидации:\n" + "\n".join(error_messages)
            return False, full_error, None

        except Exception as e:
            logger.error(f"❌ Unexpected error during full validation: {e}")
            return False, "Произошла неожиданная ошибка при валидации данных", None

    async def save_registration(self, registration_data: RegistrationData) -> bool:
        """
        Save validated registration data to database.

        Args:
            registration_data: Validated registration data

        Returns:
            True if successful, False otherwise
        """
        try:
            user_input = registration_data.to_user_registration_input()
            await self.user_dao.add_pending_user(user_input)

            logger.info(f"✅ Registration saved for user {registration_data.telegram_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving registration for {registration_data.telegram_id}: {e}")
            return False

    async def check_existing_user(self, telegram_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user already exists in any table.

        Returns:
            Tuple of (exists, status_message)
        """

        # TODO We check it during start!
        try:
            # Check if user is already registered
            registered_user = await self.user_dao.get_registered_user_by_id(telegram_id)
            if registered_user:
                return True, "Пользователь уже зарегистрирован"

            # Check if user is already pending
            pending_user = await self.user_dao.get_pending_user_by_id(telegram_id)
            if pending_user:
                return True, "Заявка на регистрацию уже отправлена"

            # Check if user is banned
            banned_user = await self.user_dao.get_banned_user_by_id(telegram_id)
            if banned_user:
                return True, "Пользователь заблокирован"

            return False, None

        except Exception as e:
            logger.error(f"❌ Error checking existing user {telegram_id}: {e}")
            return True, "Ошибка проверки пользователя"
