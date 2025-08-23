from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pydantic_core.core_schema import ValidationInfo

from src.core_settings import EMAIL_PATTERN, NAME_PATTERN, PHONE_DIGITS_PATTERN
from src.services.user_registration.models import RegistrationData


class ManualUserRegistrationData(BaseModel):
    """Manual user registration data."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    telegram_id: int = Field(gt=0, description="Telegram user ID")
    username: str | None = None
    first_name: str | None = Field(
        default=None, min_length=2, max_length=32, description="First name"
    )
    last_name: str | None = Field(
        default=None, min_length=2, max_length=32, description="Last name"
    )
    email: str | None = Field(
        default=None, min_length=5, max_length=64, description="Email address"
    )
    phone: str | None = Field(default=None, description="Phone number")
    from_whom: str | None = Field(
        default=None, min_length=3, max_length=100, description="Source information"
    )

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Telegram ID должен быть положительным числом")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_and_surnames(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None or value.strip() == "":
            return None
        value = value.strip()
        if not NAME_PATTERN.match(value):
            field_name = "Имя должно" if info.field_name == "first_name" else "Фамилия должна"
            raise ValueError(f"{field_name} начинаться с заглавной буквы и содержать только буквы")
        return value

    @field_validator("email")
    @classmethod
    def validate_email_optional(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Некорректный формат email")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone_optional(cls, input_value: str | None) -> str | None:
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
    def validate_from_whom_optional(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Поле 'Откуда узнали' должно содержать минимум 3 символа")
        return value

    def to_strict_registration(self) -> RegistrationData:
        """
        Конвертирует «мягкую» модель в твою строгую RegistrationData.
        Бросит ValidationError, если чего-то не хватает.
        """
        missing = []
        if self.telegram_id is None:
            missing.append("telegram_id")
        if self.first_name is None:
            missing.append("first_name")
        if self.last_name is None:
            self.last_name = "Не заполнено"
        if self.email is None:
            self.email = "example@example.net"
        if self.from_whom is None:
            missing.append("from_whom")

        if missing:
            raise ValidationError.from_exception_data(
                "RegistrationData",
                [
                    {
                        "type": "missing",
                        "loc": (field,),
                        "msg": "field required",
                        "input": None,
                    }
                    for field in missing
                ],
            )

        # здесь сработают строгие валидаторы RegistrationData
        return RegistrationData(
            telegram_id=self.telegram_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            from_whom=self.from_whom,
        )
