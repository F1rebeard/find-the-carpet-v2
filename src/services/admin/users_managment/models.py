import enum


class UserReviewStatus(str, enum.Enum):
    """User review status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADDED_MANUALLY = "added_manually"
    BANNED = "banned"


class RegisteredUserRole(str, enum.Enum):
    """Registered user role."""

    COLLEAGUE = "Коллега"
    UNDEFINED = "Неопределенна"
    DESIGNER = "Дизайнер"
