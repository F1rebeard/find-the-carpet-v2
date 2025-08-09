from loguru import logger

from src.core_settings import base_settings as settings


def setup_logger():
    """
    Configure the Loguru logger.
    """
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level=settings.LOG_LEVEL.upper(),
        format="🐞 {time:YYYY-MM-DD at HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        enqueue=True,
    )
    logger.debug("🔧 Logger initialized at level: {}", settings.LOG_LEVEL.upper())
