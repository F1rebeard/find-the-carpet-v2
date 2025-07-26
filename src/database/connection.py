import contextlib
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.settings import base_settings


class Database:

    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self):
        if self._engine:
            logger.warning("⚠️ Database engine already initialized")
            return

        self._engine = create_async_engine(
            base_settings.DATABASE.url,
            echo=base_settings.DATABASE.echo,
            future=True,
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("🔌 SQLAlchemy engine created")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    async def disconnect(self):
        if not self._engine:
            logger.warning("⚠️ No engine to dispose")
            return

        await self._engine.dispose()
        logger.info("🧯 SQLAlchemy engine disposed")

    @contextlib.asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        if not self._session_factory:
            raise RuntimeError("❌ Session factory is not initialized. Call connect() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
