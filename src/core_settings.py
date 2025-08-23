import re

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Validate fields
NAME_PATTERN = re.compile(r"^[A-ZА-ЯЁ][a-zа-яё\-\s]*$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_DIGITS_PATTERN = re.compile(r"\D")


class DatabaseSettings(BaseModel):
    """Database connection settings."""

    url: str
    echo: bool = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v:
            raise ValueError("Database URL is not set.")
        return v


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    DATABASE: DatabaseSettings
    BOT_TOKEN: str
    LOG_LEVEL: str = "INFO"
    ADMIN_IDS: list[int] = []
    INLINE_ROWS_PER_PAGE: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    def __init__(self, **data):
        super().__init__(**data)
        logger.info("⚙️ Settings loaded.")
        logger.debug(f"🐘 Database URL: {self.DATABASE.url}")
        logger.debug(f"🤖 Bot token: {self.BOT_TOKEN[:5]}***")
        logger.debug(f"🪵 Log level: {self.LOG_LEVEL}")


base_settings = Settings()
bot_properties = DefaultBotProperties(
    parse_mode=ParseMode.HTML,
)
bot = Bot(token=base_settings.BOT_TOKEN, default=bot_properties)
dp = Dispatcher()
