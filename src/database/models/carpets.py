import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.users import RegisteredUser


class Carpet(Base):
    """Carpet data."""

    __tablename__ = "carpets"

    carpet_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # manual id
    collection: Mapped[str] = mapped_column(String(64), nullable=False)
    geometry: Mapped[str] = mapped_column(String(32), nullable=False)
    size: Mapped[str] = mapped_column(String(32), nullable=False)
    design: Mapped[str] = mapped_column(String(64), nullable=False)
    color_1: Mapped[str] = mapped_column(String(32), nullable=True)
    color_2: Mapped[str] = mapped_column(String(32), nullable=True)
    color_3: Mapped[str] = mapped_column(String(32), nullable=True)
    style: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Double, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations as a favorite carpet for user
    favorite_by: Mapped[list["FavoriteCarpets"]] = relationship(
        "FavoriteCarpets", back_populates="carpet", cascade="all, delete-orphan"
    )


class FavoriteCarpets(Base):
    """Many-to-many relationship between users and their favorite carpets."""

    __tablename__ = "favorite_carpets"
    __table_args__ = (UniqueConstraint("user_id", "carpet_id", name="uq_user_carpet"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("registered_users.telegram_id", ondelete="CASCADE"), nullable=False
    )
    carpet_id: Mapped[int] = mapped_column(
        ForeignKey("carpets.carpet_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relations
    user: Mapped["RegisteredUser"] = relationship("RegisteredUser", back_populates="favorite")
    carpet: Mapped["Carpet"] = relationship("Carpet", back_populates="favorite_by")
