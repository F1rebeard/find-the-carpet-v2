from pydantic import ValidationError

from src.services.admin.manual_registration.models import ManualUserRegistrationData
from src.services.user_registration import ValidationResult


class ValidateManualRegistrationService:
    """Admin validation service using ManualUserRegistrationData."""

    @staticmethod
    def _extract_clean_error_message(error_msg: str) -> str:
        """Extract a clean error message."""
        prefixes_to_remove = [
            "Value error, ",
            "Assertion failed, ",
            "String should ",
            "Input should ",
        ]
        clean_msg = error_msg
        for prefix in prefixes_to_remove:
            if clean_msg.startswith(prefix):
                clean_msg = clean_msg[len(prefix) :]
                break
        return clean_msg

    @classmethod
    def validate_field(cls, field_name: str, value: str | int | None) -> ValidationResult:
        """Validate admin input field using ManualUserRegistrationData."""
        try:
            payload: dict[str, object | None] = {}
            if isinstance(value, str) and value.strip() == "":
                value = None

            if field_name == "telegram_id":
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    return ValidationResult(
                        is_valid=False,
                        error_message="Telegram ID должен быть целым положительным числом",
                        cleaned_value=None,
                    )

            payload[field_name] = value
            if field_name != "telegram_id":
                payload["telegram_id"] = 1

            validated = ManualUserRegistrationData(**payload)
            cleaned_value = getattr(validated, field_name, None)
            return ValidationResult(
                is_valid=True,
                cleaned_value=str(cleaned_value) if cleaned_value is not None else None,
            )

        except ValidationError as e:
            field_errors = [error for error in e.errors() if error["loc"] == (field_name,)]
            if field_errors:
                raw_error_message = field_errors[0]["msg"]
                clean_error_message = cls._extract_clean_error_message(raw_error_message)
            else:
                clean_error_message = "Ошибка валидации"
            return ValidationResult(is_valid=False, error_message=clean_error_message)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=cls._extract_clean_error_message(str(e)),
                cleaned_value=None,
            )
