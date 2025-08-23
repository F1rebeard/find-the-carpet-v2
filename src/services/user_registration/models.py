from collections.abc import Callable

from aiogram.fsm.state import State
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo

from src.core_settings import EMAIL_PATTERN, NAME_PATTERN, PHONE_DIGITS_PATTERN
from src.schemas.users import UserRegistrationInput


class RegistrationData(BaseModel):
    """Registration data validation schema"""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    telegram_id: int = Field(gt=0, description="Telegram user ID")
    username: str | None = None
    first_name: str = Field(min_length=2, max_length=32, description="First name")
    last_name: str = Field(min_length=2, max_length=32, description="Last name")
    email: str = Field(min_length=5, max_length=64, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    from_whom: str = Field(min_length=3, max_length=100, description="Source information")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str, info: ValidationInfo) -> str:
        """Validate first_name and last_name format."""
        if not v:
            raise ValueError("Поле не может быть пустым")

        v = v.strip()

        if not NAME_PATTERN.match(v):
            field_name = "Имя должно" if info.field_name == "first_name" else "Фамилия должна"
            raise ValueError(f"{field_name} начинаться с заглавной буквы и содержать только буквы")

        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v:
            raise ValueError("Email не может быть пустым")

        v = v.strip().lower()

        if not EMAIL_PATTERN.match(v):
            raise ValueError("Некорректный формат email")

        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, input_value: str | None) -> str | None:
        """Validate and format phone number."""
        if input_value is None or input_value.strip() == "":
            return None

        digits_only = PHONE_DIGITS_PATTERN.sub("", input_value.strip())

        if digits_only.startswith("8"):
            if len(digits_only) != 11:
                raise ValueError("Некорректное число цифр для номера начинающегося с 8")
            return f"+7{digits_only[1:]}"
        elif digits_only.startswith("7"):
            if len(digits_only) != 11:
                raise ValueError("Некорректное число цифр для номера начинающегося с 7")
            return f"+{digits_only}"
        else:
            raise ValueError("Номер должен начинаться с 8 или 7")

    @field_validator("from_whom")
    @classmethod
    def validate_from_whom(cls, v: str) -> str:
        """Validate from_whom field."""
        if not v:
            raise ValueError("Поле 'Откуда узнали' не может быть пустым")

        v = v.strip()

        if len(v) < 3:
            raise ValueError("Поле 'Откуда узнали' должно содержать минимум 3 символа")

        return v

    @model_validator(mode="after")
    def validate_model(self) -> "RegistrationData":
        """Additional model-level validation."""
        if self.telegram_id <= 0:
            raise ValueError("Некорректный Telegram ID")

        return self

    def to_user_registration_input(self) -> UserRegistrationInput:
        """Convert to UserRegistrationInput schema."""
        return UserRegistrationInput(
            telegram_id=self.telegram_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            from_whom=self.from_whom,
        )


class ValidationResult(BaseModel):
    """Result of field validation."""

    is_valid: bool
    error_message: str | None = None
    cleaned_value: str | None = None


class DialogWindowData(BaseModel):
    """Data for registration dialog windows."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    field: str = Field(..., description="Field name in dialog data")
    prompt: str = Field(..., description="Prompt message for the registration step")
    next_state: State = Field(..., description="Next FSM state for the registration step")
    normalize: Callable | None = Field(None, description="Function for field normalization")
    skip_button: bool = Field(False, description="Whether to show 'Skip' button for the step")


class DialogStructure(BaseModel):
    fields: list[DialogWindowData]
