from pydantic import BaseModel


class UserRegistrationInput(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    from_whom: str
